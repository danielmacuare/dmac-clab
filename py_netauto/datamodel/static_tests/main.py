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
