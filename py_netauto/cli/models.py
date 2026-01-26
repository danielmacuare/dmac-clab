"""
Data models for the network configuration CLI.

This module provides Pydantic models for validating and managing CLI data structures
including filter expressions, operation results, and path configurations.

"""

from enum import Enum
from pathlib import Path

from nornir.core.filter import AND, OR, F
from pydantic import BaseModel, Field, computed_field, field_validator, model_validator


class FilterExpression(BaseModel):
    """
    Represent a parsed filter expression.

    This model encapsulates CLI filter arguments and their compiled Nornir F() filter
    representation, providing validation and human-readable display formatting.

    Attributes:
        raw_filters: Original filter strings from CLI arguments.
        nornir_filter: Compiled Nornir F() filter object.
        display_text: Human-readable representation of the filter.

    """

    raw_filters: list[str] = Field(default_factory=list)
    nornir_filter: F | OR | AND | None = Field(default=None, exclude=True)
    display_text: str = Field(default="No filters applied")

    model_config = {"arbitrary_types_allowed": True}

    @classmethod
    def from_cli_args(cls, filter_strings: list[str] | None) -> "FilterExpression":
        """
        Create FilterExpression from CLI arguments.

        Parses CLI filter strings into a Nornir F() filter expression and generates
        a human-readable display representation.

        Args:
            filter_strings: List of filter strings from CLI (e.g., ["role=leaf", "name=l1"]).

        Returns:
            FilterExpression instance with parsed filter.

        Example:
            ```python
            expr = FilterExpression.from_cli_args(["role=leaf", "name=l1|l2"])
            nr_filtered = nr.filter(expr.nornir_filter)
            print(expr.display_text)  # "role=leaf AND name=l1|l2"
            ```

        """
        if not filter_strings:
            return cls()

        # Import here to avoid circular dependency with filters module
        from py_netauto.cli.filters import format_filter_expression, parse_filters  # noqa: PLC0415

        nornir_filter = parse_filters(filter_strings)
        display_text = format_filter_expression(filter_strings)

        return cls(
            raw_filters=filter_strings,
            nornir_filter=nornir_filter,
            display_text=display_text,
        )


class OperationStatus(str, Enum):
    """
    Status of an operation.

    Inherits from str to make it JSON serializable and compatible with string
    comparisons.

    """

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class DeviceResult(BaseModel):
    """
    Result of an operation on a single device.

    Captures the outcome of a configuration operation (render, push, etc.) for
    a specific network device, including status, messages, and optional diff output.

    Attributes:
        hostname: Name of the device.
        status: Operation status (success, failed, skipped).
        message: Descriptive message about the operation result.
        diff: Configuration diff (optional, for push operations).

    """

    hostname: str = Field(..., min_length=1)
    status: OperationStatus
    message: str
    diff: str | None = Field(default=None)

    @field_validator("hostname")
    @classmethod
    def validate_hostname(cls, v: str) -> str:
        """
        Validate hostname is not empty or whitespace.

        Args:
            v: Hostname value to validate.

        Returns:
            Validated hostname.

        Raises:
            ValueError: If hostname is empty or whitespace.

        """
        if not v.strip():
            raise ValueError("Hostname cannot be empty or whitespace")
        return v.strip()


class OperationResult(BaseModel):
    """
    Aggregated results for an operation across multiple devices.

    Collects and summarizes the results of a configuration operation performed
    on multiple network devices, providing computed statistics and summary methods.

    Attributes:
        operation: Name of the operation (e.g., "render", "push").
        device_results: List of results for each device.

    """

    operation: str = Field(..., min_length=1)
    device_results: list[DeviceResult] = Field(default_factory=list)

    @computed_field
    @property
    def total_devices(self) -> int:
        """
        Total number of devices processed.

        Returns:
            Count of devices in device_results.

        """
        return len(self.device_results)

    @computed_field
    @property
    def success_count(self) -> int:
        """
        Number of successful operations.

        Returns:
            Count of devices with SUCCESS status.

        """
        return sum(1 for r in self.device_results if r.status == OperationStatus.SUCCESS)

    @computed_field
    @property
    def failed_count(self) -> int:
        """
        Number of failed operations.

        Returns:
            Count of devices with FAILED status.

        """
        return sum(1 for r in self.device_results if r.status == OperationStatus.FAILED)

    @computed_field
    @property
    def skipped_count(self) -> int:
        """
        Number of skipped operations.

        Returns:
            Count of devices with SKIPPED status.

        """
        return sum(1 for r in self.device_results if r.status == OperationStatus.SKIPPED)

    def to_summary_dict(self) -> dict[str, int | str]:
        """
        Convert operation result to summary dictionary.

        Returns:
            Dictionary with operation summary statistics.

        Example:
            ```python
            result = OperationResult(operation="render", device_results=[...])
            summary = result.to_summary_dict()
            # {'operation': 'render', 'total': 5, 'success': 4, 'failed': 1, 'skipped': 0}
            ```

        """
        return {
            "operation": self.operation,
            "total": self.total_devices,
            "success": self.success_count,
            "failed": self.failed_count,
            "skipped": self.skipped_count,
        }


class PathConfiguration(BaseModel):
    """
    Configuration for templates and output paths.

    Manages and validates directory paths for Jinja2 templates and generated
    configuration output, supporting both environment defaults and CLI overrides.

    Attributes:
        templates_dir: Path to Jinja2 templates directory.
        output_dir: Path to output directory for generated configs.
        is_templates_override: Whether templates_dir is a CLI override.
        is_output_override: Whether output_dir is a CLI override.

    """

    templates_dir: Path
    output_dir: Path
    is_templates_override: bool = Field(default=False)
    is_output_override: bool = Field(default=False)

    @field_validator("templates_dir")
    @classmethod
    def validate_templates_dir(cls, v: Path) -> Path:
        """
        Validate templates directory exists and is a directory.

        Args:
            v: Templates directory path.

        Returns:
            Validated templates directory path.

        Raises:
            FileNotFoundError: If directory doesn't exist.
            ValueError: If path is not a directory.

        """
        if not v.exists():
            msg = f"Templates directory not found: {v}"
            raise FileNotFoundError(msg)
        if not v.is_dir():
            msg = f"Templates path is not a directory: {v}"
            raise ValueError(msg)
        return v

    @field_validator("output_dir")
    @classmethod
    def validate_output_dir(cls, v: Path) -> Path:
        """
        Validate output directory path.

        Creates the directory if it doesn't exist and is writable.

        Args:
            v: Output directory path.

        Returns:
            Validated output directory path.

        Raises:
            PermissionError: If directory cannot be created or is not writable.
            ValueError: If path exists but is not a directory.

        """
        if not v.exists():
            try:
                v.mkdir(parents=True, exist_ok=True)
            except PermissionError as e:
                msg = f"Cannot create output directory: {v}"
                raise PermissionError(msg) from e

        if not v.is_dir():
            msg = f"Output path is not a directory: {v}"
            raise ValueError(msg)

        # Check write permissions
        if not v.stat().st_mode & 0o200:  # Check owner write permission
            msg = f"Output directory is not writable: {v}"
            raise PermissionError(msg)

        return v

    @model_validator(mode="after")
    def validate_templates_exist(self) -> "PathConfiguration":
        """
        Validate that templates directory contains .j2 files.

        Returns:
            Self after validation.

        Raises:
            ValueError: If no .j2 template files found.

        """
        template_files = list(self.templates_dir.glob("*.j2"))
        if not template_files:
            msg = f"No Jinja2 templates (*.j2) found in templates directory: {self.templates_dir}"
            raise ValueError(msg)
        return self
