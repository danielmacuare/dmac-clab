"""
Unit tests for the render command.

This module tests the render command implementation including path management,
filter application, and error handling.

"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import typer

from py_netauto.cli.commands.render import _apply_filters_and_display, _build_operation_result, render_command
from py_netauto.cli.models import OperationStatus


class TestRenderCommandHelpers:
    """Test helper functions for render command."""

    def test_build_operation_result_success(self):
        """Test building operation result with successful renders."""
        # Create mock result
        mock_result = {
            "device1": MagicMock(failed=False, exception=None),
            "device2": MagicMock(failed=False, exception=None),
        }

        output_path = Path("/tmp/output")  # noqa: S108

        result = _build_operation_result(mock_result, output_path)

        assert result.operation == "Configuration Rendering"
        assert result.total_devices == 2
        assert result.success_count == 2
        assert result.failed_count == 0
        assert all(dr.status == OperationStatus.SUCCESS for dr in result.device_results)

    def test_build_operation_result_with_failures(self):
        """Test building operation result with some failures."""
        # Create mock result with one failure
        mock_result = {
            "device1": MagicMock(failed=False, exception=None),
            "device2": MagicMock(failed=True, exception=ValueError("Template error")),
        }

        output_path = Path("/tmp/output")  # noqa: S108

        result = _build_operation_result(mock_result, output_path)

        assert result.total_devices == 2
        assert result.success_count == 1
        assert result.failed_count == 1

    @patch("py_netauto.cli.commands.render.FilterExpression")
    @patch("py_netauto.cli.commands.render.display_filtered_hosts")
    def test_apply_filters_and_display_no_filters(self, mock_display, mock_filter_expr):
        """Test applying filters when no filters provided."""
        mock_nr = MagicMock()
        mock_filter_expr.from_cli_args.return_value.nornir_filter = None
        mock_filter_expr.from_cli_args.return_value.display_text = "No filters applied"

        filtered_nr = _apply_filters_and_display(mock_nr, None, False)

        assert filtered_nr == mock_nr
        mock_display.assert_called_once()

    @patch("py_netauto.cli.commands.render.FilterExpression")
    @patch("py_netauto.cli.commands.render.display_filtered_hosts")
    def test_apply_filters_and_display_with_filters(self, mock_display, mock_filter_expr):
        """Test applying filters when filters provided."""
        mock_nr = MagicMock()
        mock_filter = MagicMock()
        mock_filter_expr.from_cli_args.return_value.nornir_filter = mock_filter
        mock_filter_expr.from_cli_args.return_value.display_text = "role=leaf"

        filtered_nr = _apply_filters_and_display(mock_nr, ["role=leaf"], False)

        mock_nr.filter.assert_called_once_with(mock_filter)
        mock_display.assert_called_once()
        assert filtered_nr == mock_nr.filter.return_value


class TestRenderCommand:
    """Test the main render command function."""

    @patch("py_netauto.cli.commands.render.initialize_nornir")
    @patch("py_netauto.cli.commands.render.PathManager")
    @patch("py_netauto.cli.commands.render._apply_filters_and_display")
    @patch("py_netauto.cli.commands.render.print_result")
    @patch("py_netauto.cli.commands.render.display_operation_summary")
    def test_render_command_success(
        self,
        mock_summary,
        _mock_print_result,  # noqa: ARG002
        mock_apply_filters,
        mock_path_manager,
        mock_init_nornir,
    ):
        """Test successful render command execution."""
        # Setup mocks
        mock_nr = MagicMock()
        mock_nr.inventory.hosts = {"device1": MagicMock()}
        mock_nr.run.return_value = {
            "device1": MagicMock(failed=False, exception=None),
        }

        mock_init_nornir.return_value = mock_nr
        mock_apply_filters.return_value = mock_nr

        mock_pm = MagicMock()
        mock_pm.get_templates_path.return_value = Path("/tmp/templates")  # noqa: S108
        mock_pm.get_output_path.return_value = Path("/tmp/output")  # noqa: S108
        mock_path_manager.return_value = mock_pm

        # Execute command
        render_command(filters=None, output_dir=None, templates_dir=None, verbose=False)

        # Verify calls
        mock_path_manager.assert_called_once()
        mock_pm.validate_templates_dir.assert_called_once()
        mock_pm.ensure_output_dir.assert_called_once()
        mock_init_nornir.assert_called_once()
        mock_nr.run.assert_called_once()
        mock_summary.assert_called_once()

    @patch("py_netauto.cli.commands.render.initialize_nornir")
    @patch("py_netauto.cli.commands.render.PathManager")
    @patch("py_netauto.cli.commands.render._apply_filters_and_display")
    def test_render_command_no_matching_devices(
        self,
        mock_apply_filters,
        mock_path_manager,
        mock_init_nornir,
    ):
        """Test render command when no devices match filter."""
        # Setup mocks
        mock_nr = MagicMock()
        mock_nr.inventory.hosts = {}  # No devices

        mock_init_nornir.return_value = mock_nr
        mock_apply_filters.return_value = mock_nr

        mock_pm = MagicMock()
        mock_path_manager.return_value = mock_pm

        # Execute command - should exit with code 0
        with pytest.raises(typer.Exit) as exc_info:
            render_command(filters=["role=nonexistent"], output_dir=None, templates_dir=None, verbose=False)

        assert exc_info.value.exit_code == 0

    @patch("py_netauto.cli.commands.render.PathManager")
    def test_render_command_invalid_templates_dir(self, mock_path_manager):
        """Test render command with invalid templates directory."""
        # Setup mock to raise FileNotFoundError
        mock_pm = MagicMock()
        mock_pm.validate_templates_dir.side_effect = FileNotFoundError("Templates not found")
        mock_path_manager.return_value = mock_pm

        # Execute command - should exit with code 1
        with pytest.raises(typer.Exit) as exc_info:
            render_command(filters=None, output_dir=None, templates_dir=Path("/invalid"), verbose=False)

        assert exc_info.value.exit_code == 1

    @patch("py_netauto.cli.commands.render.PathManager")
    def test_render_command_permission_error(self, mock_path_manager):
        """Test render command with permission error on output directory."""
        # Setup mock to raise PermissionError
        mock_pm = MagicMock()
        mock_pm.validate_templates_dir.return_value = None
        mock_pm.ensure_output_dir.side_effect = PermissionError("Cannot write to directory")
        mock_path_manager.return_value = mock_pm

        # Execute command - should exit with code 1
        with pytest.raises(typer.Exit) as exc_info:
            render_command(filters=None, output_dir=Path("/readonly"), templates_dir=None, verbose=False)

        assert exc_info.value.exit_code == 1
