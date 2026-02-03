"""Test script for Interface.mgmt_vrf computed field."""

from py_netauto.datamodel import Interface

print("=" * 60)
print("Testing Interface.mgmt_vrf Computed Field")
print("=" * 60)

# Test 1: Management0 interface should return MGMT
print("\n[Test 1] Management0 interface should return MGMT VRF")
try:
    iface = Interface(
        name="Management0",
        ipv4="172.100.100.101/24",
    )

    print(f"  Interface: {iface.name}")
    print(f"  MGMT VRF: {iface.mgmt_vrf}")
    print(f"  MGMT VRF type: {type(iface.mgmt_vrf)}")
    assert iface.mgmt_vrf == "MGMT"
    print(f"  ✅ PASS: Management0 returns MGMT VRF")
except Exception as e:
    print(f"  ❌ FAIL: {e}")

# Test 2: Ethernet interface should return None
print("\n[Test 2] Ethernet interface should return None")
try:
    iface = Interface(
        name="Ethernet1",
        ipv4="10.254.1.0/31",
        remote_device="l1",
    )

    print(f"  Interface: {iface.name}")
    print(f"  MGMT VRF: {iface.mgmt_vrf}")
    print(f"  MGMT VRF type: {type(iface.mgmt_vrf)}")
    assert iface.mgmt_vrf is None
    print(f"  ✅ PASS: Ethernet interface returns None")
except Exception as e:
    print(f"  ❌ FAIL: {e}")

# Test 3: Loopback0 interface should return None
print("\n[Test 3] Loopback0 interface should return None")
try:
    iface = Interface(
        name="Loopback0",
        ipv4="10.255.0.1/32",
    )

    print(f"  Interface: {iface.name}")
    print(f"  MGMT VRF: {iface.mgmt_vrf}")
    print(f"  MGMT VRF type: {type(iface.mgmt_vrf)}")
    assert iface.mgmt_vrf is None
    print(f"  ✅ PASS: Loopback0 returns None")
except Exception as e:
    print(f"  ❌ FAIL: {e}")

# Test 4: Loopback1 interface should return None
print("\n[Test 4] Loopback1 interface should return None")
try:
    iface = Interface(
        name="Loopback1",
        ipv4="10.255.1.1/32",
    )

    print(f"  Interface: {iface.name}")
    print(f"  MGMT VRF: {iface.mgmt_vrf}")
    print(f"  MGMT VRF type: {type(iface.mgmt_vrf)}")
    assert iface.mgmt_vrf is None
    print(f"  ✅ PASS: Loopback1 returns None")
except Exception as e:
    print(f"  ❌ FAIL: {e}")

# Test 5: Multiple Management0 interfaces (different devices context)
print("\n[Test 5] Multiple Management0 interfaces")
try:
    management_interfaces = []
    for i in range(1, 4):
        iface = Interface(
            name="Management0",
            ipv4=f"172.100.100.{i}/24",
        )
        management_interfaces.append(iface)

    vrf_values = [iface.mgmt_vrf for iface in management_interfaces]
    print(f"  Management interfaces: {len(management_interfaces)}")
    print(f"  MGMT VRF values: {vrf_values}")
    assert all(vrf == "MGMT" for vrf in vrf_values)
    print(f"  ✅ PASS: All Management0 interfaces return MGMT VRF")
except Exception as e:
    print(f"  ❌ FAIL: {e}")

# Test 6: Interface with IPv6 should also work
print("\n[Test 6] Management0 with IPv6 should return MGMT VRF")
try:
    from ipaddress import IPv6Interface

    iface = Interface(
        name="Management0",
        ipv4="172.100.100.101/24",
        ipv6="2001:db8::101/64",
    )

    print(f"  Interface: {iface.name}")
    print(f"  IPv4: {iface.ipv4}")
    print(f"  IPv6: {iface.ipv6}")
    print(f"  MGMT VRF: {iface.mgmt_vrf}")
    assert iface.mgmt_vrf == "MGMT"
    print(f"  ✅ PASS: Management0 with IPv6 returns MGMT VRF")
except Exception as e:
    print(f"  ❌ FAIL: {e}")

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)
