"""
Network fabric data models with validation and computed fields.

This module provides Pydantic-based data models for defining and validating
network fabric configurations including topology, IP allocation, and device
parameters.

Features:
    - Type-safe data validation using Pydantic
    - Computed fields for derived values (role, descriptions, VRF assignments)
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

Example:
    Load a fabric configuration from YAML:

    ```python
    from pathlib import Path
    import yaml
    from py_netauto.datamodel import FabricDataModel

    yaml_path = Path("datamodel.yml")
    with yaml_path.open() as f:
        data = yaml.safe_load(f)

    fabric = FabricDataModel(**data)
    print(f"Fabric: {fabric.fabric_name}")
    print(f"Spines: {len(fabric.topology.spines)}")
    ```
"""

from .device import Device
from .fabric import FabricDataModel
from .interface import Interface
from .network import ManagementPool, ReservedSupernets
from .topology import Topology

__all__ = [
    "Device",
    "FabricDataModel",
    "Interface",
    "ManagementPool",
    "ReservedSupernets",
    "Topology",
]
