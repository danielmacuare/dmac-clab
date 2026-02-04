"""YAML export functionality for fabric data models.

This module provides functions to export FabricDataModel instances
to YAML format with pretty-printing and comprehensive error handling.
"""

import ipaddress
from pathlib import Path
from typing import Any

import yaml

from py_netauto.datamodel.fabric import FabricDataModel

from .base import ExporterBase, ExporterRegistry


def _convert_to_yaml_compatible(obj: Any) -> Any:
    """Convert Python objects to YAML-compatible representations.

    This function recursively converts Python objects that would otherwise
    be serialized with Python-specific YAML tags to their string representations,
    making the YAML portable and readable by any YAML parser.

    Args:
        obj: The object to convert.

    Returns:
        A YAML-compatible representation of the object.
    """
    if isinstance(obj, (ipaddress.IPv4Interface, ipaddress.IPv6Interface)):
        return str(obj)
    elif isinstance(obj, (ipaddress.IPv4Network, ipaddress.IPv6Network)):
        return str(obj)
    elif isinstance(obj, (ipaddress.IPv4Address, ipaddress.IPv6Address)):
        return str(obj)
    elif isinstance(obj, Path):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: _convert_to_yaml_compatible(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_convert_to_yaml_compatible(item) for item in obj]
    elif isinstance(obj, tuple):
        return [_convert_to_yaml_compatible(item) for item in obj]
    else:
        return obj


class YAMLExporter(ExporterBase):
    """Exporter for YAML format.

    Exports fabric data models to YAML with proper formatting,
    indentation, and all computed fields included.
    """

    def export(self, model: FabricDataModel, output_path: Path) -> None:
        """Export fabric data model to YAML file.

        Args:
            model: The fabric data model to export.
            output_path: Path where the YAML file should be written.

        Raises:
            PermissionError: If the output file cannot be written.
            OSError: If there are disk space or other I/O issues.
        """
        # Convert model to Python dictionary with all computed fields
        data = model.model_dump(mode="python", exclude_none=False)

        # Convert Python objects to YAML-compatible representations
        yaml_data = _convert_to_yaml_compatible(data)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with output_path.open("w", encoding="utf-8") as f:
                yaml.dump(
                    yaml_data,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    indent=2,
                    allow_unicode=True,
                )
        except PermissionError as e:
            msg = f"Permission denied writing to {output_path}: {e}"
            raise PermissionError(msg) from e
        except OSError as e:
            msg = f"Failed to write YAML file {output_path}: {e}"
            raise OSError(msg) from e


def export_yaml(model: FabricDataModel, output_path: str | Path, *, pretty: bool = True) -> None:
    """Export fabric data model to YAML format.

    Convenience function that exports a fabric data model to a YAML file
    with pretty-printing enabled by default. All computed fields are included
    in the output. Python objects like IP addresses are converted to strings
    for maximum YAML portability.

    Args:
        model: The fabric data model to export.
        output_path: Path where the YAML file should be written.
        pretty: Whether to pretty-print the YAML (default: True).

    Raises:
        PermissionError: If the output file cannot be written.
        OSError: If there are disk space or other I/O issues.

    Example:
        >>> from py_netauto.datamodel import load_from_yaml
        >>> from py_netauto.datamodel.exporters import export_yaml
        >>> fabric = load_from_yaml("datamodel.yml")
        >>> export_yaml(fabric, "output.yml")
        >>> # Export without pretty-printing (compact)
        >>> export_yaml(fabric, "compact.yml", pretty=False)
    """
    output_path = Path(output_path)

    # Convert model to Python dictionary with all computed fields
    data = model.model_dump(mode="python", exclude_none=False)

    # Convert Python objects to YAML-compatible representations
    yaml_data = _convert_to_yaml_compatible(data)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with output_path.open("w", encoding="utf-8") as f:
            if pretty:
                yaml.dump(
                    yaml_data,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    indent=2,
                    allow_unicode=True,
                )
            else:
                # Compact YAML (less readable but smaller)
                yaml.dump(
                    yaml_data,
                    f,
                    default_flow_style=True,
                    sort_keys=False,
                    allow_unicode=True,
                )
    except PermissionError as e:
        msg = f"Permission denied writing to {output_path}: {e}"
        raise PermissionError(msg) from e
    except OSError as e:
        msg = f"Failed to write YAML file {output_path}: {e}"
        raise OSError(msg) from e


# Register the YAML exporter
ExporterRegistry.register("yaml", YAMLExporter)
