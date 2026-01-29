"""
Fabric topology models.

This module provides models for network fabric topology structure including
spine and leaf device organization.
"""

from pydantic import BaseModel, Field

from .device import Device


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
