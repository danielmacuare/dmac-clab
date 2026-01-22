import logging

from nornir import InitNornir
from nornir.core import Nornir

from py_netauto.config import (
    GENERATED_CONFIGS_FOLDER_PATH,
    NORNIR_CONFIG_FILE_PATH,
    NORNIR_INVENTORY_DEFAULTS_PATH,
    NORNIR_INVENTORY_GROUPS_PATH,
    NORNIR_INVENTORY_HOSTS_PATH,
    SECRET_BGP_PASSWORD,
    SECRET_SSH_PASSWORD,
)

# Re-export constants for backward compatibility
__all__ = ["GENERATED_CONFIGS_FOLDER_PATH", "NORNIR_CONFIG_FILE_PATH", "initialize_nornir"]


def _inject_secrets_into_inventory(nr: Nornir) -> None:
    """
    Inject secrets and credentials into the Nornir inventory.

    This function injects environment-based secrets into the Nornir inventory
    defaults and sets SSH credentials for hosts that don't have them explicitly
    configured.

    Args:
        nr: The Nornir instance to inject secrets into.

    """
    print("[DEBUG] - Injecting secrets into Nornir inventory")

    # Inject the secrets into the global defaults for template access
    nr.inventory.defaults.data["secret_bgp_password"] = SECRET_BGP_PASSWORD.get_secret_value()
    nr.inventory.defaults.password = SECRET_SSH_PASSWORD.get_secret_value()
    print("[DEBUG] - Injected BGP and SSH passwords into inventory defaults")


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
        nr: Nornir = InitNornir(
            config_file=str(NORNIR_CONFIG_FILE_PATH),
        )

    else:
        # If a config file is not provided, then provide hosts, groups and default paths
        print("[DEBUG] - Nornir Config file has not been provided via the 'NORNIR_CONFIG_FILE_PATH' env var.")
        print(f"[DEBUG] - Loading Nornir Inventory (Hosts) from: {NORNIR_INVENTORY_HOSTS_PATH}")
        print(f"[DEBUG] - Loading Nornir Inventory (Groups) from: {NORNIR_INVENTORY_GROUPS_PATH}")
        print(f"[DEBUG] - Loading Nornir Inventory (Defaults) from: {NORNIR_INVENTORY_DEFAULTS_PATH}")

        logging.basicConfig(filename="scrapli.log", level=logging.DEBUG)

        nr: Nornir = InitNornir(
            inventory={
                "plugin": "SimpleInventory",
                "options": {
                    "host_file": str(NORNIR_INVENTORY_HOSTS_PATH),
                    "group_file": str(NORNIR_INVENTORY_GROUPS_PATH),
                    "defaults_file": str(NORNIR_INVENTORY_DEFAULTS_PATH),
                },
            },
            logging={
                "enabled": True,
                "level": "DEBUG",
                "log_file": "nornir.log",
            },  # Logging is a top-level key
        )
    # Inject secrets and credentials into the inventory
    _inject_secrets_into_inventory(nr)

    # Filtering
    # nr = nr.filter(name="l3")
    # nr = nr.filter(role="leaf")
    return nr
