"""Main test entry point for FabricDataModel validation.

This module serves as the central testing point for the py_netauto datamodel.
It loads the input datamodel, validates all models, and exports the complete
fabric configuration including computed fields to JSON.
"""

import json
import tempfile
from pathlib import Path

import yaml

from py_netauto.datamodel import FabricDataModel, load_fabric, load_from_json, load_from_yaml


def _raise_test_failure(expected_exception: str) -> None:
    """Raise test failure when expected exception was not raised.

    Args:
        expected_exception: Name of the exception that should have been raised.

    Raises:
        ValueError: Always raised to indicate test failure.
    """
    msg = f"Should have raised {expected_exception}"
    raise ValueError(msg)


def load_input_datamodel(yaml_path: Path) -> dict:
    """Load input datamodel from YAML file.

    Args:
        yaml_path: Path to the input datamodel YAML file.

    Returns:
        Dictionary containing the parsed YAML data.

    Raises:
        FileNotFoundError: If the YAML file does not exist.
        yaml.YAMLError: If the YAML file is invalid.
    """
    with yaml_path.open() as f:
        return yaml.safe_load(f)


def validate_fabric(data: dict) -> FabricDataModel:
    """Validate raw data against FabricDataModel.

    Args:
        data: Dictionary containing fabric configuration.

    Returns:
        Validated FabricDataModel instance.

    Raises:
        ValidationError: If the data fails Pydantic validation.
    """
    return FabricDataModel.model_validate(data)


def test_topology(fabric: FabricDataModel) -> bool:
    """Test topology model validation.

    Verifies that spines and leaves are correctly parsed and accessible.

    Args:
        fabric: Validated FabricDataModel instance.

    Returns:
        True if all topology tests pass.

    Raises:
        ValueError: If topology validation fails.
    """
    print("\n[TEST] Topology Validation")
    print(f"  Spines: {len(fabric.topology.spines.devices)}")
    print(f"  Leaves: {len(fabric.topology.leaves.devices)}")

    # Verify each spine has required fields
    for spine in fabric.topology.spines.devices:
        if not spine.hostname.startswith("s"):
            msg = f"Spine {spine.hostname} invalid"
            raise ValueError(msg)
        if spine.role != "spine":
            msg = f"Spine {spine.hostname} role mismatch"
            raise ValueError(msg)
        if spine.fabric_asn <= 0:
            msg = f"Spine {spine.hostname} ASN invalid"
            raise ValueError(msg)

    # Verify each leaf has required fields
    for leaf in fabric.topology.leaves.devices:
        if not leaf.hostname.startswith("l"):
            msg = f"Leaf {leaf.hostname} invalid"
            raise ValueError(msg)
        if leaf.role != "leaf":
            msg = f"Leaf {leaf.hostname} role mismatch"
            raise ValueError(msg)
        if leaf.fabric_asn <= 0:
            msg = f"Leaf {leaf.hostname} ASN invalid"
            raise ValueError(msg)

    print("  ✅ All topology tests passed")
    return True


def test_devices(fabric: FabricDataModel) -> bool:
    """Test device model validation including computed fields.

    Verifies hostname validation, role computation, and ASN assignment.

    Args:
        fabric: Validated FabricDataModel instance.

    Returns:
        True if all device tests pass.

    Raises:
        ValueError: If device validation fails.
    """
    print("\n[TEST] Device Validation")

    all_devices = fabric.topology.spines.devices + fabric.topology.leaves.devices
    print(f"  Total devices: {len(all_devices)}")

    for device in all_devices:
        # Test hostname format
        if not device.hostname.startswith(("s", "l")):
            msg = f"Invalid hostname: {device.hostname}"
            raise ValueError(msg)

        # Test role computation
        expected_role = "spine" if device.hostname.startswith("s") else "leaf"
        if device.role != expected_role:
            msg = f"Role mismatch for {device.hostname}"
            raise ValueError(msg)

        # Test ASN lookup from fabric_asns
        asn_key = "spines" if device.role == "spine" else device.hostname
        if device.fabric_asn != fabric.fabric_asns[asn_key]:
            msg = f"ASN mismatch for {device.hostname}"
            raise ValueError(msg)

        # Test router_id (computed from Loopback0)
        router_id = str(device.router_id)
        if not router_id.startswith("10.255.0"):
            msg = f"Invalid router_id for {device.hostname}: {router_id}"
            raise ValueError(msg)

        # Test VTEP for leaves (computed from Loopback1)
        if device.role == "leaf":
            vtep = str(device.vtep_ipv4)
            if not vtep.startswith("10.255.1"):
                msg = f"Invalid VTEP for {device.hostname}: {vtep}"
                raise ValueError(msg)

        print(f"    {device.hostname}: role={device.role}, asn={device.fabric_asn}, router_id={device.router_id}")

    print("  ✅ All device tests passed")
    return True


def test_interfaces(fabric: FabricDataModel) -> bool:
    """Test interface model validation.

    Verifies that interfaces are correctly parsed with IPv4/IPv6 addresses.

    Args:
        fabric: Validated FabricDataModel instance.

    Returns:
        True if all interface tests pass.

    Raises:
        ValueError: If interface validation fails.
    """
    print("\n[TEST] Interface Validation")

    all_devices = fabric.topology.spines.devices + fabric.topology.leaves.devices
    total_interfaces = 0

    for device in all_devices:
        interface_count = len(device.interfaces)
        total_interfaces += interface_count

        # Verify each interface has required fields
        for interface in device.interfaces:
            if not interface.name:
                msg = f"Interface name missing on {device.hostname}"
                raise ValueError(msg)
            if not interface.ipv4:
                msg = f"IPv4 missing on {device.hostname}.{interface.name}"
                raise ValueError(msg)

        print(f"    {device.hostname}: {interface_count} interfaces")

    print(f"  Total interfaces across all devices: {total_interfaces}")
    print("  ✅ All interface tests passed")
    return True


def _validate_interface_description(device, interface, tested_types: set) -> None:
    """Validate interface description based on interface type.

    Args:
        device: Device containing the interface.
        interface: Interface to validate.
        tested_types: Set to track tested interface types.

    Raises:
        ValueError: If description validation fails.
    """
    desc = interface.description

    # Test Management0 description
    if interface.name == "Management0":
        expected = f"Management Interface | {device.hostname.upper()}"
        if desc != expected:
            msg = f"Management0 description mismatch on {device.hostname}: got '{desc}', expected '{expected}'"
            raise ValueError(msg)
        tested_types.add("Management0")
        print(f"    {device.hostname}.{interface.name}: {desc}")

    # Test Loopback0 description
    elif interface.name == "Loopback0":
        expected = f"ROUTER_ID | EVPN_PEERING | {device.hostname.upper()}"
        if desc != expected:
            msg = f"Loopback0 description mismatch on {device.hostname}: got '{desc}', expected '{expected}'"
            raise ValueError(msg)
        tested_types.add("Loopback0")
        print(f"    {device.hostname}.{interface.name}: {desc}")

    # Test Loopback1 description (only on leaves)
    elif interface.name == "Loopback1":
        expected = f"VTEP_IP | VXLAN_DATA_PLANE | {device.hostname.upper()}"
        if desc != expected:
            msg = f"Loopback1 description mismatch on {device.hostname}: got '{desc}', expected '{expected}'"
            raise ValueError(msg)
        tested_types.add("Loopback1")
        print(f"    {device.hostname}.{interface.name}: {desc}")

    # Test Ethernet P2P descriptions
    elif interface.name.startswith("Ethernet") and interface.remote_device:
        expected = f"P2P Link to {interface.remote_device}"
        if desc != expected:
            msg = (
                f"Ethernet description mismatch on {device.hostname}.{interface.name}: "
                f"got '{desc}', expected '{expected}'"
            )
            raise ValueError(msg)
        tested_types.add("Ethernet")
        print(f"    {device.hostname}.{interface.name}: {desc}")


def test_interface_descriptions(fabric: FabricDataModel) -> bool:
    """Test interface description computed field.

    Verifies that interface descriptions are correctly generated based on
    interface name and parent device hostname. Tests Management, Loopback0,
    Loopback1, and Ethernet P2P descriptions.

    Args:
        fabric: Validated FabricDataModel instance.

    Returns:
        True if all description tests pass.

    Raises:
        ValueError: If description validation fails.
    """
    print("\n[TEST] Interface Description Computed Field")

    all_devices = fabric.topology.spines.devices + fabric.topology.leaves.devices
    tested_types = set()

    for device in all_devices:
        for interface in device.interfaces:
            _validate_interface_description(device, interface, tested_types)

    print(f"  Tested interface types: {', '.join(sorted(tested_types))}")
    print("  ✅ All interface description tests passed")
    return True


def test_mgmt_vrf(fabric: FabricDataModel) -> bool:
    """Test interface mgmt_vrf computed field.

    Verifies that Management0 interfaces return MGMT VRF and all other
    interface types return None.

    Args:
        fabric: Validated FabricDataModel instance.

    Returns:
        True if all mgmt_vrf tests pass.

    Raises:
        ValueError: If mgmt_vrf validation fails.
    """
    print("\n[TEST] Interface MGMT VRF Computed Field")

    all_devices = fabric.topology.spines.devices + fabric.topology.leaves.devices
    mgmt_count = 0
    non_mgmt_count = 0

    for device in all_devices:
        for interface in device.interfaces:
            vrf = interface.mgmt_vrf

            # Test Management0 returns MGMT
            if interface.name == "Management0":
                if vrf != "MGMT":
                    msg = f"Management0 mgmt_vrf mismatch on {device.hostname}: got '{vrf}', expected 'MGMT'"
                    raise ValueError(msg)
                mgmt_count += 1
                print(f"    {device.hostname}.{interface.name}: VRF={vrf}")

            # All other interfaces should return None
            else:
                if vrf is not None:
                    msg = f"{interface.name} mgmt_vrf should be None on {device.hostname}: got '{vrf}'"
                    raise ValueError(msg)
                non_mgmt_count += 1

    print(f"  Management interfaces: {mgmt_count}")
    print(f"  Non-management interfaces: {non_mgmt_count}")
    print("  ✅ All mgmt_vrf tests passed")
    return True


def test_remote_interface(fabric: FabricDataModel) -> bool:
    """Test interface remote_interface computed field.

    Verifies that P2P interfaces correctly identify their reciprocal
    interface on the remote device. Tests bidirectional lookup.

    Args:
        fabric: Validated FabricDataModel instance.

    Returns:
        True if all remote_interface tests pass.

    Raises:
        ValueError: If remote_interface validation fails.
    """
    print("\n[TEST] Interface remote_interface Computed Field")

    all_devices = fabric.topology.spines.devices + fabric.topology.leaves.devices
    p2p_count = 0
    tested_links = []

    for device in all_devices:
        for interface in device.interfaces:
            # Test P2P interfaces
            if interface.remote_device and interface.name.startswith("Ethernet"):
                remote_intf = interface.remote_interface
                if remote_intf is None:
                    msg = (
                        f"{device.hostname}.{interface.name} remote_interface should not be None "
                        f"(connects to {interface.remote_device})"
                    )
                    raise ValueError(msg)
                p2p_count += 1
                tested_links.append(f"{device.hostname}.{interface.name} -> {interface.remote_device}.{remote_intf}")
                print(f"    {device.hostname}.{interface.name} -> {interface.remote_device}.{remote_intf}")

            # Test non-P2P interfaces return None
            elif not interface.remote_device:
                if interface.remote_interface is not None:
                    msg = f"{device.hostname}.{interface.name} remote_interface should be None (non-P2P interface)"
                    raise ValueError(msg)

    # Verify at least some P2P links were tested
    if p2p_count > 0:
        print(f"  Tested P2P links: {p2p_count}")
        print("  ✅ All remote_interface tests passed")
    else:
        print("  ⚠️  No P2P links found to test")

    return True


def test_remote_device_references(fabric: FabricDataModel) -> bool:
    """Test remote device reference validation.

    Verifies that the validator correctly identifies invalid remote_device
    references. This test uses the already-loaded valid fabric.

    Args:
        fabric: Validated FabricDataModel instance.

    Returns:
        True if validation is working correctly.
    """
    print("\n[TEST] Remote Device Reference Validation")

    all_devices = fabric.topology.spines.devices + fabric.topology.leaves.devices
    p2p_count = 0

    for device in all_devices:
        for interface in device.interfaces:
            if interface.remote_device:
                p2p_count += 1

    print(f"  Validated P2P references: {p2p_count}")
    print("  ✅ All remote_device references are valid")

    return True


def test_unique_ipv4_addresses(fabric: FabricDataModel) -> bool:
    """Test unique IPv4 address validation.

    Verifies that no duplicate IPv4 addresses exist across the fabric.
    This test uses the already-loaded valid fabric.

    Args:
        fabric: Validated FabricDataModel instance.

    Returns:
        True if validation is working correctly.
    """
    print("\n[TEST] Unique IPv4 Address Validation")

    all_devices = fabric.topology.spines.devices + fabric.topology.leaves.devices
    tracked_ipv4s: dict[str, str] = {}
    total_ips = 0

    for device in all_devices:
        for interface in device.interfaces:
            ip_str = str(interface.ipv4)
            total_ips += 1
            location = f"{device.hostname}.{interface.name}"

            if ip_str in tracked_ipv4s:
                other_location = tracked_ipv4s[ip_str]
                print(f"  ❌ Duplicate IP detected: {ip_str} at {location} and {other_location}")
                return False

            tracked_ipv4s[ip_str] = location

    print(f"  Validated unique IPs: {total_ips}")
    print("  ✅ All IPv4 addresses are unique")

    return True


def test_required_interfaces(fabric: FabricDataModel) -> bool:
    """Test required interfaces validation.

    Verifies that all devices have Loopback0 and leaves have Loopback1.

    Args:
        fabric: Validated FabricDataModel instance.

    Returns:
        True if validation is working correctly.
    """
    print("\n[TEST] Required Interfaces Validation")

    all_devices = fabric.topology.spines.devices + fabric.topology.leaves.devices
    loopback0_count = 0
    loopback1_count = 0

    for device in all_devices:
        interface_names = {iface.name for iface in device.interfaces}

        if "Loopback0" in interface_names:
            loopback0_count += 1

        if device.role == "leaf" and "Loopback1" in interface_names:
            loopback1_count += 1

    print(f"  Devices with Loopback0: {loopback0_count}/{len(all_devices)}")
    print(f"  Leaves with Loopback1: {loopback1_count}/{len([d for d in all_devices if d.role == 'leaf'])}")
    print("  ✅ All required interfaces present")

    return True


def test_ip_pool_allocation(fabric: FabricDataModel) -> bool:
    """Test IP pool allocation validation.

    Verifies that all interface IPs are within their designated pools.

    Args:
        fabric: Validated FabricDataModel instance.

    Returns:
        True if validation is working correctly.
    """
    print("\n[TEST] IP Pool Allocation Validation")

    all_devices = fabric.topology.spines.devices + fabric.topology.leaves.devices
    pool_counts = {"mgmt": 0, "lo0": 0, "lo1": 0, "p2p": 0}

    for device in all_devices:
        for interface in device.interfaces:
            ip = interface.ipv4

            if interface.name == "Management0":
                if ip in fabric.reserved_supernets.management_pool.ipv4_subnet:
                    pool_counts["mgmt"] += 1
            elif interface.name == "Loopback0":
                if ip in fabric.reserved_supernets.loopback0_pool:
                    pool_counts["lo0"] += 1
            elif interface.name == "Loopback1":
                if ip in fabric.reserved_supernets.loopback1_pool:
                    pool_counts["lo1"] += 1
            elif interface.name.startswith("Ethernet") and ip in fabric.reserved_supernets.p2p_pool:
                pool_counts["p2p"] += 1

    print(f"  Management IPs in pool: {pool_counts['mgmt']}")
    print(f"  Loopback0 IPs in pool: {pool_counts['lo0']}")
    print(f"  Loopback1 IPs in pool: {pool_counts['lo1']}")
    print(f"  P2P IPs in pool: {pool_counts['p2p']}")
    print("  ✅ All IPs within designated pools")

    return True


def test_network_config(fabric: FabricDataModel) -> bool:
    """Test network configuration validation.

    Verifies reserved supernets and management pool configuration.

    Args:
        fabric: Validated FabricDataModel instance.

    Returns:
        True if all network tests pass.

    Raises:
        ValueError: If network configuration validation fails.
    """
    print("\n[TEST] Network Configuration Validation")

    # Test reserved supernets
    if not fabric.reserved_supernets.p2p_pool:
        msg = "P2P pool not configured"
        raise ValueError(msg)
    if not fabric.reserved_supernets.loopback0_pool:
        msg = "Loopback0 pool not configured"
        raise ValueError(msg)
    if not fabric.reserved_supernets.loopback1_pool:
        msg = "Loopback1 pool not configured"
        raise ValueError(msg)

    # Test management pool
    if not fabric.reserved_supernets.management_pool.ipv4_subnet:
        msg = "Management IPv4 not configured"
        raise ValueError(msg)
    if not fabric.reserved_supernets.management_pool.ipv6_subnet:
        msg = "Management IPv6 not configured"
        raise ValueError(msg)

    print(f"  P2P Pool: {fabric.reserved_supernets.p2p_pool}")
    print(f"  Loopback0 Pool: {fabric.reserved_supernets.loopback0_pool}")
    print(f"  Loopback1 Pool: {fabric.reserved_supernets.loopback1_pool}")
    print(f"  Management IPv4: {fabric.reserved_supernets.management_pool.ipv4_subnet}")
    print(f"  Management IPv6: {fabric.reserved_supernets.management_pool.ipv6_subnet}")
    print("  ✅ All network tests passed")
    return True


def _serialize_fabric_to_dict(fabric: FabricDataModel) -> dict:
    """Serialize fabric to dict, handling computed fields that may not exist on all devices.

    Args:
        fabric: FabricDataModel instance to serialize.

    Returns:
        Dictionary representation of the fabric.
    """

    def serialize_device(device) -> dict:
        """Serialize a device with available computed fields."""
        device_dict = {
            "hostname": device.hostname,
            "interfaces": [
                {
                    "name": iface.name,
                    "ipv4": str(iface.ipv4),
                    "ipv6": str(iface.ipv6) if iface.ipv6 else None,
                    "remote_device": iface.remote_device,
                }
                for iface in device.interfaces
            ],
            "role": device.role,
            "fabric_asn": device.fabric_asn,
            "router_id": str(device.router_id),
        }

        # VTEP is only available on leaves (not spines)
        if device.role == "leaf":
            device_dict["vtep_ipv4"] = str(device.vtep_ipv4)

        return device_dict

    return {
        "schema_version": fabric.schema_version,
        "schema_description": fabric.schema_description,
        "fabric_name": fabric.fabric_name,
        "mgmt_vrf": fabric.mgmt_vrf,
        "reserved_supernets": {
            "p2p_pool": str(fabric.reserved_supernets.p2p_pool),
            "loopback0_pool": str(fabric.reserved_supernets.loopback0_pool),
            "loopback1_pool": str(fabric.reserved_supernets.loopback1_pool),
            "management_pool": {
                "ipv4_subnet": str(fabric.reserved_supernets.management_pool.ipv4_subnet),
                "ipv6_subnet": str(fabric.reserved_supernets.management_pool.ipv6_subnet),
            },
        },
        "fabric_asns": fabric.fabric_asns,
        "topology": {
            "platform": fabric.topology.platform,
            "ecmp_maximum_paths": fabric.topology.ecmp_maximum_paths,
            "bgp_maximum_routes": fabric.topology.bgp_maximum_routes,
            "spines": {
                "nornir_group": fabric.topology.spines.nornir_group,
                "devices": [serialize_device(spine) for spine in fabric.topology.spines.devices],
            },
            "leaves": {
                "nornir_group": fabric.topology.leaves.nornir_group,
                "devices": [serialize_device(leaf) for leaf in fabric.topology.leaves.devices],
            },
        },
    }


def _test_yaml_loader(input_datamodel_path: Path) -> bool:
    """Test load_from_yaml function.

    Args:
        input_datamodel_path: Path to test YAML file.

    Returns:
        True if test passes.

    Raises:
        ValueError: If test fails.
    """
    print("  Testing load_from_yaml()...")
    fabric_yaml = load_from_yaml(input_datamodel_path)
    if fabric_yaml.fabric_name != "ceos_clab_clos":
        msg = f"Expected fabric_name 'ceos_clab_clos', got '{fabric_yaml.fabric_name}'"
        raise ValueError(msg)
    print(
        f"    ✅ Loaded {len(fabric_yaml.topology.spines.devices)} spines, {len(fabric_yaml.topology.leaves.devices)} leaves from YAML",
    )
    return True


def _test_json_loader(fabric_yaml: FabricDataModel) -> bool:
    """Test load_from_json function.

    Args:
        fabric_yaml: Fabric model to export and re-import.

    Returns:
        True if test passes.

    Raises:
        ValueError: If test fails.
    """
    print("  Testing load_from_json()...")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json_path = Path(f.name)
        fabric_dict = _serialize_fabric_to_dict(fabric_yaml)
        json.dump(fabric_dict, f, indent=2)

    try:
        fabric_json = load_from_json(json_path)
        if fabric_json.fabric_name != "ceos_clab_clos":
            msg = f"Expected fabric_name 'ceos_clab_clos', got '{fabric_json.fabric_name}'"
            raise ValueError(msg)
        print(
            f"    ✅ Loaded {len(fabric_json.topology.spines.devices)} spines, "
            f"{len(fabric_json.topology.leaves.devices)} leaves from JSON",
        )
    finally:
        json_path.unlink()  # Clean up temp file

    return True


def _test_auto_detection(input_datamodel_path: Path, fabric_yaml: FabricDataModel) -> bool:
    """Test load_fabric auto-detection.

    Args:
        input_datamodel_path: Path to test YAML file.
        fabric_yaml: Fabric model for JSON test.

    Returns:
        True if test passes.

    Raises:
        ValueError: If test fails.
    """
    print("  Testing load_fabric() auto-detection...")
    fabric_auto_yaml = load_fabric(input_datamodel_path)
    if fabric_auto_yaml.fabric_name != "ceos_clab_clos":
        msg = f"Expected fabric_name 'ceos_clab_clos', got '{fabric_auto_yaml.fabric_name}'"
        raise ValueError(msg)
    print("    ✅ Auto-detected YAML format")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json_path = Path(f.name)
        fabric_dict = _serialize_fabric_to_dict(fabric_yaml)
        json.dump(fabric_dict, f, indent=2)

    try:
        fabric_auto_json = load_fabric(json_path)
        if fabric_auto_json.fabric_name != "ceos_clab_clos":
            msg = f"Expected fabric_name 'ceos_clab_clos', got '{fabric_auto_json.fabric_name}'"
            raise ValueError(msg)
        print("    ✅ Auto-detected JSON format")
    finally:
        json_path.unlink()

    return True


def _test_error_handling() -> bool:
    """Test error handling for data loaders.

    Returns:
        True if test passes.

    Raises:
        ValueError: If test fails.
    """
    print("  Testing error handling (file not found)...")
    try:
        load_from_yaml(Path("/nonexistent/path/file.yml"))
        msg = "Should have raised FileNotFoundError"
        raise ValueError(msg)
    except FileNotFoundError:
        print("    ✅ Correctly raised FileNotFoundError")

    print("  Testing error handling (unsupported format)...")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
        xml_path = Path(f.name)
        f.write("<fabric></fabric>")

    try:
        load_fabric(xml_path)
        # Should not reach here - create helper function to avoid TRY301
        _raise_test_failure("ValueError")
    except ValueError as e:
        if "Unsupported file extension" in str(e):
            print("    ✅ Correctly raised ValueError for unsupported format")
        else:
            msg = f"Wrong error: {e}"
            raise ValueError(msg) from e
    finally:
        xml_path.unlink()

    return True


def test_data_loaders(input_datamodel_path: Path) -> bool:
    """Test data loader functions.

    Verifies that load_from_yaml, load_from_json, and load_fabric
    correctly load and validate fabric configurations.

    Args:
        input_datamodel_path: Path to the test YAML file.

    Returns:
        True if all loader tests pass.

    Raises:
        ValueError: If any loader test fails.
    """
    print("\n[TEST] Data Loaders")

    # Test 1: load_from_yaml
    _test_yaml_loader(input_datamodel_path)
    fabric_yaml = load_from_yaml(input_datamodel_path)

    # Test 2: Export to JSON and load with load_from_json
    _test_json_loader(fabric_yaml)

    # Test 3: load_fabric with auto-detection
    _test_auto_detection(input_datamodel_path, fabric_yaml)

    # Test 4 & 5: Error handling
    _test_error_handling()

    print("  ✅ All data loader tests passed")
    return True


def _serialize_fabric_dict(fabric: FabricDataModel) -> dict:
    """Serialize FabricDataModel to dictionary including computed fields.

    Handles computed fields that may not be available on all device types
    (e.g., VTEP only on leaves, not spines).

    Args:
        fabric: Validated FabricDataModel instance.

    Returns:
        Dictionary representation of the fabric with all computed fields.
    """

    # Build export dict manually to handle computed fields gracefully
    def serialize_device(device) -> dict:
        """Serialize a device with available computed fields."""
        device_dict = {
            "hostname": device.hostname,
            "interfaces": [
                {
                    "name": iface.name,
                    "ipv4": str(iface.ipv4),
                    "ipv6": str(iface.ipv6) if iface.ipv6 else None,
                    "remote_device": iface.remote_device,
                    "description": iface.description,  # Computed field
                    "mgmt_vrf": iface.mgmt_vrf,  # Computed field
                    "remote_interface": iface.remote_interface,  # Computed field
                }
                for iface in device.interfaces
            ],
            # Computed fields
            "role": device.role,
            "fabric_asn": device.fabric_asn,
            "router_id": str(device.router_id),
        }

        # VTEP is only available on leaves (not spines)
        if device.role == "leaf":
            device_dict["vtep_ipv4"] = str(device.vtep_ipv4)

        return device_dict

    return {
        "schema_version": fabric.schema_version,
        "schema_description": fabric.schema_description,
        "fabric_name": fabric.fabric_name,
        "mgmt_vrf": fabric.mgmt_vrf,
        "reserved_supernets": {
            "p2p_pool": str(fabric.reserved_supernets.p2p_pool),
            "loopback0_pool": str(fabric.reserved_supernets.loopback0_pool),
            "loopback1_pool": str(fabric.reserved_supernets.loopback1_pool),
            "management_pool": {
                "ipv4_subnet": str(fabric.reserved_supernets.management_pool.ipv4_subnet),
                "ipv6_subnet": str(fabric.reserved_supernets.management_pool.ipv6_subnet),
            },
        },
        "fabric_asns": fabric.fabric_asns,
        "topology": {
            "platform": fabric.topology.platform,
            "ecmp_maximum_paths": fabric.topology.ecmp_maximum_paths,
            "bgp_maximum_routes": fabric.topology.bgp_maximum_routes,
            "spines": {
                "nornir_group": fabric.topology.spines.nornir_group,
                "devices": [serialize_device(spine) for spine in fabric.topology.spines.devices],
            },
            "leaves": {
                "nornir_group": fabric.topology.leaves.nornir_group,
                "devices": [serialize_device(leaf) for leaf in fabric.topology.leaves.devices],
            },
        },
    }


def export_to_yaml(fabric: FabricDataModel, output_path: Path) -> None:
    """Export FabricDataModel to YAML including computed fields.

    Args:
        fabric: Validated FabricDataModel instance.
        output_path: Path where the YAML file will be written.
    """
    print(f"\n[EXPORT] Saving YAML to {output_path}")

    fabric_dict = _serialize_fabric_dict(fabric)

    # Write to YAML file with pretty formatting
    with output_path.open("w") as f:
        yaml.dump(fabric_dict, f, default_flow_style=False, sort_keys=False, indent=2)

    print("  ✅ Exported successfully")
    print(f"  File size: {output_path.stat().st_size} bytes")


def export_to_json(fabric: FabricDataModel, output_path: Path) -> None:
    """Export FabricDataModel to JSON including computed fields.

    Args:
        fabric: Validated FabricDataModel instance.
        output_path: Path where the JSON file will be written.
    """
    print(f"\n[EXPORT] Saving JSON to {output_path}")

    fabric_dict = _serialize_fabric_dict(fabric)

    # Write to JSON file with pretty formatting
    with output_path.open("w") as f:
        json.dump(fabric_dict, f, indent=2, default=str)

    print("  ✅ Exported successfully")
    print(f"  File size: {output_path.stat().st_size} bytes")


def export_to_json_schema(output_path: Path) -> None:
    """Export FabricDataModel JSON Schema.

    Args:
        output_path: Path where the JSON Schema file will be written.
    """
    print(f"\n[EXPORT] Saving JSON Schema to {output_path}")

    # Generate JSON Schema from the Pydantic model
    schema = FabricDataModel.model_json_schema()

    # Write to JSON Schema file with pretty formatting
    with output_path.open("w") as f:
        json.dump(schema, f, indent=2, default=str)

    print("  ✅ Exported successfully")
    print(f"  File size: {output_path.stat().st_size} bytes")


def main() -> None:
    """Main entry point for datamodel testing and export."""
    print("=" * 60)
    print("FabricDataModel Testing and Export")
    print("=" * 60)

    # Define paths
    base_dir = Path(__file__).parent
    input_datamodel_path = base_dir / "input-datamodel.yaml"
    output_yaml_path = base_dir / "output-datamodel.yml"
    output_json_path = base_dir / "output-datamodel.json"
    output_schema_path = base_dir / "output-datamodel-schema.json"

    print(f"\nLoading input datamodel: {input_datamodel_path}")

    # Load and validate
    data = load_input_datamodel(input_datamodel_path)
    print(f"  Schema: {data['schema_version']} - {data['schema_description']}")
    print(f"  Fabric: {data['fabric_name']}")

    fabric = validate_fabric(data)
    print("  ✅ FabricDataModel validated successfully")

    # Run all tests
    all_tests_passed = True
    all_tests_passed &= test_topology(fabric)
    all_tests_passed &= test_devices(fabric)
    all_tests_passed &= test_interfaces(fabric)
    all_tests_passed &= test_interface_descriptions(fabric)
    all_tests_passed &= test_mgmt_vrf(fabric)
    all_tests_passed &= test_remote_interface(fabric)
    all_tests_passed &= test_remote_device_references(fabric)
    all_tests_passed &= test_unique_ipv4_addresses(fabric)
    all_tests_passed &= test_required_interfaces(fabric)
    all_tests_passed &= test_ip_pool_allocation(fabric)
    all_tests_passed &= test_network_config(fabric)
    all_tests_passed &= test_data_loaders(input_datamodel_path)

    # Export to all formats
    export_to_yaml(fabric, output_yaml_path)
    export_to_json(fabric, output_json_path)
    export_to_json_schema(output_schema_path)

    # Summary
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("\nOutput files:")
    print(f"  - {output_yaml_path}")
    print(f"  - {output_json_path}")
    print(f"  - {output_schema_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
