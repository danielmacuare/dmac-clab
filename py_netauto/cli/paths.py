"""
Path management for templates and output directories.

This module handles directory path overrides and validation for CLI operations,
allowing runtime overrides while respecting environment defaults.

"""

from pathlib import Path

from py_netauto.config import (
    GENERATED_CONFIGS_FOLDER_PATH,
    JINJA_TEMPLATES_FOLDER_PATH,
)


class PathManager:
    """
    Manage path overrides for templates and output directories.

    This class handles directory path resolution with override precedence:
    CLI argument override > environment variable > default value.

    Attributes:
        templates_dir: Path to Jinja2 templates directory.
        output_dir: Path to output directory for generated configs.

    """

    def __init__(
        self,
        templates_override: Path | None = None,
        output_override: Path | None = None,
    ) -> None:
        """
        Initialize path manager with optional overrides.

        Args:
            templates_override: Optional path to override default templates directory.
            output_override: Optional path to override default output directory.

        """
        self.templates_dir = templates_override or JINJA_TEMPLATES_FOLDER_PATH
        self.output_dir = output_override or GENERATED_CONFIGS_FOLDER_PATH

    def validate_templates_dir(self) -> None:
        """
        Validate templates directory exists and contains .j2 files.

        Raises:
            FileNotFoundError: If templates directory doesn't exist.
            ValueError: If path is not a directory or contains no .j2 files.

        """
        if not self.templates_dir.exists():
            msg = f"Templates directory not found: {self.templates_dir}"
            raise FileNotFoundError(msg)

        if not self.templates_dir.is_dir():
            msg = f"Templates path is not a directory: {self.templates_dir}"
            raise ValueError(msg)

        # Check for .j2 template files
        template_files = list(self.templates_dir.glob("*.j2"))
        if not template_files:
            msg = f"No Jinja2 templates (*.j2) found in templates directory: {self.templates_dir}"
            raise ValueError(msg)

    def ensure_output_dir(self) -> None:
        """
        Ensure output directory exists, create if necessary.

        Raises:
            PermissionError: If directory cannot be created or is not writable.
            ValueError: If path exists but is not a directory.

        """
        if not self.output_dir.exists():
            try:
                self.output_dir.mkdir(parents=True, exist_ok=True)
            except PermissionError as e:
                msg = f"Cannot create output directory: {self.output_dir}"
                raise PermissionError(msg) from e

        if not self.output_dir.is_dir():
            msg = f"Output path is not a directory: {self.output_dir}"
            raise ValueError(msg)

        # Check write permissions
        if not self.output_dir.stat().st_mode & 0o200:  # Check owner write permission
            msg = f"Output directory is not writable: {self.output_dir}"
            raise PermissionError(msg)

    def get_templates_path(self) -> Path:
        """
        Get the active templates directory path.

        Returns:
            Path to templates directory.

        """
        return self.templates_dir

    def get_output_path(self) -> Path:
        """
        Get the active output directory path.

        Returns:
            Path to output directory.

        """
        return self.output_dir
