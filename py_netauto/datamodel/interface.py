"""
Network interface models.

This module provides models for network interface configuration including
physical and logical interfaces with IPv4/IPv6 addressing.
"""

from ipaddress import IPv4Interface, IPv6Interface

from pydantic import BaseModel, Field


class Interface(BaseModel):
    """
    Network interface configuration.

    Represents a physical or logical network interface with IPv4/IPv6
    addressing and connectivity information.
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
    description: str | None = Field(
        default=None,
        description="Human-readable description of the interface purpose or connection",
    )
    remote_device: str | None = Field(
        default=None,
        description="Hostname of the remote device connected to this interface (None for loopback/management)",
    )
