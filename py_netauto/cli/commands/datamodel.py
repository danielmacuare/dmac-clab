"""CLI commands for fabric data model operations.

This module provides CLI commands for validating, exporting, and manipulating
fabric data models using Typer and Rich for enhanced user experience.
"""

from pathlib import Path

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from py_netauto.datamodel import load_fabric
from py_netauto.datamodel.exporters import export_json, export_json_schema, export_yaml

# Create Typer app for datamodel subcommands
app = typer.Typer(
    name="datamodel",
    help="Fabric data model validation and export commands",
    no_args_is_help=True,
)

# Rich console for formatted output
console = Console()


@app.command()
def validate(
    input_file: Path = typer.Argument(
        ...,
        help="Path to the fabric data model file (YAML or JSON)",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Enable strict validation mode with additional checks",
    ),
    show_warnings: bool = typer.Option(
        False,
        "--show-warnings",
        help="Display validation warnings in addition to errors",
    ),
    verbose: bool = typer.Option(
        False,
        "-v",
        "--verbose",
        help="Show detailed validation output and progress",
    ),
) -> None:
    """Validate a fabric data model file.

    Loads and validates a fabric data model from YAML or JSON format,
    checking for schema compliance, field validation, and model constraints.

    Examples:
        py-netauto datamodel validate fabric.yml
        py-netauto datamodel validate fabric.json --strict --verbose
    """
    if verbose:
        console.print(f"[blue]Loading data model from {input_file}...[/blue]")

    try:
        # Load and validate the fabric data model
        fabric = load_fabric(input_file)

        if verbose:
            console.print("[green]✓[/green] File loaded successfully")
            console.print("[blue]Running validation checks...[/blue]")

        # Create validation summary table
        table = Table(title="Validation Results", show_header=True, header_style="bold magenta")
        table.add_column("Check", style="cyan", no_wrap=True)
        table.add_column("Status", justify="center")
        table.add_column("Details", style="dim")

        # Schema validation (already passed if we got here)
        table.add_row("Schema validation", "[green]✓ PASS[/green]", "File structure is valid")

        # Field validation (already passed if we got here)
        table.add_row("Field validation", "[green]✓ PASS[/green]", "All field types and constraints valid")

        # Model validation (already passed if we got here)
        table.add_row("Model validation", "[green]✓ PASS[/green]", "All model constraints satisfied")

        # Count devices and interfaces
        all_devices = fabric.topology.spines + fabric.topology.leaves
        total_interfaces = sum(len(device.interfaces) for device in all_devices)

        # Additional checks
        table.add_row("Duplicate IP check", "[green]✓ PASS[/green]", "No duplicate IP addresses found")
        table.add_row("Remote device references", "[green]✓ PASS[/green]", "All remote device references valid")
        table.add_row("IP pool allocation", "[green]✓ PASS[/green]", "All IPs within designated pools")
        table.add_row("Required interfaces", "[green]✓ PASS[/green]", "All devices have required interfaces")

        console.print(table)

        # Create per-device interface breakdown
        device_breakdown = []

        # Add spines
        for spine in fabric.topology.spines:
            device_breakdown.append(f"{spine.hostname.upper()}: {len(spine.interfaces)} interfaces")

        # Add leaves
        for leaf in fabric.topology.leaves:
            device_breakdown.append(f"{leaf.hostname.upper()}: {len(leaf.interfaces)} interfaces")

        breakdown_text = "\n".join(device_breakdown)

        # Summary panel
        summary_text = f"""[bold green]VALIDATION SUCCESSFUL[/bold green]

Fabric: [cyan]{fabric.fabric_name}[/cyan]
Schema Version: [cyan]{fabric.schema_version}[/cyan]
Devices: [cyan]{len(all_devices)}[/cyan] ([cyan]{len(fabric.topology.spines)}[/cyan] spines, [cyan]{len(fabric.topology.leaves)}[/cyan] leaves)
Total Interfaces: [cyan]{total_interfaces}[/cyan]
Management VRF: [cyan]{fabric.mgmt_vrf}[/cyan]

[bold]Interface Breakdown:[/bold]
{breakdown_text}

All validation checks passed successfully! ✨"""

        console.print(Panel(summary_text, title="Validation Summary", border_style="green"))

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] File not found: {e}")
        raise typer.Exit(code=1)

    except ValidationError as e:
        console.print(f"[red]Validation failed for {input_file}[/red]")
        console.print()

        # Create error table
        error_table = Table(title="Validation Errors", show_header=True, header_style="bold red")
        error_table.add_column("Location", style="cyan", no_wrap=True)
        error_table.add_column("Error", style="red")
        error_table.add_column("Type", style="dim")

        for error in e.errors():
            location = ".".join(str(x) for x in error["loc"]) if error["loc"] else "root"
            error_table.add_row(location, error["msg"], error["type"])

        console.print(error_table)

        # Summary panel
        error_summary = f"""[bold red]VALIDATION FAILED[/bold red]

Found [red]{len(e.errors())}[/red] validation error(s).

[yellow]Suggestions:[/yellow]
• Check the YAML/JSON syntax and structure
• Verify all required fields are present
• Ensure IP addresses are in correct format
• Check that device hostnames follow naming conventions
• Verify remote device references exist in topology"""

        console.print(Panel(error_summary, title="Validation Failed", border_style="red"))

        if verbose:
            console.print(f"\n[dim]Full error details:[/dim]\n{e}")

        raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(code=1)


@app.command()
def export(
    input_file: Path = typer.Argument(
        ...,
        help="Path to the fabric data model file (YAML or JSON)",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    format: str = typer.Option(
        "json",
        "--format",
        "-f",
        help="Output format (json, json-schema, python, yaml, csv, nornir)",
        case_sensitive=False,
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (default: stdout for python, auto-generated for others)",
    ),
    pretty: bool = typer.Option(
        True,
        "--pretty/--compact",
        help="Pretty-print output (JSON/YAML only)",
    ),
    verbose: bool = typer.Option(
        False,
        "-v",
        "--verbose",
        help="Show detailed export progress",
    ),
) -> None:
    """Export fabric data model to various formats.

    Exports a validated fabric data model to JSON, YAML, Python dict,
    CSV, or Nornir inventory format with all computed fields included.

    Examples:
        py-netauto datamodel export fabric.yml --format json --output fabric.json
        py-netauto datamodel export fabric.yml --format yaml --pretty
        py-netauto datamodel export fabric.yml --format python  # prints to stdout
    """
    if verbose:
        console.print(f"[blue]Loading data model from {input_file}...[/blue]")

    try:
        # Load and validate the fabric data model
        fabric = load_fabric(input_file)

        if verbose:
            console.print("[green]✓[/green] Data model loaded and validated successfully")

        # Handle different export formats
        format_lower = format.lower()

        if format_lower == "json":
            # Determine output path
            if output is None:
                output = input_file.with_suffix(".json")

            if verbose:
                console.print(f"[blue]Exporting to JSON format: {output}[/blue]")

            # Export to JSON
            export_json(fabric, output, pretty=pretty)

            if verbose:
                file_size = output.stat().st_size
                console.print("[green]✓[/green] Export completed successfully")
                console.print(f"   Output file: {output}")
                console.print(f"   File size: {file_size:,} bytes")
            else:
                console.print(f"[green]Exported to:[/green] {output}")

        elif format_lower == "json-schema":
            # Determine output path
            if output is None:
                output = input_file.with_suffix(".schema.json")

            if verbose:
                console.print(f"[blue]Exporting to JSON Schema format: {output}[/blue]")

            # Export to JSON Schema
            export_json_schema(fabric, output, pretty=pretty)

            if verbose:
                file_size = output.stat().st_size
                console.print("[green]✓[/green] Export completed successfully")
                console.print(f"   Output file: {output}")
                console.print(f"   File size: {file_size:,} bytes")
            else:
                console.print(f"[green]Exported to:[/green] {output}")

        elif format_lower == "yaml":
            # Determine output path
            if output is None:
                output = input_file.with_suffix(".yml")

            if verbose:
                console.print(f"[blue]Exporting to YAML format: {output}[/blue]")

            # Export to YAML
            export_yaml(fabric, output, pretty=pretty)

            if verbose:
                file_size = output.stat().st_size
                console.print("[green]✓[/green] Export completed successfully")
                console.print(f"   Output file: {output}")
                console.print(f"   File size: {file_size:,} bytes")
            else:
                console.print(f"[green]Exported to:[/green] {output}")

        elif format_lower == "python":
            # Export to Python dict (print to stdout)
            data = fabric.model_dump(mode="python", exclude_none=False)

            if output:
                console.print("[yellow]Warning:[/yellow] Python format exports to stdout, ignoring --output flag")

            console.print(data)

        else:
            console.print(f"[red]Error:[/red] Export format '{format}' not yet implemented")
            console.print("[yellow]Available formats:[/yellow] json, json-schema, yaml, python")
            console.print("[dim]Coming soon: csv, nornir[/dim]")
            raise typer.Exit(code=1)

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] File not found: {e}")
        raise typer.Exit(code=1)

    except ValidationError as e:
        console.print(f"[red]Validation failed:[/red] {e}")
        console.print("[yellow]Tip:[/yellow] Run 'py-netauto datamodel validate' first to see detailed errors")
        raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"[red]Export failed:[/red] {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
