"""
Network fabric data models with validation and computed fields.

This module provides Pydantic-based data models for defining and validating
network fabric configurations including topology, IP allocation, and device
parameters.

Features:
    - Type-safe data validation using Pydantic
    - Computed fields for derived values (role, descriptions, VRF assignments)
    - Data loaders for YAML and JSON formats
    - Multiple export formats (JSON, YAML, Python dict, CSV)
    - IPv4/IPv6 address validation
    - BGP ASN management
    - Support for 3-stage Clos fabric architectures

Models:
    - FabricDataModel: Root model containing complete fabric configuration
    - Topology: Spine and leaf device topology structure
    - Device: Individual network device with interfaces
    - Interface: Network interface with IP addressing
    - ReservedSupernets: IP address pool allocations
    - ManagementPool: Management network configuration

Data Loaders:
    - load_from_yaml: Load fabric from YAML file
    - load_from_json: Load fabric from JSON file
    - load_fabric: Auto-detect format and load

Example:
    Load a fabric configuration from YAML:

    ```python
    from py_netauto.datamodel import load_from_yaml

    fabric = load_from_yaml("datamodel.yml")
    print(f"Fabric: {fabric.fabric_name}")
    print(f"Spines: {len(fabric.topology.spines)}")
    ```
"""

from .device import Device
from .fabric import FabricDataModel
from .interface import Interface
from .loaders import load_fabric, load_from_json, load_from_yaml
from .network import ManagementPool, ReservedSupernets
from .topology import Topology

__all__ = [
    "Device",
    "FabricDataModel",
    "Interface",
    "ManagementPool",
    "ReservedSupernets",
    "Topology",
    "load_fabric",
    "load_from_json",
    "load_from_yaml",
]
