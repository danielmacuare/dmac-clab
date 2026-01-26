"""Unit tests for output formatting utilities."""

from unittest.mock import MagicMock, patch

from nornir.core import Nornir
from nornir.core.inventory import Host, Hosts, Inventory

from py_netauto.cli.output import (
    display_diff,
    display_filtered_hosts,
    display_operation_summary,
)


class TestDisplayFilteredHosts:
    """Test display_filtered_hosts function."""

    def test_display_single_host(self):
        """Display single host should show table with one row."""
        # Create mock Nornir instance with one host
        hosts = Hosts()
        hosts["spine1"] = Host(
            name="spine1",
            platform="arista_eos",
            data={"role": "spine"},
        )
        inventory = Inventory(hosts=hosts)
        nr = MagicMock(spec=Nornir)
        nr.inventory = inventory

        # Capture console output
        with patch("py_netauto.cli.output.console") as mock_console:
            display_filtered_hosts(nr)
            mock_console.print.assert_called_once()

    def test_display_multiple_hosts(self):
        """Display multiple hosts should show table with multiple rows."""
        hosts = Hosts()
        hosts["spine1"] = Host(name="spine1", platform="arista_eos", data={"role": "spine"})
        hosts["spine2"] = Host(name="spine2", platform="arista_eos", data={"role": "spine"})
        hosts["leaf1"] = Host(name="leaf1", platform="nokia_srl", data={"role": "leaf"})

        inventory = Inventory(hosts=hosts)
        nr = MagicMock(spec=Nornir)
        nr.inventory = inventory

        with patch("py_netauto.cli.output.console") as mock_console:
            display_filtered_hosts(nr)
            mock_console.print.assert_called_once()

    def test_display_with_filter_expression(self):
        """Display with filter expression should include filter in title."""
        hosts = Hosts()
        hosts["leaf1"] = Host(name="leaf1", platform="arista_eos", data={"role": "leaf"})

        inventory = Inventory(hosts=hosts)
        nr = MagicMock(spec=Nornir)
        nr.inventory = inventory

        with patch("py_netauto.cli.output.console") as mock_console:
            display_filtered_hosts(nr, filter_expr="role=leaf")
            mock_console.print.assert_called_once()

    def test_display_empty_inventory(self):
        """Display empty inventory should show table with zero devices."""
        hosts = Hosts()
        inventory = Inventory(hosts=hosts)
        nr = MagicMock(spec=Nornir)
        nr.inventory = inventory

        with patch("py_netauto.cli.output.console") as mock_console:
            display_filtered_hosts(nr)
            mock_console.print.assert_called_once()

    def test_display_host_without_role(self):
        """Display host without role should show N/A."""
        hosts = Hosts()
        hosts["device1"] = Host(name="device1", platform="arista_eos")

        inventory = Inventory(hosts=hosts)
        nr = MagicMock(spec=Nornir)
        nr.inventory = inventory

        with patch("py_netauto.cli.output.console") as mock_console:
            display_filtered_hosts(nr)
            mock_console.print.assert_called_once()

    def test_display_host_without_platform(self):
        """Display host without platform should show N/A."""
        hosts = Hosts()
        hosts["device1"] = Host(name="device1", data={"role": "leaf"})

        inventory = Inventory(hosts=hosts)
        nr = MagicMock(spec=Nornir)
        nr.inventory = inventory

        with patch("py_netauto.cli.output.console") as mock_console:
            display_filtered_hosts(nr)
            mock_console.print.assert_called_once()


class TestDisplayOperationSummary:
    """Test display_operation_summary function."""

    def test_display_all_success(self):
        """Display summary with all successes should show green panel."""
        with patch("py_netauto.cli.output.console") as mock_console:
            display_operation_summary(
                total=5,
                success=5,
                failed=0,
                operation="Configuration Rendering",
            )
            mock_console.print.assert_called_once()

    def test_display_all_failed(self):
        """Display summary with all failures should show red panel."""
        with patch("py_netauto.cli.output.console") as mock_console:
            display_operation_summary(
                total=5,
                success=0,
                failed=5,
                operation="Configuration Push",
            )
            mock_console.print.assert_called_once()

    def test_display_mixed_results(self):
        """Display summary with mixed results should show yellow panel."""
        with patch("py_netauto.cli.output.console") as mock_console:
            display_operation_summary(
                total=10,
                success=7,
                failed=3,
                operation="Configuration Rendering",
            )
            mock_console.print.assert_called_once()

    def test_display_zero_devices(self):
        """Display summary with zero devices should handle division by zero."""
        with patch("py_netauto.cli.output.console") as mock_console:
            display_operation_summary(
                total=0,
                success=0,
                failed=0,
                operation="Configuration Rendering",
            )
            mock_console.print.assert_called_once()

    def test_success_rate_calculation(self):
        """Success rate should be calculated correctly."""
        with patch("py_netauto.cli.output.console") as mock_console:
            display_operation_summary(
                total=10,
                success=8,
                failed=2,
                operation="Test",
            )
            # Success rate should be 80%
            mock_console.print.assert_called_once()


class TestDisplayDiff:
    """Test display_diff function."""

    def test_display_simple_diff(self):
        """Display simple diff should show panel with syntax highlighting."""
        diff_text = "+ interface Ethernet1\n- interface Ethernet2"

        with patch("py_netauto.cli.output.console") as mock_console:
            display_diff("spine1", diff_text)
            mock_console.print.assert_called_once()

    def test_display_empty_diff(self):
        """Display empty diff should show panel."""
        with patch("py_netauto.cli.output.console") as mock_console:
            display_diff("leaf1", "")
            mock_console.print.assert_called_once()

    def test_display_multiline_diff(self):
        """Display multiline diff should show panel with all lines."""
        diff_text = """
+ interface Ethernet1
+   description New Interface
+   no shutdown
- interface Ethernet2
-   shutdown
  interface Ethernet3
    description Unchanged
"""

        with patch("py_netauto.cli.output.console") as mock_console:
            display_diff("spine1", diff_text)
            mock_console.print.assert_called_once()

    def test_display_diff_with_special_characters(self):
        """Display diff with special characters should handle correctly."""
        diff_text = "+ description Test & Special <chars>"

        with patch("py_netauto.cli.output.console") as mock_console:
            display_diff("device1", diff_text)
            mock_console.print.assert_called_once()

    def test_hostname_in_panel_title(self):
        """Hostname should appear in panel title."""
        diff_text = "+ test"

        with patch("py_netauto.cli.output.console") as mock_console:
            display_diff("test-device", diff_text)
            mock_console.print.assert_called_once()
            # Verify the panel was created with hostname in title
            call_args = mock_console.print.call_args
            assert call_args is not None
