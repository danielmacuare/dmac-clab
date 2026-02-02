"""
Network device models.

This module provides models for network devices including spines and leaves
with computed fields for role determination and other device properties.
"""

from ipaddress import IPv4Address

from pydantic import BaseModel, Field, computed_field, field_validator

from .interface import Interface


# MODELS
class Device(BaseModel):
    """
    Network device configuration.

    Represents a spine or leaf switch in the fabric with its hostname
    and associated network interfaces.
    """

    _fabric_asns: dict[str, int] | None = None
    hostname: str = Field(
        description="Unique hostname of the device (e.g., s1, l1, spine1, leaf1)",
    )
    interfaces: list[Interface] = Field(
        description="List of network interfaces configured on this device",
    )

    # FIELD VALIDATORS
    @field_validator("hostname")
    @classmethod
    def validate_hostname(cls, v: str) -> str:
        """
        Validate and normalize device hostname.

        Ensures hostnames follow the required naming convention:
        - Spines: s1 through s8 (exactly 8 allowed)
        - Leaves: l1 through l128 (exactly 128 allowed)
        - Lowercase only, no leading zeros

        Args:
            v: The hostname string to validate.

        Returns:
            str: The validated and normalized (lowercase) hostname.

        Raises:
            ValueError: If hostname doesn't match required patterns or is out of range.

        Example:
            >>> Device.validate_hostname("S1")
            's1'
            >>> Device.validate_hostname("l128")
            'l128'
            >>> Device.validate_hostname("l129")  # doctest: +SKIP
            ValueError: Device Hostname: l129 not valid...
        """
        v = v.lower()

        # Error
        if not v.startswith(("l", "s")):
            msg = f"Device hostname '{v}' is invalid. Valid hostnames must start with 'l' (leaf) or 's' (spine)."
            raise ValueError(msg)

        # Leaves Validation
        if v.startswith("l"):
            max_leaves: int = 128
            try:
                num = int(v[1:])
            except ValueError:
                msg = f"Invalid leaf hostname '{v}'. Expected format: l<number> (e.g., l1, l2, ..., l{max_leaves})"
                raise ValueError(msg) from None

            if not 1 <= num <= max_leaves:
                msg = f"Leaf hostname '{v}' out of range. Valid range: l1 to l{max_leaves}"
                raise ValueError(msg)
            return v

        # Spines Validation
        max_spines: int = 8
        try:
            num: int = int(v[1:])
        except ValueError:
            msg = f"Invalid spine hostname '{v}'. Expected format: s<number> (e.g., s1, s2, ..., s{max_spines})"
            raise ValueError(msg) from None

        if not 1 <= num <= max_spines:
            msg = f"Spine hostname '{v}' out of range. Valid range: s1 to s{max_spines}"
            raise ValueError(msg)
        return v

    # COMPUTED FIELDS
    @computed_field
    @property
    def role(self) -> str:
        """
        Compute device role from hostname prefix.

        Determines whether the device is a spine or leaf based on the
        first character of the hostname (s=spine, l=leaf).

        Returns:
            Device role as either "spine" or "leaf".

        Raises:
            ValueError: If hostname doesn't start with 's' or 'l'.
        """
        if self.hostname.startswith("l"):
            return "leaf"
        if self.hostname.startswith("s"):
            return "spine"

        msg = f"Cannot determine role from hostname {self.hostname}."
        raise ValueError(msg)

    @computed_field
    @property
    def fabric_asn(self) -> int:
        """
        Retrieve BGP ASN from fabric-wide ASN mapping.

        The fabric ASN is determined by looking up the device in the fabric_asns
        dictionary injected by the FabricDataModel. Spines use a shared ASN from
        the 'spines' key, while leaves use their hostname as the lookup key.

        Returns:
            int: The BGP Autonomous System Number for this device.

        Raises:
            ValueError: If fabric_asns is not initialized or no mapping exists
                for this device.

        Example:
            >>> # Spine device
            >>> spine._fabric_asns = {"spines": 64600, "l1": 65001}
            >>> spine.fabric_asn
            64600

            >>> # Leaf device
            >>> leaf._fabric_asns = {"spines": 64600, "l1": 65001}
            >>> leaf.fabric_asn
            65001
        """
        if not self._fabric_asns:
            msg = (
                f"Fabric ASNs not initialized for device '{self.hostname}'. "
                f"This should be injected by FabricDataModel during initialization."
            )
            raise ValueError(msg)

        # If role is spine, set common spine ASN
        if self.role == "spine" and "spines" in self._fabric_asns:
            return self._fabric_asns["spines"]

        # if hostname leaf, get the ASN associated to that leaf.
        if self.hostname in self._fabric_asns:
            return self._fabric_asns[self.hostname]

        msg = f"No ASN mapping found for device '{self.hostname}'. Available mappings: {list(self._fabric_asns.keys())}"
        raise ValueError(msg)

    @computed_field
    @property
    def router_id(self) -> IPv4Address:
        """
        Extract router ID from Loopback0 interface IP address.

        The router ID is a unique identifier used by routing protocols (BGP, OSPF)
        to identify this device in the routing domain. By convention, it is derived
        from the Loopback0 interface IP address without the subnet mask.

        Returns:
            IPv4Address: The router ID extracted from Loopback0 (e.g., 10.255.0.1).

        Raises:
            ValueError: If the device does not have a Loopback0 interface configured.

        Example:
            >>> device = Device(hostname="s1", interfaces=[Interface(name="Loopback0", ipv4="10.255.0.1/32")])
            >>> device.router_id
            IPv4Address('10.255.0.1')
        """
        for interface in self.interfaces:
            if interface.name == "Loopback0":
                return interface.ipv4.ip

        msg = (
            f"Device '{self.hostname}' missing required Loopback0 interface. "
            f"Router ID cannot be computed without Loopback0 IP address."
        )
        raise ValueError(msg)

    @computed_field
    @property
    def vtep_ip(self) -> IPv4Address:
        """
        Extract VTEP IP from Loopback1 interface IP address.

        VTEP (VXLAN Tunnel Endpoint) IP is used for EVPN-VXLAN encapsulation.
        In MLAG pairs, both leaf switches share the same VTEP anycast address.

        Returns:
            IPv4Address: The VTEP IP extracted from Loopback1 (e.g., 10.255.1.1).

        Raises:
            ValueError: If the device does not have a Loopback1 interface configured.

        Example:
            >>> device = Device(hostname="s1", interfaces=[Interface(name="Loopback1", ipv4="10.255.1.1/32")])
            >>> device.vtep_ip
            IPv4Address('10.255.1.1')
        """
        for interface in self.interfaces:
            if interface.name == "Loopback1":
                return interface.ipv4.ip
        msg = (
            f"Device '{self.hostname}' missing required Loopback1 interface. "
            f"VTEP IP cannot be computed without Loopback1 IP address."
        )
        raise ValueError(msg)
