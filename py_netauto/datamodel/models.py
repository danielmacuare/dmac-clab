"""
Data models for network fabric configuration.

This module provides Pydantic models for defining, validating, and exporting
network fabric data models with computed fields and type safety.
"""

from ipaddress import IPv4Interface, IPv4Network, IPv6Interface, IPv6Network

from pydantic import BaseModel, Field, computed_field


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


class Topology(BaseModel):
    """
    Network fabric topology structure.

    Defines the physical topology of the fabric including all spine
    and leaf devices in a 3-stage Clos architecture.
    """

    spines: list[Device] = Field(
        description="List of spine switches in the fabric",
    )
    leaves: list[Device] = Field(
        description="List of leaf switches in the fabric",
    )


class FabricDataModel(BaseModel):
    """
    Complete fabric data model.

    Root model containing all configuration data for a network fabric
    including topology, IP allocation, ASN assignments, and metadata.
    """

    schema_version: str = Field(
        description="Version of the data model schema (e.g., 1.0.0)",
    )
    schema_description: str = Field(
        description="Human-readable description of this fabric configuration",
    )
    fabric_name: str = Field(
        description="Unique name identifying this fabric (e.g., dc1, production-fabric)",
    )
    mgmt_vrf: str = Field(
        description="VRF name for management interfaces (e.g., MGMT, management)",
    )
    reserved_supernets: ReservedSupernets = Field(
        description="IP address pools reserved for fabric infrastructure",
    )
    fabric_asns: dict[str, int] = Field(
        description="BGP ASN assignments by device role (e.g., {'spines': 64600, 'l1': 65001})",
    )
    topology: Topology = Field(
        description="Physical topology structure with all devices",
    )
