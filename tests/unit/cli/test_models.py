"""Unit tests for Pydantic data models."""

import pytest
from pydantic import ValidationError

from py_netauto.cli.models import (
    DeviceResult,
    FilterExpression,
    OperationResult,
    OperationStatus,
    PathConfiguration,
)


class TestFilterExpression:
    """Test FilterExpression model."""

    def test_default_initialization(self):
        """Default initialization should create empty filter."""
        expr = FilterExpression()
        assert expr.raw_filters == []
        assert expr.nornir_filter is None
        assert expr.display_text == "No filters applied"

    def test_from_cli_args_with_none(self):
        """from_cli_args with None should create empty filter."""
        expr = FilterExpression.from_cli_args(None)
        assert expr.raw_filters == []
        assert expr.nornir_filter is None
        assert expr.display_text == "No filters applied"

    def test_from_cli_args_with_empty_list(self):
        """from_cli_args with empty list should create empty filter."""
        expr = FilterExpression.from_cli_args([])
        assert expr.raw_filters == []
        assert expr.nornir_filter is None
        assert expr.display_text == "No filters applied"

    def test_from_cli_args_with_single_filter(self):
        """from_cli_args with single filter should parse correctly."""
        expr = FilterExpression.from_cli_args(["role=leaf"])
        assert expr.raw_filters == ["role=leaf"]
        assert expr.nornir_filter is not None
        assert expr.display_text == "role=leaf"

    def test_from_cli_args_with_multiple_filters(self):
        """from_cli_args with multiple filters should parse correctly."""
        expr = FilterExpression.from_cli_args(["role=leaf", "name=l1"])
        assert expr.raw_filters == ["role=leaf", "name=l1"]
        assert expr.nornir_filter is not None
        assert expr.display_text == "role=leaf AND name=l1"

    def test_from_cli_args_with_or_filter(self):
        """from_cli_args with OR filter should parse correctly."""
        expr = FilterExpression.from_cli_args(["role=leaf|spine"])
        assert expr.raw_filters == ["role=leaf|spine"]
        assert expr.nornir_filter is not None
        assert expr.display_text == "role=leaf|spine"


class TestOperationStatus:
    """Test OperationStatus enum."""

    def test_success_status(self):
        """SUCCESS status should be 'success'."""
        assert OperationStatus.SUCCESS == "success"
        assert OperationStatus.SUCCESS.value == "success"

    def test_failed_status(self):
        """FAILED status should be 'failed'."""
        assert OperationStatus.FAILED == "failed"
        assert OperationStatus.FAILED.value == "failed"

    def test_skipped_status(self):
        """SKIPPED status should be 'skipped'."""
        assert OperationStatus.SKIPPED == "skipped"
        assert OperationStatus.SKIPPED.value == "skipped"

    def test_status_is_string(self):
        """Status should be comparable to string."""
        assert OperationStatus.SUCCESS == "success"
        assert OperationStatus.SUCCESS == "success"


class TestDeviceResult:
    """Test DeviceResult model."""

    def test_valid_device_result(self):
        """Valid device result should be created successfully."""
        result = DeviceResult(
            hostname="spine1",
            status=OperationStatus.SUCCESS,
            message="Configuration rendered successfully",
        )
        assert result.hostname == "spine1"
        assert result.status == OperationStatus.SUCCESS
        assert result.message == "Configuration rendered successfully"
        assert result.diff is None

    def test_device_result_with_diff(self):
        """Device result with diff should store diff correctly."""
        diff_text = "+ interface Ethernet1\n- interface Ethernet2"
        result = DeviceResult(
            hostname="leaf1",
            status=OperationStatus.SUCCESS,
            message="Config pushed",
            diff=diff_text,
        )
        assert result.diff == diff_text

    def test_empty_hostname_raises_error(self):
        """Empty hostname should raise ValidationError."""
        with pytest.raises(ValidationError):
            DeviceResult(
                hostname="",
                status=OperationStatus.SUCCESS,
                message="Test",
            )

    def test_whitespace_hostname_raises_error(self):
        """Whitespace-only hostname should raise ValidationError."""
        with pytest.raises(ValidationError):
            DeviceResult(
                hostname="   ",
                status=OperationStatus.SUCCESS,
                message="Test",
            )

    def test_hostname_trimmed(self):
        """Hostname with whitespace should be trimmed."""
        result = DeviceResult(
            hostname="  spine1  ",
            status=OperationStatus.SUCCESS,
            message="Test",
        )
        assert result.hostname == "spine1"

    def test_missing_required_fields_raises_error(self):
        """Missing required fields should raise ValidationError."""
        with pytest.raises(ValidationError):
            DeviceResult(hostname="spine1")  # Missing status and message


class TestOperationResult:
    """Test OperationResult model."""

    def test_empty_operation_result(self):
        """Empty operation result should have zero counts."""
        result = OperationResult(operation="render", device_results=[])
        assert result.operation == "render"
        assert result.total_devices == 0
        assert result.success_count == 0
        assert result.failed_count == 0
        assert result.skipped_count == 0

    def test_operation_result_with_successes(self):
        """Operation result with successes should count correctly."""
        device_results = [
            DeviceResult(hostname="spine1", status=OperationStatus.SUCCESS, message="OK"),
            DeviceResult(hostname="spine2", status=OperationStatus.SUCCESS, message="OK"),
            DeviceResult(hostname="leaf1", status=OperationStatus.SUCCESS, message="OK"),
        ]
        result = OperationResult(operation="render", device_results=device_results)
        assert result.total_devices == 3
        assert result.success_count == 3
        assert result.failed_count == 0
        assert result.skipped_count == 0

    def test_operation_result_with_failures(self):
        """Operation result with failures should count correctly."""
        device_results = [
            DeviceResult(hostname="spine1", status=OperationStatus.SUCCESS, message="OK"),
            DeviceResult(hostname="spine2", status=OperationStatus.FAILED, message="Error"),
            DeviceResult(hostname="leaf1", status=OperationStatus.FAILED, message="Error"),
        ]
        result = OperationResult(operation="push", device_results=device_results)
        assert result.total_devices == 3
        assert result.success_count == 1
        assert result.failed_count == 2
        assert result.skipped_count == 0

    def test_operation_result_with_mixed_statuses(self):
        """Operation result with mixed statuses should count correctly."""
        device_results = [
            DeviceResult(hostname="spine1", status=OperationStatus.SUCCESS, message="OK"),
            DeviceResult(hostname="spine2", status=OperationStatus.FAILED, message="Error"),
            DeviceResult(hostname="leaf1", status=OperationStatus.SKIPPED, message="Skipped"),
            DeviceResult(hostname="leaf2", status=OperationStatus.SUCCESS, message="OK"),
        ]
        result = OperationResult(operation="render", device_results=device_results)
        assert result.total_devices == 4
        assert result.success_count == 2
        assert result.failed_count == 1
        assert result.skipped_count == 1

    def test_to_summary_dict(self):
        """to_summary_dict should return correct dictionary."""
        device_results = [
            DeviceResult(hostname="spine1", status=OperationStatus.SUCCESS, message="OK"),
            DeviceResult(hostname="spine2", status=OperationStatus.FAILED, message="Error"),
        ]
        result = OperationResult(operation="render", device_results=device_results)
        summary = result.to_summary_dict()

        assert summary["operation"] == "render"
        assert summary["total"] == 2
        assert summary["success"] == 1
        assert summary["failed"] == 1
        assert summary["skipped"] == 0

    def test_empty_operation_name_raises_error(self):
        """Empty operation name should raise ValidationError."""
        with pytest.raises(ValidationError):
            OperationResult(operation="", device_results=[])


class TestPathConfiguration:
    """Test PathConfiguration model."""

    def test_valid_path_configuration(self, tmp_path):
        """Valid path configuration should be created successfully."""
        # Create temporary directories
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "test.j2").touch()

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        config = PathConfiguration(
            templates_dir=templates_dir,
            output_dir=output_dir,
        )
        assert config.templates_dir == templates_dir
        assert config.output_dir == output_dir
        assert not config.is_templates_override
        assert not config.is_output_override

    def test_path_configuration_with_overrides(self, tmp_path):
        """Path configuration with override flags should store flags correctly."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "test.j2").touch()

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        config = PathConfiguration(
            templates_dir=templates_dir,
            output_dir=output_dir,
            is_templates_override=True,
            is_output_override=True,
        )
        assert config.is_templates_override
        assert config.is_output_override

    def test_nonexistent_templates_dir_raises_error(self, tmp_path):
        """Nonexistent templates directory should raise FileNotFoundError."""
        templates_dir = tmp_path / "nonexistent"
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with pytest.raises(FileNotFoundError, match="Templates directory not found"):
            PathConfiguration(
                templates_dir=templates_dir,
                output_dir=output_dir,
            )

    def test_templates_dir_not_directory_raises_error(self, tmp_path):
        """Templates path that is not a directory should raise ValueError."""
        templates_file = tmp_path / "templates.txt"
        templates_file.touch()

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with pytest.raises(ValueError, match="not a directory"):
            PathConfiguration(
                templates_dir=templates_file,
                output_dir=output_dir,
            )

    def test_templates_dir_without_j2_files_raises_error(self, tmp_path):
        """Templates directory without .j2 files should raise ValueError."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        # Create non-template file
        (templates_dir / "readme.txt").touch()

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with pytest.raises(ValueError, match="No Jinja2 templates"):
            PathConfiguration(
                templates_dir=templates_dir,
                output_dir=output_dir,
            )

    def test_output_dir_created_if_not_exists(self, tmp_path):
        """Output directory should be created if it doesn't exist."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "test.j2").touch()

        output_dir = tmp_path / "output"
        # Don't create output_dir

        PathConfiguration(
            templates_dir=templates_dir,
            output_dir=output_dir,
        )
        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_output_dir_not_directory_raises_error(self, tmp_path):
        """Output path that is not a directory should raise ValueError."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "test.j2").touch()

        output_file = tmp_path / "output.txt"
        output_file.touch()

        with pytest.raises(ValueError, match="not a directory"):
            PathConfiguration(
                templates_dir=templates_dir,
                output_dir=output_file,
            )
