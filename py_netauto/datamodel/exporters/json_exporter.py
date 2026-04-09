"""JSON export functionality for fabric data models.

This module provides functions to export FabricDataModel instances
to JSON format with pretty-printing and comprehensive error handling.
"""

import json
from pathlib import Path

from py_netauto.datamodel.fabric import FabricDataModel

from .base import ExporterBase, ExporterRegistry


class JSONExporter(ExporterBase):
    """Exporter for JSON format.

    Exports fabric data models to JSON with pretty-printing,
    proper indentation, and all computed fields included.
    """

    def export(self, model: FabricDataModel, output_path: Path) -> None:
        """Export fabric data model to JSON file.

        Args:
            model: The fabric data model to export.
            output_path: Path where the JSON file should be written.

        Raises:
            PermissionError: If the output file cannot be written.
            OSError: If there are disk space or other I/O issues.
        """
        # Convert model to JSON-serializable dictionary with all computed fields
        data = model.model_dump(mode="json", exclude_none=False)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(
                    data,
                    f,
                    indent=2,
                    sort_keys=False,
                    ensure_ascii=False,
                )
        except PermissionError as e:
            msg = f"Permission denied writing to {output_path}: {e}"
            raise PermissionError(msg) from e
        except OSError as e:
            msg = f"Failed to write JSON file {output_path}: {e}"
            raise OSError(msg) from e


def export_json(model: FabricDataModel, output_path: str | Path, *, pretty: bool = True) -> None:
    """Export fabric data model to JSON format.

    Convenience function that exports a fabric data model to a JSON file
    with pretty-printing enabled by default. All computed fields are included
    in the output.

    Args:
        model: The fabric data model to export.
        output_path: Path where the JSON file should be written.
        pretty: Whether to pretty-print the JSON (default: True).

    Raises:
        PermissionError: If the output file cannot be written.
        OSError: If there are disk space or other I/O issues.

    Example:
        >>> from py_netauto.datamodel import load_from_yaml
        >>> from py_netauto.datamodel.exporters import export_json
        >>> fabric = load_from_yaml("datamodel.yml")
        >>> export_json(fabric, "output.json")
        >>> # Export without pretty-printing
        >>> export_json(fabric, "compact.json", pretty=False)
    """
    output_path = Path(output_path)

    # Convert model to JSON-serializable dictionary with all computed fields
    data = model.model_dump(mode="json", exclude_none=False)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with output_path.open("w", encoding="utf-8") as f:
            if pretty:
                json.dump(
                    data,
                    f,
                    indent=2,
                    sort_keys=False,
                    ensure_ascii=False,
                )
            else:
                json.dump(
                    data,
                    f,
                    separators=(",", ":"),
                    ensure_ascii=False,
                )
    except PermissionError as e:
        msg = f"Permission denied writing to {output_path}: {e}"
        raise PermissionError(msg) from e
    except OSError as e:
        msg = f"Failed to write JSON file {output_path}: {e}"
        raise OSError(msg) from e


# Register the JSON exporter
ExporterRegistry.register("json", JSONExporter)
