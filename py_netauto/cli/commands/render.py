"""
Render command implementation.

This module implements the configuration rendering command that generates
device configurations from Jinja2 templates.

"""

from pathlib import Path

import typer
from nornir.core import Nornir
from nornir.core.task import AggregatedResult
from nornir_rich.functions import print_result
from rich.console import Console

from py_netauto.cli.models import DeviceResult, FilterExpression, OperationResult, OperationStatus
from py_netauto.cli.output import display_filtered_hosts, display_operation_summary
from py_netauto.cli.paths import PathManager
from py_netauto.nornir_tasks.render_config import render_configs
from py_netauto.utils.nornir_helpers import initialize_nornir

console = Console()


def _build_operation_result(result: AggregatedResult, output_path: Path) -> OperationResult:
    """
    Build operation result from Nornir aggregated result.

    Args:
        result: Nornir aggregated result from render_configs task.
        output_path: Path where configuration files were written.

    Returns:
        OperationResult with device-level results and statistics.

    """
    device_results = []
    for hostname, multi_result in result.items():
        if multi_result.failed:
            device_results.append(
                DeviceResult(
                    hostname=hostname,
                    status=OperationStatus.FAILED,
                    message=str(multi_result.exception) if multi_result.exception else "Unknown error",
                ),
            )
        else:
            device_results.append(
                DeviceResult(
                    hostname=hostname,
                    status=OperationStatus.SUCCESS,
                    message=f"Configuration rendered to {output_path}/{hostname}.cfg",
                ),
            )

    return OperationResult(
        operation="Configuration Rendering",
        device_results=device_results,
    )


def _apply_filters_and_display(nr: Nornir, filters: list[str] | None, verbose: bool) -> Nornir:  # noqa: FBT001
    """
    Apply filters to Nornir inventory and display filtered hosts.

    Args:
        nr: Nornir instance to filter.
        filters: List of filter strings from CLI.
        verbose: Whether to show verbose output.

    Returns:
        Filtered Nornir instance.

    """
    filter_expr = FilterExpression.from_cli_args(filters)

    if filter_expr.nornir_filter is not None:
        if verbose:
            console.print(f"[cyan]Applying filter: {filter_expr.display_text}[/cyan]")
        nr = nr.filter(filter_expr.nornir_filter)

    console.print()
    display_filtered_hosts(nr, filter_expr.display_text)
    console.print()

    return nr


def render_command(  # noqa: C901
    filters: list[str] | None = typer.Option(  # noqa: B008
        None,
        "--filter",
        "-f",
        help="Filter devices (e.g., role=leaf, name=spine1). Multiple filters are ANDed. Use | for OR (e.g., 'role=leaf|spine')",
    ),
    output_dir: Path | None = typer.Option(  # noqa: B008
        None,
        "--output-dir",
        "-o",
        help="Override default output directory for generated configurations",
    ),
    templates_dir: Path | None = typer.Option(  # noqa: B008
        None,
        "--templates-dir",
        "-t",
        help="Override default templates directory for Jinja2 templates",
    ),
    verbose: bool = typer.Option(  # noqa: FBT001
        False,
        "--verbose",
        "-v",
        help="Enable verbose output for debugging",
    ),
) -> None:
    """
    Render device configurations from Jinja2 templates.

    This command generates configuration files for network devices by rendering
    Jinja2 templates with device-specific data from the Nornir inventory. The
    rendered configurations are saved to the output directory.

    Args:
        filters: List of filter strings to select specific devices. Multiple filters
            are combined with AND logic. Use pipe (|) within a filter for OR logic.
            Examples: ["role=leaf"], ["role=leaf", "name=l1|l2"]
        output_dir: Optional path to override the default output directory where
            generated configuration files will be saved.
        templates_dir: Optional path to override the default templates directory
            where Jinja2 template files are located.
        verbose: Enable verbose output for detailed debugging information.

    Raises:
        typer.Exit: Exits with code 1 on error (invalid paths, missing templates, etc.)

    Example:
        Render all devices:

        ```bash
        py-netauto render
        ```

        Render only leaf devices:

        ```bash
        py-netauto render --filter role=leaf
        ```

        Render with custom paths:

        ```bash
        py-netauto render --output-dir ./custom-output --templates-dir ./custom-templates
        ```

        Complex filtering:

        ```bash
        py-netauto render --filter role=leaf --filter "name=l1|l2"
        ```

    """
    try:
        # Initialize and validate paths
        if verbose:
            console.print("[cyan]Initializing path manager...[/cyan]")

        path_manager = PathManager(
            templates_override=templates_dir,
            output_override=output_dir,
        )
        path_manager.validate_templates_dir()
        path_manager.ensure_output_dir()

        # Initialize Nornir
        if verbose:
            console.print("[cyan]Initializing Nornir...[/cyan]")
        nr = initialize_nornir()

        # Apply filters and display hosts
        nr = _apply_filters_and_display(nr, filters, verbose)

        # Check if any devices match
        if len(nr.inventory.hosts) == 0:
            console.print("[yellow]No devices match the filter criteria. Nothing to render.[/yellow]")
            raise typer.Exit(code=0)  # noqa: TRY301

        # Execute render task
        if verbose:
            console.print("[cyan]Rendering configurations...[/cyan]")

        result = nr.run(
            task=render_configs,
            templates_path=path_manager.get_templates_path(),
            output_path=path_manager.get_output_path(),
        )

        # Display results
        console.print()
        print_result(result)
        console.print()

        # Build and display summary
        operation_result = _build_operation_result(result, path_manager.get_output_path())
        display_operation_summary(
            total=operation_result.total_devices,
            success=operation_result.success_count,
            failed=operation_result.failed_count,
            operation=operation_result.operation,
        )

        # Exit with error if any failures
        if operation_result.failed_count > 0:
            raise typer.Exit(code=1)  # noqa: TRY301

    except typer.Exit:
        # Re-raise typer.Exit to allow proper exit code handling
        raise

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("\n[yellow]Examples of valid usage:[/yellow]")
        console.print("  py-netauto render")
        console.print("  py-netauto render --filter role=leaf")
        console.print("  py-netauto render --filter 'role=leaf|spine'")
        console.print("  py-netauto render --filter role=leaf --filter name=l1")
        raise typer.Exit(code=1) from e

    except FileNotFoundError as e:
        console.print(f"[red]File not found:[/red] {e}")
        console.print("\n[yellow]Tip:[/yellow] Use --templates-dir to specify a custom templates directory")
        raise typer.Exit(code=1) from e

    except PermissionError as e:
        console.print(f"[red]Permission error:[/red] {e}")
        console.print(
            "\n[yellow]Tip:[/yellow] Check directory permissions or use --output-dir to specify a writable directory",
        )
        raise typer.Exit(code=1) from e

    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(code=1) from e
