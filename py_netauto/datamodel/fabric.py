"""
Root fabric data model.

This module provides the root FabricDataModel that contains all configuration
data for a network fabric including topology, IP allocation, and ASN assignments.
"""

from ipaddress import IPv4Interface

from pydantic import BaseModel, Field, model_validator

from .network import ReservedSupernets
from .topology import Topology


class FabricDataModel(BaseModel):
    """
    Complete fabric data model.

    Root model containing all configuration data for a network fabric
    including topology, IP allocation, ASN assignments, and metadata.

    Model Validators:
        inject_fabric_asns: Injects fabric_asns mapping into all devices
            (Device._fabric_asns) for fabric_asn computed field.
        inject_mgmt_vrf: Injects mgmt_vrf into Management0 interfaces
            (Interface._mgmt_vrf) for mgmt_vrf computed field.
        inject_devices: Injects device list into P2P interfaces
            (Interface._devices) for remote_interface computed field.
        validate_remote_device_references: Validates that remote_device attributes
            point to existing devices in the topology.
        validate_unique_ipv4_addresses: Validates that all IPv4 addresses are unique
            across the fabric topology.
        validate_ip_pool_allocation: Validates that all interface IPs are within
            their designated pools (management, loopback, P2P).

    Data Flow:
        1. Model initialization creates topology with all devices/interfaces
        2. inject_fabric_asns() → Device._fabric_asns
        3. inject_mgmt_vrf() → Interface._mgmt_vrf (Management0 only)
        4. inject_devices() → Interface._devices (P2P interfaces only)
        5. Device model validator → Interface._device_hostname
    """

    schema_version: str = Field(
        description="Version of the data model schema (e.g., 1.0.0)",
        examples=["1.0.0", "1.0.1", "2.0.0"],
    )
    schema_description: str = Field(
        description="Human-readable description of this fabric configuration",
        examples=[
            "Full data model not including computed fields that will be passed into Pydantic",
            "Production fabric configuration for DC1",
            "Test environment fabric with minimal topology",
        ],
    )
    fabric_name: str = Field(
        description="Unique name identifying this fabric (e.g., dc1, production-fabric)",
        examples=["dc1", "production-fabric", "ceos_clab_clos", "test-fabric"],
    )
    mgmt_vrf: str = Field(
        description="VRF name for management interfaces (e.g., MGMT, management)",
        examples=["MGMT", "management", "default"],
    )
    reserved_supernets: ReservedSupernets = Field(
        description="IP address pools reserved for fabric infrastructure",
    )
    fabric_asns: dict[str, int] = Field(
        description="BGP ASN assignments by device role (e.g., {'spines': 64600, 'l1': 65001})",
        examples=[
            {"spines": 64600, "l1": 65001, "l2": 65002},
            {"spines": 65000, "leaves": 65100},
            {"spine": 64512, "leaf1": 65001, "leaf2": 65002},
        ],
    )
    topology: Topology = Field(
        description="Physical topology structure with all devices",
    )

    # MODEL VALIDATORS
    @model_validator(mode="after")
    def inject_fabric_asns(self) -> "FabricDataModel":
        """Inject fabric_asns into all devices after model initialization."""
        all_devices = self.topology.spines + self.topology.leaves
        for device in all_devices:
            device._fabric_asns = self.fabric_asns  # noqa: SLF001

        return self

    @model_validator(mode="after")
    def inject_mgmt_vrf(self) -> "FabricDataModel":
        """Inject mgmt_vrf into Management0 interfaces (Interface.mgmt_vrf) after model initialization."""
        for device in self.topology.spines + self.topology.leaves:
            for interface in device.interfaces:
                if interface.name == "Management0":
                    interface._mgmt_vrf = self.mgmt_vrf  # noqa: SLF001

        return self

    @model_validator(mode="after")
    def inject_devices(self) -> "FabricDataModel":
        """
        Inject devices data into interfaces for remote_interface lookup.

        This validator provides interfaces with access to the full device list
        so they can perform bidirectional lookups to find reciprocal P2P links.
        Only interfaces with remote_device set receive the topology injection
        as an optimization.

        Returns:
            FabricDataModel: The validated model with topology injected.
        """
        all_devices = self.topology.spines + self.topology.leaves
        for device in all_devices:
            for interface in device.interfaces:
                if interface.remote_device:  # Only P2P Links
                    interface._devices = all_devices  # noqa: SLF001

        return self

    @model_validator(mode="after")
    def validate_remote_device_references(self) -> "FabricDataModel":
        """
        Validate that all remote_device references point to existing devices.

        Iterates through all interfaces and verifies that any interface with
        remote_device set references a hostname that exists in the topology.

        Raises:
            ValueError: If an interface references a non-existent device.

        Returns:
            FabricDataModel: The validated model.
        """
        all_devices = self.topology.spines + self.topology.leaves
        valid_hostnames = {device.hostname for device in all_devices}

        for device in all_devices:
            for interface in device.interfaces:
                if not interface.remote_device:
                    continue

                if interface.remote_device not in valid_hostnames:
                    msg = (
                        f"Device '{device.hostname}' interface '{interface.name}' "
                        f"references non-existent remote device '{interface.remote_device}'. "
                        f"Valid devices: {sorted(valid_hostnames)}"
                    )
                    raise ValueError(msg)

        return self

    @model_validator(mode="after")
    def validate_unique_ipv4_addresses(self) -> "FabricDataModel":
        """
        Validate that all IPv4 addresses are unique across the fabric.

        Iterates through all interfaces and verifies that no two interfaces
        share the same IPv4 address. This prevents configuration errors
        where duplicate IPs could cause routing issues.

        Raises:
            ValueError: If duplicate IPv4 addresses are detected.

        Returns:
            FabricDataModel: The validated model.
        """
        all_devices = self.topology.spines + self.topology.leaves
        tracked_ipv4s: dict[IPv4Interface, str] = {}  # IP -> device.interface

        for device in all_devices:
            for interface in device.interfaces:
                ip = interface.ipv4
                location = f"{device.hostname}.{interface.name}"

                if ip in tracked_ipv4s:
                    duplicated_ipv4_location = tracked_ipv4s[ip]
                    msg = (
                        f"Duplicate IPv4 Address '{ip}' detected: {location} conflicts with {duplicated_ipv4_location}"
                    )
                    raise ValueError(msg)

                tracked_ipv4s[ip] = location

        return self

    @model_validator(mode="after")
    def validate_ip_pool_allocation(self) -> "FabricDataModel":
        """
        Validate that all interface IPs are within their designated pools.

        Verifies that:
            - Management0 IPs are within management_pool.ipv4_subnet
            - Loopback0 IPs are within loopback0_pool
            - Loopback1 IPs are within loopback1_pool
            - P2P (Ethernet) IPs are within p2p_pool

        Raises:
            ValueError: If any IP is outside its designated pool.

        Returns:
            FabricDataModel: The validated model.
        """
        all_devices = self.topology.spines + self.topology.leaves

        for device in all_devices:
            for interface in device.interfaces:
                ip = interface.ipv4
                location = f"{device.hostname}.{interface.name}"

                # Check pool based on interface type
                if interface.name == "Management0" and ip not in self.reserved_supernets.management_pool.ipv4_subnet:
                    msg = (
                        f"Management IP '{ip}' at {location} is outside "
                        f"management pool {self.reserved_supernets.management_pool.ipv4_subnet}"
                    )
                    raise ValueError(msg)

                if interface.name == "Loopback0" and ip not in self.reserved_supernets.loopback0_pool:
                    msg = (
                        f"Loopback0 IP '{ip}' at {location} is outside "
                        f"Loopback0 pool {self.reserved_supernets.loopback0_pool}"
                    )
                    raise ValueError(msg)

                if interface.name == "Loopback1" and ip not in self.reserved_supernets.loopback1_pool:
                    msg = (
                        f"Loopback1 IP '{ip}' at {location} is outside "
                        f"Loopback1 pool {self.reserved_supernets.loopback1_pool}"
                    )
                    raise ValueError(msg)

                if interface.name.startswith("Ethernet") and ip not in self.reserved_supernets.p2p_pool:
                    msg = f"P2P IP '{ip}' at {location} is outside P2P pool {self.reserved_supernets.p2p_pool}"
                    raise ValueError(msg)

        return self
