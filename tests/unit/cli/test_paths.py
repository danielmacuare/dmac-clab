"""Unit tests for path management."""

import pytest

from py_netauto.cli.paths import PathManager


class TestPathManager:
    """Test PathManager class."""

    def test_default_initialization(self):
        """Default initialization should use environment defaults."""
        manager = PathManager()
        assert manager.templates_dir is not None
        assert manager.output_dir is not None

    def test_initialization_with_overrides(self, tmp_path):
        """Initialization with overrides should use provided paths."""
        templates_override = tmp_path / "custom_templates"
        output_override = tmp_path / "custom_output"

        manager = PathManager(
            templates_override=templates_override,
            output_override=output_override,
        )
        assert manager.templates_dir == templates_override
        assert manager.output_dir == output_override

    def test_get_templates_path(self, tmp_path):
        """get_templates_path should return templates directory."""
        templates_dir = tmp_path / "templates"
        manager = PathManager(templates_override=templates_dir)
        assert manager.get_templates_path() == templates_dir

    def test_get_output_path(self, tmp_path):
        """get_output_path should return output directory."""
        output_dir = tmp_path / "output"
        manager = PathManager(output_override=output_dir)
        assert manager.get_output_path() == output_dir

    def test_validate_templates_dir_success(self, tmp_path):
        """validate_templates_dir should succeed with valid directory."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "test.j2").touch()

        manager = PathManager(templates_override=templates_dir)
        manager.validate_templates_dir()  # Should not raise

    def test_validate_templates_dir_not_exists(self, tmp_path):
        """validate_templates_dir should raise FileNotFoundError if directory doesn't exist."""
        templates_dir = tmp_path / "nonexistent"
        manager = PathManager(templates_override=templates_dir)

        with pytest.raises(FileNotFoundError, match="Templates directory not found"):
            manager.validate_templates_dir()

    def test_validate_templates_dir_not_directory(self, tmp_path):
        """validate_templates_dir should raise ValueError if path is not a directory."""
        templates_file = tmp_path / "templates.txt"
        templates_file.touch()

        manager = PathManager(templates_override=templates_file)

        with pytest.raises(ValueError, match="not a directory"):
            manager.validate_templates_dir()

    def test_validate_templates_dir_no_j2_files(self, tmp_path):
        """validate_templates_dir should raise ValueError if no .j2 files found."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "readme.txt").touch()

        manager = PathManager(templates_override=templates_dir)

        with pytest.raises(ValueError, match="No Jinja2 templates"):
            manager.validate_templates_dir()

    def test_ensure_output_dir_creates_directory(self, tmp_path):
        """ensure_output_dir should create directory if it doesn't exist."""
        output_dir = tmp_path / "output"
        manager = PathManager(output_override=output_dir)

        assert not output_dir.exists()
        manager.ensure_output_dir()
        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_ensure_output_dir_with_existing_directory(self, tmp_path):
        """ensure_output_dir should succeed with existing directory."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        manager = PathManager(output_override=output_dir)
        manager.ensure_output_dir()  # Should not raise

    def test_ensure_output_dir_not_directory(self, tmp_path):
        """ensure_output_dir should raise ValueError if path is not a directory."""
        output_file = tmp_path / "output.txt"
        output_file.touch()

        manager = PathManager(output_override=output_file)

        with pytest.raises(ValueError, match="not a directory"):
            manager.ensure_output_dir()

    def test_ensure_output_dir_creates_nested_directories(self, tmp_path):
        """ensure_output_dir should create nested directories."""
        output_dir = tmp_path / "level1" / "level2" / "output"
        manager = PathManager(output_override=output_dir)

        assert not output_dir.exists()
        manager.ensure_output_dir()
        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_templates_override_precedence(self, tmp_path):
        """Templates override should take precedence over environment default."""
        templates_override = tmp_path / "custom_templates"
        manager = PathManager(templates_override=templates_override)

        # Override should be used
        assert manager.templates_dir == templates_override

    def test_output_override_precedence(self, tmp_path):
        """Output override should take precedence over environment default."""
        output_override = tmp_path / "custom_output"
        manager = PathManager(output_override=output_override)

        # Override should be used
        assert manager.output_dir == output_override

    def test_partial_override(self, tmp_path):
        """Partial override should use override for one path and default for other."""
        templates_override = tmp_path / "custom_templates"
        manager = PathManager(templates_override=templates_override)

        # Templates should use override
        assert manager.templates_dir == templates_override
        # Output should use default (not None)
        assert manager.output_dir is not None
