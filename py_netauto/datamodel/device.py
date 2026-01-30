"""
Network device models.

This module provides models for network devices including spines and leaves
with computed fields for role determination and other device properties.
"""

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
        v = v.lower()

        # Error
        if not v.startswith(("l", "s")):
            msg: str = f"Device Hostname: {v} not valid. Valid hostnames start with 'l' or 's'"
            raise ValueError(msg)
        # Leaves Validation
        if v.startswith("l"):
            max_leaves: int = 128
            try:
                num = int(v[1:])
            except ValueError:
                msg: str = f"Hostname must be {v[0]}<number>. From l1 to l{max_leaves} got: '{v}'"
                raise ValueError(msg) from None
            if not 1 <= num <= max_leaves:
                msg: str = f"Device Hostname: {v} not valid. Valid Leaf hostnames: l1 - l2 - l3 ... l{max_leaves}"
                raise ValueError(msg)
            return v
        # Spines Validation
        max_spines: int = 8
        try:
            num: int = int(v[1:])
        except ValueError:
            msg = f"Hostname must be {v[0]}<number>, got: '{v}'"
            raise ValueError(msg) from None
        if not 1 <= num <= max_spines:
            msg: str = f"Device Hostname: {v} not valid. Valid Spine hostnames: s1 - s2 - s3 ... s{max_spines}"
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
        if not self._fabric_asns:
            raise ValueError("Var: 'fabric_asns' not initialized")

        # If role is spine, get spine attirbute
        if self.role == "spine" and "spines" in self._fabric_asns:
            return self._fabric_asns["spines"]

        # if hostname lx in favirc_Asns
        if self.hostname in self._fabric_asns:
            return self._fabric_asns[self.hostname]

        msg: str = f"No ASN Mapping has been provided for device {self.hostname}"
        raise ValueError(msg)
