"""
Output formatting utilities for CLI operations.

This module provides utilities for formatting CLI output with rich formatting,
including device lists, operation summaries, and configuration diffs.

"""

from nornir.core import Nornir
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

console = Console()


def display_filtered_hosts(nr: Nornir, filter_expr: str | None = None) -> None:
    """
    Display table of hosts that match the current filter.

    Shows a formatted table with hostname, role, and platform for all devices
    in the filtered Nornir inventory. The table title includes the device count.

    Args:
        nr: Nornir instance with filtered inventory.
        filter_expr: Human-readable filter expression string for display.
            Defaults to None.

    Example:
        Basic usage with filtered inventory:

        ```python
        nr = initialize_nornir()
        nr = nr.filter(F(role="leaf"))
        display_filtered_hosts(nr, "role=leaf")
        ```

    """
    hosts = nr.inventory.hosts
    device_count = len(hosts)

    # Create table with title showing device count
    title = f"Filtered Devices ({device_count} device{'s' if device_count != 1 else ''})"
    if filter_expr:
        title = f"{title} - Filter: {filter_expr}"

    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Hostname", style="cyan", no_wrap=True)
    table.add_column("Role", style="yellow")
    table.add_column("Platform", style="green")

    # Add rows for each host
    for hostname, host in hosts.items():
        role = host.get("role", "N/A")
        platform = host.platform or "N/A"
        table.add_row(hostname, role, platform)

    console.print(table)


def display_operation_summary(
    total: int,
    success: int,
    failed: int,
    operation: str,
) -> None:
    """
    Display summary panel for operation results.

    Shows a color-coded panel with operation statistics including total devices
    processed, successful operations, and failures. Success counts are shown in
    green, failures in red.

    Args:
        total: Total number of devices processed.
        success: Number of successful operations.
        failed: Number of failed operations.
        operation: Name of the operation (e.g., "render", "push").

    Example:
        Display summary after rendering configs:

        ```python
        display_operation_summary(total=10, success=8, failed=2, operation="Configuration Rendering")
        ```

    """
    # Calculate success rate
    success_rate = (success / total * 100) if total > 0 else 0

    # Build summary text with color coding
    summary_lines = [
        f"Operation: {operation}",
        f"Total Devices: {total}",
        f"[green]Successful: {success}[/green]",
        f"[red]Failed: {failed}[/red]",
        f"Success Rate: {success_rate:.1f}%",
    ]

    summary_text = "\n".join(summary_lines)

    # Choose panel style based on results
    if failed == 0:
        panel_style = "green"
        title = "✓ Operation Complete"
    elif success == 0:
        panel_style = "red"
        title = "✗ Operation Failed"
    else:
        panel_style = "yellow"
        title = "⚠ Operation Complete with Errors"

    panel = Panel(
        summary_text,
        title=title,
        border_style=panel_style,
        expand=False,
    )

    console.print(panel)


def display_diff(hostname: str, diff: str) -> None:
    """
    Display configuration diff for a device.

    Shows the configuration diff with syntax highlighting using the diff lexer.
    The diff is displayed in a panel with the device hostname as the title.

    Args:
        hostname: Name of the device.
        diff: Configuration diff text to display.

    Example:
        Display diff for a device:

        ```python
        diff_text = '''
        + interface Ethernet1
        +   description New Interface
        - interface Ethernet2
        -   shutdown
        '''
        display_diff("spine1", diff_text)
        ```

    """
    # Create syntax-highlighted diff
    syntax = Syntax(
        diff,
        "diff",
        theme="monokai",
        line_numbers=False,
        word_wrap=True,
    )

    # Display in panel with hostname as title
    panel = Panel(
        syntax,
        title=f"Configuration Diff: {hostname}",
        border_style="blue",
        expand=True,
    )

    console.print(panel)
