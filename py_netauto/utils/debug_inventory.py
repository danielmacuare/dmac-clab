"""
Debug inventory script to trace variable inheritance for Nornir hosts.

This module provides utilities to inspect how variables are inherited
through the Nornir inventory hierarchy (defaults -> groups -> host).
"""

from typing import Any

from nornir.core.inventory import Host
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from py_netauto.utils.nornir_helpers import initialize_nornir

# Special Nornir attributes that are not stored in .data
SPECIAL_ATTRIBUTES = ["hostname", "username", "password", "platform", "port"]


def get_special_attribute_raw(obj, attr: str) -> Any:
    """
    Get a special attribute directly from an inventory object.

    Args:
        obj: Nornir inventory object (Host, Group, or Defaults).
        attr: Attribute name to retrieve.

    Returns:
        The attribute value or None if not set at this level.

    """
    # Use dict() to get the raw values at this level
    obj_dict = obj.dict()
    return obj_dict.get(attr)


def collect_host_variables(nr_host: Host) -> dict[str, dict[str, Any]]:
    """
    Collect all variables for a host organized by source.

    Args:
        nr_host: The Nornir Host object to inspect.

    Returns:
        Dictionary with keys 'host', 'groups', 'defaults', and 'special_attrs'.
        Special_attrs contains info about where special attributes are defined
        and which source is selected.

    """
    variables = {"host": {}, "groups": {}, "defaults": {}, "special_attrs": {}}

    # Collect host-level variables (direct data)
    variables["host"] = dict(nr_host.data)

    # Collect group-level variables
    for group in nr_host.groups:
        group_vars = {}
        # Get all keys from the group data
        for key in group.data:
            group_vars[key] = group.data[key]
        if group_vars:
            variables["groups"][group.name] = group_vars

    # Collect defaults-level variables
    if nr_host.defaults:
        variables["defaults"] = dict(nr_host.defaults.data)

    # Collect special attributes with source tracking
    for attr in SPECIAL_ATTRIBUTES:
        attr_info = {"sources": [], "selected_value": None, "selected_from": None}

        # Check defaults
        defaults_val = get_special_attribute_raw(nr_host.defaults, attr)
        if defaults_val is not None:
            attr_info["sources"].append(("defaults", defaults_val))

        # Check groups (in order)
        for group in nr_host.groups:
            group_val = get_special_attribute_raw(group, attr)
            if group_val is not None:
                attr_info["sources"].append((f"group: {group.name}", group_val))

        # Check host
        host_val = get_special_attribute_raw(nr_host, attr)
        if host_val is not None:
            attr_info["sources"].append(("host", host_val))

        # Determine which value is selected (Nornir inheritance: host > groups > defaults)
        selected_val = getattr(nr_host, attr, None)
        attr_info["selected_value"] = selected_val

        # Determine selected source
        if host_val is not None:
            attr_info["selected_from"] = "host"
        elif any(get_special_attribute_raw(group, attr) is not None for group in reversed(nr_host.groups)):
            # Find the last group that defines this attribute
            for group in reversed(nr_host.groups):
                if get_special_attribute_raw(group, attr) is not None:
                    attr_info["selected_from"] = f"group: {group.name}"
                    break
        elif defaults_val is not None:
            attr_info["selected_from"] = "defaults"

        # Only store if the attribute is defined somewhere
        if attr_info["sources"]:
            variables["special_attrs"][attr] = attr_info

    # Handle connection_options separately (it's more complex)
    conn_opts_info = {"sources": [], "selected_value": None, "selected_from": None}

    # Check defaults
    defaults_dict = nr_host.defaults.dict()
    if defaults_dict.get("connection_options"):
        conn_opts_info["sources"].append(("defaults", defaults_dict["connection_options"]))

    # Check groups
    for group in nr_host.groups:
        group_dict = group.dict()
        if group_dict.get("connection_options"):
            conn_opts_info["sources"].append((f"group: {group.name}", group_dict["connection_options"]))

    # Check host
    host_dict = nr_host.dict()
    if host_dict.get("connection_options"):
        conn_opts_info["sources"].append(("host", host_dict["connection_options"]))

    if conn_opts_info["sources"]:
        conn_opts_info["selected_value"] = dict(nr_host.connection_options)
        # Determine selected source (simplified - shows if defined at each level)
        if host_dict.get("connection_options"):
            conn_opts_info["selected_from"] = "host"
        elif any(group.dict().get("connection_options") for group in reversed(nr_host.groups)):
            for group in reversed(nr_host.groups):
                if group.dict().get("connection_options"):
                    conn_opts_info["selected_from"] = f"group: {group.name}"
                    break
        elif defaults_dict.get("connection_options"):
            conn_opts_info["selected_from"] = "defaults"

        variables["special_attrs"]["connection_options"] = conn_opts_info

    return variables


def display_host_variables(nr_host: Host) -> None:
    """
    Display all inherited variables for a host in a rich table.

    Args:
        nr_host: The Nornir Host object to display variables for.

    """
    console = Console()

    # Display host info
    console.print(f"\n[bold cyan]Host:[/bold cyan] {nr_host.name}")
    console.print(f"[bold cyan]Hostname:[/bold cyan] {nr_host.hostname}")
    console.print(f"[bold cyan]Groups:[/bold cyan] {', '.join([g.name for g in nr_host.groups])}\n")

    # Collect variables
    variables = collect_host_variables(nr_host)

    # Create table
    table = Table(
        title=f"Variable Inheritance for Host: [bold cyan]{nr_host.name}[/bold cyan]",
        show_lines=True,
    )

    table.add_column("Variable Name", style="magenta", no_wrap=True)
    table.add_column("Value", style="green")
    table.add_column("Source", style="yellow", no_wrap=False)

    # Add special attributes first (with all sources shown)
    for attr_name, attr_info in sorted(variables["special_attrs"].items()):
        value = attr_info["selected_value"]
        sources = attr_info["sources"]
        selected_from = attr_info["selected_from"]

        # Build source string showing all locations where it's defined
        source_parts = []
        for source_name, _source_val in sources:
            source_parts.append(source_name)

        source_str = ", ".join(source_parts)

        # Add note about which one was selected
        if len(sources) > 1:
            source_str += f"\n[bold cyan]→ Selected from:[/bold cyan] {selected_from}"

        table.add_row(attr_name, str(value), source_str)

    # Add defaults variables (skip if already shown as special attribute)
    for var_name, var_value in sorted(variables["defaults"].items()):
        if var_name not in variables["special_attrs"]:
            table.add_row(var_name, str(var_value), "[dim]defaults[/dim]")

    # Add group variables (skip if already shown as special attribute)
    for group_name, group_vars in variables["groups"].items():
        for var_name, var_value in sorted(group_vars.items()):
            if var_name not in variables["special_attrs"]:
                table.add_row(var_name, str(var_value), f"[bold]group:[/bold] {group_name}")

    # Add host variables (skip if already shown as special attribute)
    for var_name, var_value in sorted(variables["host"].items()):
        if var_name not in variables["special_attrs"]:
            table.add_row(var_name, str(var_value), "[bold green]host[/bold green]")

    console.print(table)

    # Display summary
    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  {len(variables['special_attrs'])} Special Attributes")
    console.print(f"  {len(variables['defaults'])} Default Vars")

    total_group_vars = sum(len(v) for v in variables["groups"].values())
    console.print(f"  {total_group_vars} Group Vars ({len(variables['groups'])} Groups)")

    for group_name, group_vars in variables["groups"].items():
        console.print(f"    Group Name: [yellow]{group_name}[/yellow] - Vars: {len(group_vars)}")

    console.print(f"  {len(variables['host'])} Host Vars")


def select_host_interactive(nr) -> str | None:
    """
    Interactively select a host from the inventory.

    Args:
        nr: Initialized Nornir object.

    Returns:
        Selected hostname or None if cancelled.

    """
    console = Console()

    # Display available hosts
    hosts = sorted(nr.inventory.hosts.keys())
    console.print("\n[bold cyan]Available hosts:[/bold cyan]")
    for idx, host in enumerate(hosts, 1):
        console.print(f"  {idx}. {host}")

    # Prompt for selection
    choice = Prompt.ask(
        "\nEnter host name or number (or 'q' to quit)",
        default=hosts[0] if hosts else "",
    )

    if choice.lower() == "q":
        return None

    # Handle numeric selection
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(hosts):
            return hosts[idx]
        console.print("[red]Invalid selection[/red]")
        return None

    # Handle name selection
    if choice in hosts:
        return choice

    console.print(f"[red]Host '{choice}' not found in inventory[/red]")
    return None


def main():
    """
    Main function to run the inventory debug tool.

    Initializes Nornir, allows interactive host selection, and displays
    all inherited variables for the selected host.
    """
    nr = initialize_nornir()
    console = Console()

    # Interactive host selection
    target_host = select_host_interactive(nr)

    if target_host and target_host in nr.inventory.hosts:
        display_host_variables(nr.inventory.hosts[target_host])
    elif target_host:
        console.print(f"[red]Host {target_host} not found in inventory.[/red]")


if __name__ == "__main__":
    main()
