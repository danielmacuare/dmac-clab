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
__all__ = [
    "GENERATED_CONFIGS_FOLDER_PATH",
    "NORNIR_CONFIG_FILE_PATH",
    "initialize_nornir",
    "inject_current_device_data",
]


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
    print(
        "[DEBUG] - env var: SECRET_BGP_PASSWORD has been injected --> nr.inventory.defaults.data['secret_bgp_password']",
    )
    print("[DEBUG] - env var: SECRET_SSH_PASSWORD has been injected --> nr.inventory.defaults.password")


def _get_topology_data(host_obj):
    """
    Extract topology data from host's groups.

    Args:
        host_obj: Nornir host object.

    Returns:
        Topology data dictionary or None if not found.

    """
    for group in host_obj.groups:
        if "topology" in group.data:
            return group.data["topology"]
    return None


def _find_device_in_group(hostname: str, group_data: dict) -> dict | None:
    """
    Find device data by hostname in a device group.

    Args:
        hostname: Device hostname to search for.
        group_data: Group data containing devices list.

    Returns:
        Device data dictionary or None if not found.

    """
    devices = group_data.get("devices", [])
    for device in devices:
        if device.get("hostname") == hostname:
            return device
    return None


def _inject_device_data_for_host(hostname: str, host_obj, topology_data: dict) -> None:
    """
    Inject device data for a single host.

    Args:
        hostname: Device hostname.
        host_obj: Nornir host object.
        topology_data: Topology data containing device groups.

    """
    group_names = [g.name for g in host_obj.groups]

    # Check if this is a leaf device
    if "leaf_group" in group_names:
        leaves_data = topology_data.get("leaves", {})
        device_data = _find_device_in_group(hostname, leaves_data)
        if device_data:
            host_obj.data["current_device"] = device_data
            print(f"[DEBUG] - Injected current_device for leaf: {hostname}")

    # Check if this is a spine device
    elif "spine_group" in group_names:
        spines_data = topology_data.get("spines", {})
        device_data = _find_device_in_group(hostname, spines_data)
        if device_data:
            host_obj.data["current_device"] = device_data
            print(f"[DEBUG] - Injected current_device for spine: {hostname}")


def inject_current_device_data(nr: Nornir) -> None:
    """
    Inject current device data into each host for template access.

    This function extracts device-specific data from the topology structure
    stored in group data and injects it into each host's data dictionary as
    'current_device'. This makes device data easily accessible in Jinja2 templates.

    The function looks for topology data in the host's groups (typically the 'fabric'
    group) and matches devices by hostname to inject the appropriate data.

    Args:
        nr: The Nornir instance with inventory to inject device data into.

    Example:
        After calling this function, templates can access device data via:




    jinja2
        {{ current_device.hostname }}
        {{ current_device.interfaces[0].name }}




    """
    print("[DEBUG] - Injecting current_device data into hosts")

    for hostname, host_obj in nr.inventory.hosts.items():
        topology_data = _get_topology_data(host_obj)

        if not topology_data:
            print(f"[DEBUG] - No topology data found for host {hostname}")
            continue

        _inject_device_data_for_host(hostname, host_obj, topology_data)


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
                "enabled": False,  # Disable Nornir logging to avoid conflict with native Python logging
            },
        )
    # Inject secrets and credentials into the inventory
    _inject_secrets_into_inventory(nr)

    # Inject current device data for template access
    inject_current_device_data(nr)

    # Filtering
    # nr = nr.filter(name="l3")
    # nr = nr.filter(role="leaf")
    return nr
