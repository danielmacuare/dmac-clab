from nornir.core.inventory import Host
from rich.console import Console
from rich.pretty import pprint as rprint
from rich.table import Table

from py_netauto.utils.nornir_helpers import _inject_secrets_into_inventory, initialize_nornir


def trace_host_variables(nr_host: Host):
    console = Console()
    table = Table(title=f"Variable Trace for Host: [bold cyan]{nr_host.name}[/bold cyan]")

    table.add_column("Variable Name", style="magenta")
    table.add_column("Value", style="green")
    table.add_column("Source", style="yellow")

    # 1. Get ALL keys known to the host (merged view)
    # .keys() on a Nornir Host object looks through the whole hierarchy
    all_keys = sorted(nr_host.keys())

    for key in all_keys:
        value = nr_host.get(key)
        source = "Unknown"

        # Check Host level
        if key in nr_host.data:
            source = "Host (Direct)"

        # Check Group level (Iterate through all assigned groups)
        else:
            for group in nr_host.groups:
                if key in group.data:
                    source = f"Group ({group.name})"
                    break

            # Check Defaults level
            if source == "Unknown" and key in nr_host.defaults.data:
                source = "Defaults"

        table.add_row(str(key), str(value), source)

    console.print(table)


def main():
    nr = initialize_nornir()

    # Specify the host you want to inspect
    target_host = "l5"

    if target_host in nr.inventory.hosts:
        trace_host_variables(nr.inventory.hosts[target_host])
        # rprint("Inventory vars:")
        # rprint(nr.inventory.dict())
    # pass

    else:
        print(f"Host {target_host} not found in inventory.")


if __name__ == "__main__":
    main()
