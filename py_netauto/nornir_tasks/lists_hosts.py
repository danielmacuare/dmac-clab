#!/usr/bin/env/python3
from nornir.core import Nornir

from py_netauto.utils.nornir_helpers import initialize_nornir


def main() -> None:
    # Initialize Nornir using your custom Pathlib helper
    nr: Nornir = initialize_nornir()

    print("\nListing all hosts in the inventory:")
    print("-" * 30)

    # nr.inventory.hosts is a dictionary-like object
    # We can iterate over its keys to get the host names
    for host_name in nr.inventory.hosts:
        print(f"Host Found: {host_name}")

    print("-" * 30)
    print(f"Total hosts: {len(nr.inventory.hosts)}")


if __name__ == "__main__":
    main()
