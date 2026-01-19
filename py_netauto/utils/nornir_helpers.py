from nornir import InitNornir
from nornir.core import Nornir

from py_netauto.config import (
    NORNIR_CONFIG_FILE_PATH,
    NORNIR_INVENTORY_DEFAULTS_PATH,
    NORNIR_INVENTORY_GROUPS_PATH,
    NORNIR_INVENTORY_HOSTS_PATH,
)

# Re-export constants for backward compatibility
__all__ = ["NORNIR_CONFIG_FILE_PATH", "initialize_nornir"]


def initialize_nornir() -> Nornir:
    """
    Initializes Nornir using the NORNIR_CONFIG_FILE_PATH from configuration.

    The configuration path is loaded from environment variables via the
    py_netauto.config module. Validation of the path is handled during
    module initialization in py_netauto.config.

    Returns:
        Nornir: Initialized Nornir instance

    Raises:
        FileNotFoundError: If the configuration file does not exist
            (raised by py_netauto.config during import)

    """
    # If Config file is provided
    if NORNIR_CONFIG_FILE_PATH is not None:
        print(f"[DEBUG] - Loading Nornir Config from: {NORNIR_CONFIG_FILE_PATH}")
        nr: Nornir = InitNornir(config_file=str(NORNIR_CONFIG_FILE_PATH))

    else:
        # If a config file is not provided, then provide hosts, groups and default paths
        print("[DEBUG] - Nornir Config file has not been provided via the 'NORNIR_CONFIG_FILE_PATH' env var.")
        print(f"[DEBUG] - Loading Nornir Inventory (Hosts) from: {NORNIR_INVENTORY_HOSTS_PATH}")
        print(f"[DEBUG] - Loading Nornir Inventory (Groups) from: {NORNIR_INVENTORY_GROUPS_PATH}")
        print(f"[DEBUG] - Loading Nornir Inventory (Defaults) from: {NORNIR_INVENTORY_DEFAULTS_PATH}")
        nr: Nornir = InitNornir(
            inventory={
                "plugin": "SimpleInventory",
                "options": {
                    "host_file": str(NORNIR_INVENTORY_HOSTS_PATH),
                    "group_file": str(NORNIR_INVENTORY_GROUPS_PATH),
                    "defaults_file": str(NORNIR_INVENTORY_DEFAULTS_PATH),
                },
            },
        )
    return nr
