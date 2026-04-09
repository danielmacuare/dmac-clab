"""JSON Schema export functionality for fabric data models.

This module provides functions to export FabricDataModel JSON Schema
for API documentation, validation, and third-party tool integration.
"""

import json
from pathlib import Path

from py_netauto.datamodel.fabric import FabricDataModel

from .base import ExporterBase, ExporterRegistry


class JSONSchemaExporter(ExporterBase):
    """Exporter for JSON Schema format.

    Exports the Pydantic model schema as JSON Schema, which can be used
    for API documentation, validation, and code generation in other languages.
    """

    def export(self, model: FabricDataModel, output_path: Path) -> None:
        """Export fabric data model schema to JSON Schema file.

        Args:
            model: The fabric data model to export schema from.
            output_path: Path where the JSON Schema file should be written.

        Raises:
            PermissionError: If the output file cannot be written.
            OSError: If there are disk space or other I/O issues.
        """
        # Generate JSON Schema from the Pydantic model
        schema = model.model_json_schema()

        # Add metadata to the schema
        schema["title"] = "Fabric Data Model Schema"
        schema["description"] = "JSON Schema for network fabric data model validation and documentation"

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(
                    schema,
                    f,
                    indent=2,
                    sort_keys=False,
                    ensure_ascii=False,
                )
        except PermissionError as e:
            msg = f"Permission denied writing to {output_path}: {e}"
            raise PermissionError(msg) from e
        except OSError as e:
            msg = f"Failed to write JSON Schema file {output_path}: {e}"
            raise OSError(msg) from e


def export_json_schema(model: FabricDataModel, output_path: str | Path, *, pretty: bool = True) -> None:
    """Export fabric data model JSON Schema.

    Convenience function that exports the JSON Schema for a fabric data model.
    The schema can be used for validation, API documentation, and code generation.

    Args:
        model: The fabric data model to export schema from.
        output_path: Path where the JSON Schema file should be written.
        pretty: Whether to pretty-print the JSON Schema (default: True).

    Raises:
        PermissionError: If the output file cannot be written.
        OSError: If there are disk space or other I/O issues.

    Example:
        >>> from py_netauto.datamodel import load_from_yaml
        >>> from py_netauto.datamodel.exporters import export_json_schema
        >>> fabric = load_from_yaml("datamodel.yml")
        >>> export_json_schema(fabric, "fabric-schema.json")
        >>> # Export without pretty-printing
        >>> export_json_schema(fabric, "compact-schema.json", pretty=False)
    """
    output_path = Path(output_path)

    # Generate JSON Schema from the Pydantic model
    schema = model.model_json_schema()

    # Add metadata to the schema
    schema["title"] = "Fabric Data Model Schema"
    schema["description"] = "JSON Schema for network fabric data model validation and documentation"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with output_path.open("w", encoding="utf-8") as f:
            if pretty:
                json.dump(
                    schema,
                    f,
                    indent=2,
                    sort_keys=False,
                    ensure_ascii=False,
                )
            else:
                json.dump(
                    schema,
                    f,
                    separators=(",", ":"),
                    ensure_ascii=False,
                )
    except PermissionError as e:
        msg = f"Permission denied writing to {output_path}: {e}"
        raise PermissionError(msg) from e
    except OSError as e:
        msg = f"Failed to write JSON Schema file {output_path}: {e}"
        raise OSError(msg) from e


# Register the JSON Schema exporter
ExporterRegistry.register("json-schema", JSONSchemaExporter)
