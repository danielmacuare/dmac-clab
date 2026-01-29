"""
Network device models.

This module provides models for network devices including spines and leaves
with computed fields for role determination and other device properties.
"""

from pydantic import BaseModel, Field, computed_field

from .interface import Interface


class Device(BaseModel):
    """
    Network device configuration.

    Represents a spine or leaf switch in the fabric with its hostname
    and associated network interfaces.
    """

    hostname: str = Field(
        description="Unique hostname of the device (e.g., s1, l1, spine1, leaf1)",
    )
    asn: int = Field(
        description="BGP Autonomous System Number assigned to this device",
    )
    interfaces: list[Interface] = Field(
        description="List of network interfaces configured on this device",
    )

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
