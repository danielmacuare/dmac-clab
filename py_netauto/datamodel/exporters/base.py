"""Base classes for fabric data model exporters.

This module provides the abstract base class and registry system
for implementing different export formats.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

from py_netauto.datamodel.fabric import FabricDataModel


class ExporterBase(ABC):
    """Abstract base class for fabric data model exporters.

    All exporters must inherit from this class and implement the export method.
    This ensures a consistent interface across all export formats.
    """

    @abstractmethod
    def export(self, model: FabricDataModel, output_path: Path) -> None:
        """Export fabric data model to the specified output path.

        Args:
            model: The fabric data model to export.
            output_path: Path where the exported data should be written.

        Raises:
            NotImplementedError: If the subclass doesn't implement this method.
        """
        msg = "Subclasses must implement the export method"
        raise NotImplementedError(msg)


class ExporterRegistry:
    """Registry for managing available export formats.

    Provides a centralized way to register and retrieve exporters
    for different output formats.
    """

    _exporters: ClassVar[dict[str, type[ExporterBase]]] = {}

    @classmethod
    def register(cls, format_name: str, exporter_class: type[ExporterBase]) -> None:
        """Register an exporter for a specific format.

        Args:
            format_name: Name of the export format (e.g., 'json', 'yaml').
            exporter_class: The exporter class to register.
        """
        cls._exporters[format_name] = exporter_class

    @classmethod
    def get_exporter(cls, format_name: str) -> ExporterBase:
        """Get an exporter instance for the specified format.

        Args:
            format_name: Name of the export format.

        Returns:
            ExporterBase: An instance of the requested exporter.

        Raises:
            ValueError: If the format is not registered.
        """
        if format_name not in cls._exporters:
            available = list(cls._exporters.keys())
            msg = f"Unknown export format '{format_name}'. Available formats: {available}"
            raise ValueError(msg)

        return cls._exporters[format_name]()

    @classmethod
    def available_formats(cls) -> list[str]:
        """Get list of available export formats.

        Returns:
            list[str]: List of registered format names.
        """
        return list(cls._exporters.keys())
