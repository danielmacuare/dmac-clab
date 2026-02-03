"""
Network interface models.

This module provides models for network interface configuration including
physical and logical interfaces with IPv4/IPv6 addressing.
"""

from ipaddress import IPv4Interface, IPv6Interface

from pydantic import BaseModel, Field, computed_field


class Interface(BaseModel):
    """
    Network interface configuration.

    Represents a physical or logical network interface with IPv4/IPv6
    addressing and connectivity information. Automatically generates
    interface descriptions based on interface type and parent device.

    The description is computed based on interface name:
    - Management0: "Management Interface | <HOSTNAME>"
    - Loopback0: "ROUTER_ID | EVPN_PEERING | <HOSTNAME>"
    - Loopback1: "VTEP_IP | VXLAN_DATA_PLANE | <HOSTNAME>"
    - Ethernet*: "P2P Link to <REMOTE_DEVICE>" (if remote_device is set)

    Attributes:
        name: Interface name (e.g., Ethernet1, Management0, Loopback0).
        ipv4: IPv4 address with prefix length.
        ipv6: Optional IPv6 address with prefix length.
        remote_device: Hostname of connected remote device (for P2P links).
        description: Computed description based on interface type.
    """

    name: str = Field(
        description="Interface name (e.g., Ethernet1, Management0, Loopback0)",
    )
    ipv4: IPv4Interface = Field(
        description="IPv4 address with prefix length assigned to the interface (e.g., 10.254.1.0/31)",
    )
    ipv6: IPv6Interface | None = Field(
        default=None,
        description="IPv6 address with prefix length assigned to the interface (e.g., 2001:db8::1/64)",
    )
    remote_device: str | None = Field(
        default=None,
        description="Hostname of the remote device connected to this interface (None for loopback/management)",
    )

    # Private attribute injected by parent Device model
    _device_hostname: str | None = None

    # Private attribute injected by the parent FabricDataModel
    _mgmt_vrf: str | None = None

    @computed_field
    @property
    def description(self) -> str | None:
        """
        Generate interface description based on interface type.

        Automatically creates standardized descriptions for different interface types:
        - Management interfaces: "Management Interface | <HOSTNAME>"
        - Loopback0: "ROUTER_ID | EVPN_PEERING | <HOSTNAME>"
        - Loopback1: "VTEP_IP | VXLAN_DATA_PLANE | <HOSTNAME>"
        - Ethernet P2P links: "P2P Link to <REMOTE_DEVICE>"

        Returns:
            str: Generated description for known interface types.
            None: If parent device hostname is not set or interface type is unknown.

        Example:
            >>> iface = Interface(name="Loopback0", ipv4="10.255.0.1/32")
            >>> iface._device_hostname = "s1"
            >>> iface.description
            'ROUTER_ID | EVPN_PEERING | S1'

            >>> p2p = Interface(name="Ethernet1", ipv4="10.254.1.0/31", remote_device="l1")
            >>> p2p._device_hostname = "s1"
            >>> p2p.description
            'P2P Link to l1'
        """
        hostname = self._device_hostname.upper() if self._device_hostname else None

        if hostname is None:
            return None

        interface_descriptions = {
            "Management0": f"Management Interface | {hostname}",
            "Loopback0": f"ROUTER_ID | EVPN_PEERING | {hostname}",
            "Loopback1": f"VTEP_IP | VXLAN_DATA_PLANE | {hostname}",
        }
        if self.name in interface_descriptions:
            return interface_descriptions[self.name]

        if self.name.startswith("Ethernet") and self.remote_device:
            return f"P2P Link to {self.remote_device}"

        return None

    @computed_field
    @property
    def mgmt_vrf(self) -> str | None:
        """
        Determine the VRF for this interface.

        Returns the management VRF name if this is a Management0 interface,
        otherwise returns None to indicate no VRF assignment. The VRF value
        is injected from the parent FabricDataModel during validation.

        Returns:
            str: Management VRF name (e.g., "MGMT") for Management0 interfaces
                when injected from FabricDataModel.
            None: For all other interface types, or if VRF was not injected.

        Example:
            >>> iface = Interface(name="Management0", ipv4="10.0.0.1/24")
            >>> iface._mgmt_vrf = "MGMT"  # Injected by FabricDataModel
            >>> iface.mgmt_vrf
            'MGMT'

            >>> iface = Interface(name="Ethernet1", ipv4="10.254.1.0/31")
            >>> iface.mgmt_vrf is None
            True
        """
        if self.name == "Management0":
            return self._mgmt_vrf
        return None
