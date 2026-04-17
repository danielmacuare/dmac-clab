"""
Push command implementation.

This module implements configuration push operations with dry-run and commit modes,
allowing safe validation before deploying changes to network devices.

"""

from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm

from py_netauto.cli.models import DeviceResult, FilterExpression, OperationResult, OperationStatus
from py_netauto.cli.output import display_diff, display_filtered_hosts, display_operation_summary
from py_netauto.cli.paths import PathManager
from py_netauto.nornir_tasks.scrapli_config_device import config_device_commit, config_device_dry_run
from py_netauto.utils.nornir_helpers import initialize_nornir

console = Console()


def _confirm_operation(is_commit_mode: bool, device_count: int, force: bool) -> bool:  # noqa: FBT001
    """
    Display operation mode warning and return True if the operation should proceed.

    Args:
        is_commit_mode: Whether the operation will commit changes.
        device_count: Number of devices that will be affected.
        force: Whether to skip the confirmation prompt.

    Returns:
        True if the operation should proceed, False if cancelled.

    """
    if is_commit_mode:
        console.print("[bold red]⚠ WARNING:[/bold red] This will COMMIT configuration changes to devices!")
        console.print(f"[yellow]Devices affected:[/yellow] {device_count}")
        console.print()
        if not force and not Confirm.ask("[yellow]Do you want to continue?[/yellow]"):
            console.print("[yellow]Operation cancelled[/yellow]")
            return False
    else:
        console.print("[cyan]INFO: Running in DRY-RUN mode[/cyan] - No changes will be committed")
        console.print()
    return True


def push_command(  # noqa: C901, PLR0913
    filters: list[str] | None = typer.Option(None, "--filter", "-f", help="Filter devices (e.g., role=leaf)"),  # noqa: B008
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Explicitly enable dry-run mode"),  # noqa: FBT001
    commit: bool = typer.Option(False, "--commit", "-c", help="Commit configuration changes to devices"),  # noqa: FBT001
    output_dir: Path | None = typer.Option(None, "--output-dir", "-o", help="Override output directory path"),  # noqa: B008
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompts"),  # noqa: FBT001
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),  # noqa: FBT001
) -> None:
    """
    Push configurations to network devices (dry-run by default).

    This command loads configuration files to network devices and either shows
    the diff without committing (dry-run mode) or commits the changes (commit mode).

    Examples:
        # Dry-run for all devices (default)
        py-netauto push

        # Dry-run for specific devices
        py-netauto push --filter role=leaf

        # Commit changes to specific devices
        py-netauto push --commit --filter "name=spine1|spine2"

        # Commit with custom config directory
        py-netauto push --commit --output-dir custom/configs --force

    """
    try:
        # Validate that dry_run and commit are mutually exclusive
        if dry_run and commit:
            console.print("[red]Error:[/red] Cannot use both --dry-run and --commit flags")
            console.print("[yellow]Tip:[/yellow] Use --commit to apply changes, or omit both for dry-run (default)")
            raise typer.Exit(code=1)  # noqa: TRY301

        # Determine operation mode (default to dry-run if neither flag is set)
        is_commit_mode = commit and not dry_run

        # Initialize PathManager with overrides
        try:
            path_manager = PathManager(output_override=output_dir)
            path_manager.ensure_output_dir()
        except (FileNotFoundError, PermissionError, ValueError) as e:
            console.print(f"[red]Path error:[/red] {e}")
            raise typer.Exit(code=1) from e

        # Validate configuration files exist in output directory
        config_files = list(path_manager.get_output_path().glob("*.cfg"))
        if not config_files:
            console.print(
                f"[red]Error:[/red] No configuration files (*.cfg) found in output directory: "
                f"{path_manager.get_output_path()}",
            )
            console.print("[yellow]Tip:[/yellow] Run 'py-netauto render' first to generate configuration files")
            raise typer.Exit(code=1)  # noqa: TRY301

        # Initialize Nornir
        if verbose:
            console.print("[dim]Initializing Nornir...[/dim]")

        nr = initialize_nornir()

        # Parse and apply filters
        filter_expr = FilterExpression.from_cli_args(filters)
        if filter_expr.nornir_filter:
            nr = nr.filter(filter_expr.nornir_filter)

        # Display filtered device list
        console.print()
        display_filtered_hosts(nr, filter_expr.display_text)
        console.print()

        # Check if any devices match the filter
        if not nr.inventory.hosts:
            console.print("[yellow]Warning:[/yellow] No devices match the specified filter")
            raise typer.Exit(code=0)  # noqa: TRY301

        if not _confirm_operation(is_commit_mode, len(nr.inventory.hosts), force):
            raise typer.Exit(code=0)  # noqa: TRY301

        # Execute operation based on mode
        if is_commit_mode:
            _execute_commit(nr, path_manager, verbose)
        else:
            _execute_dry_run(nr, path_manager, verbose)

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(code=1) from e


def _execute_dry_run(nr, path_manager: PathManager, verbose: bool) -> None:  # noqa: FBT001
    """
    Execute dry-run operation for filtered devices.

    Args:
        nr: Filtered Nornir instance.
        path_manager: PathManager instance with output directory.
        verbose: Whether to show verbose output.

    """
    if verbose:
        console.print("[dim]Executing dry-run operation...[/dim]")

    # Execute config_device_dry_run task for filtered devices
    result = nr.run(
        task=config_device_dry_run,
        config_dir=path_manager.get_output_path(),
        name="Configuration Dry-Run",
    )

    # Collect results
    operation_result = OperationResult(operation="Push (Dry-Run)", device_results=[])

    console.print()
    console.print("[bold cyan]Configuration Diffs:[/bold cyan]")
    console.print()

    for hostname, multi_result in result.items():
        if multi_result.failed:
            # Handle failure - surface per-subtask exceptions for actionable output
            console.print(f"[red]✗ {hostname}:[/red] Dry-run failed")
            for task_result in multi_result:
                if task_result.exception is not None:
                    console.print(f"  [red][{task_result.name}][/red] {task_result.exception}")

            subtask_errors = [f"[{r.name}] {r.exception}" for r in multi_result if r.exception is not None]
            operation_result.device_results.append(
                DeviceResult(
                    hostname=hostname,
                    status=OperationStatus.FAILED,
                    message=f"Dry-run failed: {'; '.join(subtask_errors) or 'Unknown error'}",
                ),
            )
        else:
            # Display diff for successful devices
            diff = multi_result[0].result if multi_result else ""

            if diff and diff.strip():
                display_diff(hostname, diff)
                operation_result.device_results.append(
                    DeviceResult(
                        hostname=hostname,
                        status=OperationStatus.SUCCESS,
                        message="Diff retrieved successfully",
                        diff=diff,
                    ),
                )
            else:
                console.print(f"[yellow]⚠ {hostname}:[/yellow] No configuration changes detected")
                operation_result.device_results.append(
                    DeviceResult(
                        hostname=hostname,
                        status=OperationStatus.SKIPPED,
                        message="No configuration changes",
                    ),
                )

    # Display operation summary
    console.print()
    display_operation_summary(
        total=operation_result.total_devices,
        success=operation_result.success_count,
        failed=operation_result.failed_count,
        operation="Push (Dry-Run)",
    )

    # Exit with error code if any devices failed
    if operation_result.failed_count > 0:
        raise typer.Exit(code=1)


def _execute_commit(nr, path_manager: PathManager, verbose: bool) -> None:  # noqa: FBT001
    """
    Execute commit operation for filtered devices.

    Args:
        nr: Filtered Nornir instance.
        path_manager: PathManager instance with output directory.
        verbose: Whether to show verbose output.

    """
    if verbose:
        console.print("[dim]Executing commit operation...[/dim]")

    # Execute config_device_commit task for filtered devices
    result = nr.run(
        task=config_device_commit,
        config_dir=path_manager.get_output_path(),
        name="Configuration Commit",
    )

    # Collect results
    operation_result = OperationResult(operation="Push (Commit)", device_results=[])

    console.print()
    console.print("[bold green]Configuration Results:[/bold green]")
    console.print()

    for hostname, multi_result in result.items():
        if multi_result.failed:
            # Handle failure - surface per-subtask exceptions for actionable output
            console.print(f"[red]✗ {hostname}:[/red] Configuration commit failed")
            for task_result in multi_result:
                if task_result.exception is not None:
                    console.print(f"  [red][{task_result.name}][/red] {task_result.exception}")

            subtask_errors = [f"[{r.name}] {r.exception}" for r in multi_result if r.exception is not None]
            operation_result.device_results.append(
                DeviceResult(
                    hostname=hostname,
                    status=OperationStatus.FAILED,
                    message=f"Commit failed: {'; '.join(subtask_errors) or 'Unknown error'}",
                ),
            )
        else:
            # Display diff and success message
            diff = multi_result[0].result if multi_result else ""

            if diff and diff.strip():
                display_diff(hostname, diff)

            console.print(f"[green]✓ {hostname}:[/green] Configuration committed successfully")

            operation_result.device_results.append(
                DeviceResult(
                    hostname=hostname,
                    status=OperationStatus.SUCCESS,
                    message="Configuration committed successfully",
                    diff=diff,
                ),
            )

    # Display operation summary
    console.print()
    display_operation_summary(
        total=operation_result.total_devices,
        success=operation_result.success_count,
        failed=operation_result.failed_count,
        operation="Push (Commit)",
    )

    # Exit with error code if any devices failed
    if operation_result.failed_count > 0:
        raise typer.Exit(code=1)
