from nornir import InitNornir
from nornir.core import Nornir

from py_netauto.config import NORNIR_CONFIG_FILE_PATH, NORNIR_INVENTORY_GROUPS_PATH, NORNIR_INVENTORY_HOSTS_PATH

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
    print(f"[DEBUG] - Loading Nornir Config from: {NORNIR_CONFIG_FILE_PATH}")
    print(f"[DEBUG] - Loading Nornir Inventory (Hosts) from: {NORNIR_INVENTORY_HOSTS_PATH}")
    print(f"[DEBUG] - Loading Nornir Inventory (Groups) from: {NORNIR_INVENTORY_GROUPS_PATH}")

    # InitNornir expects the config_file as a string
    nr: Nornir = InitNornir(
        config_file=str(NORNIR_CONFIG_FILE_PATH),
        inventory={
            "plugin": "SimpleInventory",
            "options": {"host_file": str(NORNIR_INVENTORY_HOSTS_PATH), "group_file": str(NORNIR_INVENTORY_GROUPS_PATH)},
        },
    )
    return nr
