"""
Network infrastructure models.

This module provides models for network-level configuration including
management pools and reserved IP supernets.
"""

from ipaddress import IPv4Network, IPv6Network

from pydantic import BaseModel, Field


class ManagementPool(BaseModel):
    """
    Management network pool configuration.

    Defines the IPv4 and IPv6 subnets allocated for out-of-band
    management access to network devices.
    """

    ipv4_subnet: IPv4Network = Field(
        description="IPv4 subnet for out-of-band management network (e.g., 192.168.0.0/24)",
    )
    ipv6_subnet: IPv6Network = Field(
        description="IPv6 subnet for out-of-band management network (e.g., 2001:db8::/64)",
    )


class ReservedSupernets(BaseModel):
    """
    Reserved IP supernets for fabric allocation.

    Defines the IP address pools reserved for different purposes
    in the network fabric including point-to-point links, loopback
    interfaces, and management networks.
    """

    p2p_pool: IPv4Network = Field(
        description="IPv4 supernet for point-to-point links between spine and leaf devices (e.g., 10.254.0.0/16)",
    )
    loopback0_pool: IPv4Network = Field(
        description="IPv4 pool for Loopback0 interfaces used as BGP router IDs (e.g., 10.255.0.0/24)",
    )
    loopback1_pool: IPv4Network = Field(
        description="IPv4 pool for Loopback1 interfaces used as VXLAN tunnel endpoints (VTEP) (e.g., 10.255.1.0/24)",
    )
    management_pool: ManagementPool = Field(
        description="Management network configuration for out-of-band device access",
    )
