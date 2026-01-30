"""
Root fabric data model.

This module provides the root FabricDataModel that contains all configuration
data for a network fabric including topology, IP allocation, and ASN assignments.
"""

from pydantic import BaseModel, Field, model_validator

from .network import ReservedSupernets
from .topology import Topology


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

    @model_validator(mode="after")
    def inject_fabric_asns(self) -> "FabricDataModel":
        """Inject fabric_asns into all devices after model initialization."""
        for device in self.topology.spines + self.topology.leaves:
            device._fabric_asns = self.fabric_asns  # noqa: SLF001

        return self
