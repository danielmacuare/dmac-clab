"""
Fabric topology models.

This module provides models for network fabric topology structure including
spine and leaf device organization.
"""

from pydantic import BaseModel, Field, field_validator

from .device import Device


class DeviceGroup(BaseModel):
    """
    Group of devices with a shared Nornir inventory group.

    This model wraps a list of devices (spines or leaves) and associates
    them with a Nornir inventory group name for automation purposes.
    """

    nornir_group: str = Field(
        description="Nornir inventory group name for all devices in this group",
        examples=["spine_group", "leaf_group", "SPINES", "LEAVES", "DC1_SPINES"],
    )
    devices: list[Device] = Field(
        description="List of devices in this group",
        examples=[],
    )


class Topology(BaseModel):
    """
    Network fabric topology structure.

    Defines the physical topology of the fabric including all spine
    and leaf devices in a 3-stage Clos architecture.
    """

    platform: str = Field(
        default="arista_eos",
        description="Default platform type for all devices (e.g., arista_eos, cisco_ios). Can be overridden per device.",
        examples=["arista_eos", "cisco_ios", "juniper_junos", "nokia_sros"],
    )
    ecmp_maximum_paths: int = Field(
        description="Maximum number of ECMP paths for load balancing (1-128)",
        examples=[64, 32, 128],
    )
    bgp_maximum_routes: int = Field(
        description="Maximum number of BGP routes allowed (0-4294967294)",
        examples=[12000, 10000, 50000],
    )
    spines: DeviceGroup = Field(
        description="Spine switches group with Nornir inventory group name",
    )
    leaves: DeviceGroup = Field(
        description="Leaf switches group with Nornir inventory group name",
    )

    @field_validator("ecmp_maximum_paths")
    @classmethod
    def validate_ecmp_maximum_paths(cls, v: int) -> int:
        """
        Validate ECMP maximum paths is within valid range.

        ECMP (Equal-Cost Multi-Path) maximum paths determines how many
        parallel paths can be used for load balancing. The value must be
        between 1 and 128.

        Args:
            v: The ECMP maximum paths value to validate.

        Returns:
            int: The validated ECMP maximum paths value.

        Raises:
            ValueError: If value is outside the valid range (1-128).

        Example:
            >>> Topology.validate_ecmp_maximum_paths(64)
            64
            >>> Topology.validate_ecmp_maximum_paths(0)  # doctest: +SKIP
            ValueError: ECMP maximum paths must be between 1 and 128...
        """
        min_paths = 1
        max_paths = 128

        if not (min_paths <= v <= max_paths):
            msg = (
                f"ECMP maximum paths must be between {min_paths} and {max_paths}. "
                f"Got: {v}. Common values: 64 (default), 32 (conservative), 128 (maximum)"
            )
            raise ValueError(msg)

        return v

    @field_validator("bgp_maximum_routes")
    @classmethod
    def validate_bgp_maximum_routes(cls, v: int) -> int:
        """
        Validate BGP maximum routes is within valid range.

        BGP maximum routes determines the maximum number of routes that can
        be learned from BGP peers. The value must be between 0 and 4294967294
        (2^32 - 2).

        Args:
            v: The BGP maximum routes value to validate.

        Returns:
            int: The validated BGP maximum routes value.

        Raises:
            ValueError: If value is outside the valid range (0-4294967294).

        Example:
            >>> Topology.validate_bgp_maximum_routes(12000)
            12000
            >>> Topology.validate_bgp_maximum_routes(-1)  # doctest: +SKIP
            ValueError: BGP maximum routes must be between 0 and 4294967294...
        """
        min_routes = 0
        max_routes = 4294967294  # 2^32 - 2

        if not (min_routes <= v <= max_routes):
            msg = (
                f"BGP maximum routes must be between {min_routes} and {max_routes}. "
                f"Got: {v}. Common values: 12000 (default), 10000 (small), 50000 (large), 0 (unlimited)"
            )
            raise ValueError(msg)

        return v
