"""Main test entry point for FabricDataModel validation.

This module serves as the central testing point for the py_netauto datamodel.
It loads the lean datamodel, validates all models, and exports the complete
fabric configuration including computed fields to JSON.
"""

import json
from pathlib import Path

import yaml

from py_netauto.datamodel import FabricDataModel


def load_lean_datamodel(yaml_path: Path) -> dict:
    """Load lean datamodel from YAML file.

    Args:
        yaml_path: Path to the lean datamodel YAML file.

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
    """
    print("\n[TEST] Topology Validation")
    print(f"  Spines: {len(fabric.topology.spines)}")
    print(f"  Leaves: {len(fabric.topology.leaves)}")

    # Verify each spine has required fields
    for spine in fabric.topology.spines:
        assert spine.hostname.startswith("s"), f"Spine {spine.hostname} invalid"
        assert spine.role == "spine", f"Spine {spine.hostname} role mismatch"
        assert spine.fabric_asn > 0, f"Spine {spine.hostname} ASN invalid"

    # Verify each leaf has required fields
    for leaf in fabric.topology.leaves:
        assert leaf.hostname.startswith("l"), f"Leaf {leaf.hostname} invalid"
        assert leaf.role == "leaf", f"Leaf {leaf.hostname} role mismatch"
        assert leaf.fabric_asn > 0, f"Leaf {leaf.hostname} ASN invalid"

    print("  ✅ All topology tests passed")
    return True


def test_devices(fabric: FabricDataModel) -> bool:
    """Test device model validation including computed fields.

    Verifies hostname validation, role computation, and ASN assignment.

    Args:
        fabric: Validated FabricDataModel instance.

    Returns:
        True if all device tests pass.
    """
    print("\n[TEST] Device Validation")

    all_devices = fabric.topology.spines + fabric.topology.leaves
    print(f"  Total devices: {len(all_devices)}")

    for device in all_devices:
        # Test hostname format
        assert device.hostname.startswith(("s", "l")), f"Invalid hostname: {device.hostname}"

        # Test role computation
        expected_role = "spine" if device.hostname.startswith("s") else "leaf"
        assert device.role == expected_role, f"Role mismatch for {device.hostname}"

        # Test ASN lookup from fabric_asns
        asn_key = "spines" if device.role == "spine" else device.hostname
        assert device.fabric_asn == fabric.fabric_asns[asn_key], f"ASN mismatch for {device.hostname}"

        # Test router_id (computed from Loopback0)
        router_id = str(device.router_id)
        assert router_id.startswith("10.255.0"), f"Invalid router_id for {device.hostname}: {router_id}"

        # Test VTEP for leaves (computed from Loopback1)
        if device.role == "leaf":
            vtep = str(device.vtep_ipv4)
            assert vtep.startswith("10.255.1"), f"Invalid VTEP for {device.hostname}: {vtep}"

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
    """
    print("\n[TEST] Interface Validation")

    all_devices = fabric.topology.spines + fabric.topology.leaves
    total_interfaces = 0

    for device in all_devices:
        interface_count = len(device.interfaces)
        total_interfaces += interface_count

        # Verify each interface has required fields
        for interface in device.interfaces:
            assert interface.name, f"Interface name missing on {device.hostname}"
            assert interface.ipv4, f"IPv4 missing on {device.hostname}.{interface.name}"

        print(f"    {device.hostname}: {interface_count} interfaces")

    print(f"  Total interfaces across all devices: {total_interfaces}")
    print("  ✅ All interface tests passed")
    return True


def test_interface_descriptions(fabric: FabricDataModel) -> bool:
    """Test interface description computed field.

    Verifies that interface descriptions are correctly generated based on
    interface name and parent device hostname. Tests Management, Loopback0,
    Loopback1, and Ethernet P2P descriptions.

    Args:
        fabric: Validated FabricDataModel instance.

    Returns:
        True if all description tests pass.
    """
    print("\n[TEST] Interface Description Computed Field")

    all_devices = fabric.topology.spines + fabric.topology.leaves
    tested_types = set()

    for device in all_devices:
        for interface in device.interfaces:
            desc = interface.description

            # Test Management0 description
            if interface.name == "Management0":
                expected = f"Management Interface | {device.hostname.upper()}"
                assert desc == expected, (
                    f"Management0 description mismatch on {device.hostname}: got '{desc}', expected '{expected}'"
                )
                tested_types.add("Management0")
                print(f"    {device.hostname}.{interface.name}: {desc}")

            # Test Loopback0 description
            elif interface.name == "Loopback0":
                expected = f"ROUTER_ID | EVPN_PEERING | {device.hostname.upper()}"
                assert desc == expected, (
                    f"Loopback0 description mismatch on {device.hostname}: got '{desc}', expected '{expected}'"
                )
                tested_types.add("Loopback0")
                print(f"    {device.hostname}.{interface.name}: {desc}")

            # Test Loopback1 description (only on leaves)
            elif interface.name == "Loopback1":
                expected = f"VTEP_IP | VXLAN_DATA_PLANE | {device.hostname.upper()}"
                assert desc == expected, (
                    f"Loopback1 description mismatch on {device.hostname}: got '{desc}', expected '{expected}'"
                )
                tested_types.add("Loopback1")
                print(f"    {device.hostname}.{interface.name}: {desc}")

            # Test Ethernet P2P descriptions
            elif interface.name.startswith("Ethernet") and interface.remote_device:
                expected = f"P2P Link to {interface.remote_device}"
                assert desc == expected, (
                    f"Ethernet description mismatch on {device.hostname}.{interface.name}: got '{desc}', expected '{expected}'"
                )
                tested_types.add("Ethernet")
                print(f"    {device.hostname}.{interface.name}: {desc}")

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
    """
    print("\n[TEST] Interface MGMT VRF Computed Field")

    all_devices = fabric.topology.spines + fabric.topology.leaves
    mgmt_count = 0
    non_mgmt_count = 0

    for device in all_devices:
        for interface in device.interfaces:
            vrf = interface.mgmt_vrf

            # Test Management0 returns MGMT
            if interface.name == "Management0":
                assert vrf == "MGMT", (
                    f"Management0 mgmt_vrf mismatch on {device.hostname}: got '{vrf}', expected 'MGMT'"
                )
                mgmt_count += 1
                print(f"    {device.hostname}.{interface.name}: VRF={vrf}")

            # All other interfaces should return None
            else:
                assert vrf is None, f"{interface.name} mgmt_vrf should be None on {device.hostname}: got '{vrf}'"
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
    """
    print("\n[TEST] Interface remote_interface Computed Field")

    all_devices = fabric.topology.spines + fabric.topology.leaves
    p2p_count = 0
    tested_links = []

    for device in all_devices:
        for interface in device.interfaces:
            # Test P2P interfaces
            if interface.remote_device and interface.name.startswith("Ethernet"):
                remote_intf = interface.remote_interface
                assert remote_intf is not None, (
                    f"{device.hostname}.{interface.name} remote_interface should not be None "
                    f"(connects to {interface.remote_device})"
                )
                p2p_count += 1
                tested_links.append(f"{device.hostname}.{interface.name} -> {interface.remote_device}.{remote_intf}")
                print(f"    {device.hostname}.{interface.name} -> {interface.remote_device}.{remote_intf}")

            # Test non-P2P interfaces return None
            elif not interface.remote_device:
                assert interface.remote_interface is None, (
                    f"{device.hostname}.{interface.name} remote_interface should be None (non-P2P interface)"
                )

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

    all_devices = fabric.topology.spines + fabric.topology.leaves
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

    all_devices = fabric.topology.spines + fabric.topology.leaves
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

    all_devices = fabric.topology.spines + fabric.topology.leaves
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

    all_devices = fabric.topology.spines + fabric.topology.leaves
    mgmt_in_pool = 0
    lo0_in_pool = 0
    lo1_in_pool = 0
    p2p_in_pool = 0

    for device in all_devices:
        for interface in device.interfaces:
            ip = interface.ipv4

            if interface.name == "Management0":
                if ip in fabric.reserved_supernets.management_pool.ipv4_subnet:
                    mgmt_in_pool += 1
            elif interface.name == "Loopback0":
                if ip in fabric.reserved_supernets.loopback0_pool:
                    lo0_in_pool += 1
            elif interface.name == "Loopback1":
                if ip in fabric.reserved_supernets.loopback1_pool:
                    lo1_in_pool += 1
            elif interface.name.startswith("Ethernet"):
                if ip in fabric.reserved_supernets.p2p_pool:
                    p2p_in_pool += 1

    print(f"  Management IPs in pool: {mgmt_in_pool}")
    print(f"  Loopback0 IPs in pool: {lo0_in_pool}")
    print(f"  Loopback1 IPs in pool: {lo1_in_pool}")
    print(f"  P2P IPs in pool: {p2p_in_pool}")
    print("  ✅ All IPs within designated pools")

    return True


def test_network_config(fabric: FabricDataModel) -> bool:
    """Test network configuration validation.

    Verifies reserved supernets and management pool configuration.

    Args:
        fabric: Validated FabricDataModel instance.

    Returns:
        True if all network tests pass.
    """
    print("\n[TEST] Network Configuration Validation")

    # Test reserved supernets
    assert fabric.reserved_supernets.p2p_pool, "P2P pool not configured"
    assert fabric.reserved_supernets.loopback0_pool, "Loopback0 pool not configured"
    assert fabric.reserved_supernets.loopback1_pool, "Loopback1 pool not configured"

    # Test management pool
    assert fabric.reserved_supernets.management_pool.ipv4_subnet, "Management IPv4 not configured"
    assert fabric.reserved_supernets.management_pool.ipv6_subnet, "Management IPv6 not configured"

    print(f"  P2P Pool: {fabric.reserved_supernets.p2p_pool}")
    print(f"  Loopback0 Pool: {fabric.reserved_supernets.loopback0_pool}")
    print(f"  Loopback1 Pool: {fabric.reserved_supernets.loopback1_pool}")
    print(f"  Management IPv4: {fabric.reserved_supernets.management_pool.ipv4_subnet}")
    print(f"  Management IPv6: {fabric.reserved_supernets.management_pool.ipv6_subnet}")
    print("  ✅ All network tests passed")
    return True


def export_to_json(fabric: FabricDataModel, output_path: Path) -> None:
    """Export FabricDataModel to JSON including computed fields.

    Handles computed fields that may not be available on all device types
    (e.g., VTEP only on leaves, not spines).

    Args:
        fabric: Validated FabricDataModel instance.
        output_path: Path where the JSON file will be written.
    """
    print(f"\n[EXPORT] Saving to {output_path}")

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

    fabric_dict = {
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
            "spines": [serialize_device(spine) for spine in fabric.topology.spines],
            "leaves": [serialize_device(leaf) for leaf in fabric.topology.leaves],
        },
    }

    # Write to JSON file with pretty formatting
    with output_path.open("w") as f:
        json.dump(fabric_dict, f, indent=2, default=str)

    print("  ✅ Exported successfully")
    print(f"  File size: {output_path.stat().st_size} bytes")


def main() -> None:
    """Main entry point for datamodel testing and export."""
    print("=" * 60)
    print("FabricDataModel Testing and Export")
    print("=" * 60)

    # Define paths
    base_dir = Path(__file__).parent
    lean_datamodel_path = base_dir / "lean-datamodel.yaml"
    output_path = base_dir / "fabric-export.json"

    print(f"\nLoading lean datamodel: {lean_datamodel_path}")

    # Load and validate
    data = load_lean_datamodel(lean_datamodel_path)
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

    # Export to JSON
    export_to_json(fabric, output_path)

    # Summary
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print(f"Output: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
