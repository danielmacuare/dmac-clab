"""
Session management command implementation.

This module implements commands for managing configuration sessions on devices,
including detecting and aborting stale sessions.

"""

import typer
from nornir.core import Nornir
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from py_netauto.cli.models import DeviceResult, FilterExpression, OperationResult, OperationStatus
from py_netauto.cli.output import display_filtered_hosts, display_operation_summary
from py_netauto.nornir_tasks.scrapli_config_device import abort_all_sessions, abort_specific_session, list_all_sessions
from py_netauto.utils.nornir_helpers import initialize_nornir

console = Console()


def sessions_list_command(
    filters: list[str] | None = typer.Option(None, "--filter", "-f", help="Filter devices (e.g., role=leaf)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """
    List all configuration sessions on devices.

    This command queries devices for active configuration sessions and displays
    the session information in a formatted table.

    Examples:
        # List sessions on all devices
        py-netauto sessions list

        # List sessions on specific devices
        py-netauto sessions list --filter role=leaf

        # List with verbose output
        py-netauto sessions list --filter "name=spine1|spine2" --verbose

    """
    try:
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
            raise typer.Exit(code=0)

        # Execute list_all_sessions task
        if verbose:
            console.print("[dim]Querying configuration sessions...[/dim]")

        result = nr.run(
            task=list_all_sessions,
            name="List Configuration Sessions",
        )

        # Display results
        console.print()
        console.print("[bold cyan]Configuration Sessions:[/bold cyan]")
        console.print()

        total_sessions = 0
        devices_with_sessions = 0

        for hostname, multi_result in result.items():
            if multi_result.failed:
                # Handle failure
                error_msg = str(multi_result.exception) if multi_result.exception else "Unknown error"
                console.print(f"[red]✗ {hostname}:[/red] Failed to query sessions - {error_msg}")
            else:
                # Display session information
                sessions_info = multi_result[0].result
                session_count = sessions_info["count"]
                sessions = sessions_info["sessions"]

                if session_count > 0:
                    devices_with_sessions += 1
                    total_sessions += session_count
                    console.print(f"[yellow]📋 {hostname}:[/yellow] {session_count} active session(s)")

                    for session in sessions:
                        console.print(f"   • {session['name']} - {session['status']}")
                        if verbose:
                            console.print(f"     {session['details']}")
                else:
                    console.print(f"[green]✓ {hostname}:[/green] No active sessions")

                if verbose and sessions_info.get("raw_output"):
                    console.print(f"\n[dim]Raw output for {hostname}:[/dim]")
                    console.print(f"[dim]{sessions_info['raw_output']}[/dim]\n")

        # Display summary
        console.print()
        if total_sessions > 0:
            console.print(
                f"[bold yellow]Summary:[/bold yellow] Found {total_sessions} session(s) "
                f"across {devices_with_sessions} device(s)"
            )
        else:
            console.print("[bold green]Summary:[/bold green] No active sessions found on any device")

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(code=1) from e


def sessions_abort_command(
    filters: list[str] | None = typer.Option(None, "--filter", "-f", help="Filter devices (e.g., role=leaf)"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompts"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """
    Interactively abort configuration sessions on devices.

    This command first checks for active sessions, displays them, and offers
    options to abort all sessions or select specific ones. Useful for cleaning
    up stale sessions left by failed operations.

    Examples:
        # Interactive abort (shows sessions and prompts for choice)
        py-netauto sessions abort

        # Abort sessions on specific devices
        py-netauto sessions abort --filter role=leaf

        # Abort all sessions without confirmation
        py-netauto sessions abort --force

    """
    try:
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
            raise typer.Exit(code=0)

        # Step 1: Check for active sessions
        if verbose:
            console.print("[dim]Checking for active configuration sessions...[/dim]")

        result = nr.run(
            task=list_all_sessions,
            name="List Configuration Sessions",
        )

        # Collect all sessions across devices
        all_sessions = []
        devices_with_sessions = {}

        for hostname, multi_result in result.items():
            if not multi_result.failed:
                sessions_info = multi_result[0].result
                if sessions_info["count"] > 0:
                    devices_with_sessions[hostname] = sessions_info["sessions"]
                    for session in sessions_info["sessions"]:
                        all_sessions.append(
                            {
                                "hostname": hostname,
                                "session_name": session["name"],
                                "status": session["status"],
                                "details": session["details"],
                            }
                        )

        # Step 2: If no sessions, exit
        if not all_sessions:
            console.print()
            console.print("[green]✓ No active configuration sessions found on any device[/green]")
            raise typer.Exit(code=0)

        # Step 3: Display active sessions
        console.print()
        console.print("[bold yellow]Active Configuration Sessions:[/bold yellow]")
        console.print()

        for hostname, sessions in devices_with_sessions.items():
            console.print(f"[yellow]📋 {hostname}:[/yellow] {len(sessions)} session(s)")
            for session in sessions:
                console.print(f"   • {session['name']} - {session['status']}")

        console.print()
        console.print(
            f"[bold]Total:[/bold] {len(all_sessions)} session(s) across {len(devices_with_sessions)} device(s)"
        )
        console.print()

        # Step 4: Offer choices (unless --force flag)
        if force:
            # Force mode: abort all sessions without prompting
            _abort_all_sessions_on_devices(nr, verbose)
        else:
            # Interactive mode: show menu
            console.print("[bold cyan]What would you like to do?[/bold cyan]")
            console.print("  [1] Abort ALL sessions on all devices")
            console.print("  [2] Select specific sessions to abort")
            console.print("  [3] Cancel")
            console.print()

            choice = Prompt.ask(
                "[cyan]Enter your choice[/cyan]",
                choices=["1", "2", "3"],
                default="3",
            )

            if choice == "1":
                # Abort all sessions
                console.print()
                console.print("[bold yellow]⚠ WARNING:[/bold yellow] This will ABORT all sessions on all devices!")
                if Confirm.ask("[yellow]Are you sure?[/yellow]"):
                    _abort_all_sessions_on_devices(nr, verbose)
                else:
                    console.print("[yellow]Operation cancelled[/yellow]")
                    raise typer.Exit(code=0)

            elif choice == "2":
                # Select specific sessions
                _abort_specific_sessions_interactive(nr, all_sessions, verbose)

            else:
                # Cancel
                console.print("[yellow]Operation cancelled[/yellow]")
                raise typer.Exit(code=0)

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(code=1) from e


def _abort_all_sessions_on_devices(nr: Nornir, verbose: bool) -> None:
    """
    Abort all sessions on all devices in the Nornir inventory.

    Args:
        nr: Nornir instance with filtered devices.
        verbose: Enable verbose output.

    """
    if verbose:
        console.print("[dim]Aborting all configuration sessions...[/dim]")

    result = nr.run(
        task=abort_all_sessions,
        name="Abort Configuration Sessions",
    )

    # Collect results
    operation_result = OperationResult(operation="Session Abort", device_results=[])

    console.print()
    console.print("[bold cyan]Session Abort Results:[/bold cyan]")
    console.print()

    for hostname, multi_result in result.items():
        if multi_result.failed:
            error_msg = str(multi_result.exception) if multi_result.exception else "Unknown error"
            console.print(f"[red]✗ {hostname}:[/red] Session abort failed - {error_msg}")

            operation_result.device_results.append(
                DeviceResult(
                    hostname=hostname,
                    status=OperationStatus.FAILED,
                    message=f"Session abort failed: {error_msg}",
                ),
            )
        else:
            # Get the abort count from the result
            abort_info = multi_result[0].result
            aborted_count = abort_info.get("aborted_count", 0)

            if aborted_count > 0:
                console.print(f"[green]✓ {hostname}:[/green] Aborted {aborted_count} session(s)")
                operation_result.device_results.append(
                    DeviceResult(
                        hostname=hostname,
                        status=OperationStatus.SUCCESS,
                        message=f"Aborted {aborted_count} session(s)",
                    ),
                )
            else:
                console.print(f"[dim]○ {hostname}:[/dim] No sessions to abort")
                # Don't add to operation_result for devices with no sessions

    # Display operation summary (only count devices that had sessions)
    console.print()
    if operation_result.total_devices > 0:
        display_operation_summary(
            total=operation_result.total_devices,
            success=operation_result.success_count,
            failed=operation_result.failed_count,
            operation="Session Abort",
        )
    else:
        console.print("[dim]No sessions were aborted on any device[/dim]")

    # Exit with error code if any devices failed
    if operation_result.failed_count > 0:
        raise typer.Exit(code=1)


def _abort_specific_sessions_interactive(nr: Nornir, all_sessions: list[dict], verbose: bool) -> None:
    """
    Interactively select and abort specific sessions.

    Args:
        nr: Nornir instance with filtered devices.
        all_sessions: List of all session dictionaries with hostname, session_name, status, details.
        verbose: Enable verbose output.

    """
    console.print()
    console.print("[bold cyan]Select sessions to abort:[/bold cyan]")
    console.print()

    # Display numbered list of sessions
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Device", style="yellow")
    table.add_column("Session Name", style="cyan")
    table.add_column("Status", style="magenta")

    for idx, session in enumerate(all_sessions, start=1):
        table.add_row(
            str(idx),
            session["hostname"],
            session["session_name"],
            session["status"],
        )

    console.print(table)
    console.print()

    # Prompt for session numbers
    console.print("[dim]Enter session numbers separated by commas (e.g., 1,3,5) or 'all' for all sessions[/dim]")
    selection = Prompt.ask("[cyan]Sessions to abort[/cyan]", default="")

    if not selection or selection.lower() == "cancel":
        console.print("[yellow]Operation cancelled[/yellow]")
        raise typer.Exit(code=0)

    # Parse selection
    if selection.lower() == "all":
        selected_indices = list(range(len(all_sessions)))
    else:
        try:
            selected_indices = [int(x.strip()) - 1 for x in selection.split(",")]
            # Validate indices
            if any(idx < 0 or idx >= len(all_sessions) for idx in selected_indices):
                console.print("[red]Error:[/red] Invalid session number(s)")
                raise typer.Exit(code=1)
        except ValueError:
            console.print("[red]Error:[/red] Invalid input format")
            raise typer.Exit(code=1)

    # Get selected sessions
    selected_sessions = [all_sessions[idx] for idx in selected_indices]

    # Confirm
    console.print()
    console.print(f"[bold yellow]⚠ WARNING:[/bold yellow] About to abort {len(selected_sessions)} session(s)")
    for session in selected_sessions:
        console.print(f"   • {session['hostname']}: {session['session_name']}")
    console.print()

    if not Confirm.ask("[yellow]Proceed with abort?[/yellow]"):
        console.print("[yellow]Operation cancelled[/yellow]")
        raise typer.Exit(code=0)

    # Abort selected sessions
    if verbose:
        console.print("[dim]Aborting selected sessions...[/dim]")

    console.print()
    console.print("[bold cyan]Session Abort Results:[/bold cyan]")
    console.print()

    operation_result = OperationResult(operation="Session Abort", device_results=[])

    for session in selected_sessions:
        hostname = session["hostname"]
        session_name = session["session_name"]

        try:
            # Filter to specific host
            host_nr = nr.filter(name=hostname)

            # Abort the specific session
            result = host_nr.run(
                task=abort_specific_session,
                session_name=session_name,
                name=f"Abort Session {session_name}",
            )

            # Check result
            if result[hostname].failed:
                error_msg = str(result[hostname].exception) if result[hostname].exception else "Unknown error"
                console.print(f"[red]✗ {hostname} ({session_name}):[/red] Failed - {error_msg}")

                operation_result.device_results.append(
                    DeviceResult(
                        hostname=hostname,
                        status=OperationStatus.FAILED,
                        message=f"Session {session_name} abort failed: {error_msg}",
                    ),
                )
            else:
                console.print(f"[green]✓ {hostname} ({session_name}):[/green] Aborted successfully")

                operation_result.device_results.append(
                    DeviceResult(
                        hostname=hostname,
                        status=OperationStatus.SUCCESS,
                        message=f"Session {session_name} aborted successfully",
                    ),
                )

        except Exception as e:
            console.print(f"[red]✗ {hostname} ({session_name}):[/red] Exception - {e}")

            operation_result.device_results.append(
                DeviceResult(
                    hostname=hostname,
                    status=OperationStatus.FAILED,
                    message=f"Session {session_name} abort failed: {e}",
                ),
            )

    # Display operation summary
    console.print()
    display_operation_summary(
        total=operation_result.total_devices,
        success=operation_result.success_count,
        failed=operation_result.failed_count,
        operation="Session Abort",
    )

    # Exit with error code if any devices failed
    if operation_result.failed_count > 0:
        raise typer.Exit(code=1)
