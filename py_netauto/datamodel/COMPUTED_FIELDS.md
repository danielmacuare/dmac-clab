# Data Model Computed Fields Reference

This document provides a complete reference of all computed fields in the data models, their sources, and dependencies.

## Overview

Computed fields are derived values calculated at runtime based on other model attributes or injected dependencies. They are marked with `@computed_field` decorator and appear in serialized output.

## Computed Fields by Model

### Device Model

| Field | Return Type | Data Source | Injected Dependency | Description |
|-------|-------------|-------------|---------------------|-------------|
| `role` | `str` | `hostname` | No | Device role: "spine" or "leaf" based on hostname prefix (s=spine, l=leaf) |
| `fabric_asn` | `int` | `fabric_asns` dict | Yes (`_fabric_asns`) | BGP ASN from fabric-wide mapping. Spines use 'spines' key, leaves use hostname |
| `router_id` | `IPv4Address` | `Loopback0.ipv4` | No | Router ID extracted from Loopback0 interface IP |
| `vtep_ipv4` | `IPv4Address` | `Loopback1.ipv4` | No | VTEP IP extracted from Loopback1 interface IP |

**Injected Dependencies:**
- `_fabric_asns`: `dict[str, int] | None` - Injected by `FabricDataModel.inject_fabric_asns()` validator

**Model Validators:**
- `inject_device_hostname()`: Injects hostname into all interfaces for description generation

---

### Interface Model

| Field | Return Type | Data Source | Injected Dependency | Description |
|-------|-------------|-------------|---------------------|-------------|
| `description` | `str \| None` | `name` + `_device_hostname` | Yes (`_device_hostname`) | Generated description based on interface type and parent hostname |
| `mgmt_vrf` | `str \| None` | `_mgmt_vrf` | Yes (`_mgmt_vrf`) | Management VRF name for Management0 interfaces |
| `remote_interface` | `str \| None` | `_devices` lookup | Yes (`_devices`) | Name of reciprocal interface on remote device for P2P links |

**Description Patterns:**
| Interface Name | Description Format |
|----------------|-------------------|
| `Management0` | `"Management Interface | <HOSTNAME>"` |
| `Loopback0` | `"ROUTER_ID | EVPN_PEERING | <HOSTNAME>"` |
| `Loopback1` | `"VTEP_IP | VXLAN_DATA_PLANE | <HOSTNAME>"` |
| `Ethernet*` (with remote_device) | `"P2P Link to <REMOTE_DEVICE>"` |

**Injected Dependencies:**
- `_device_hostname`: `str | None` - Injected by `Device.inject_device_hostname()` validator
- `_mgmt_vrf`: `str | None` - Injected by `FabricDataModel.inject_mgmt_vrf()` validator
- `_devices`: `list[Device] | None` - Injected by `FabricDataModel.inject_devices()` validator (only for P2P links)

---

## Dependency Injection Flow

The following diagram shows how data flows through the model hierarchy:

```
FabricDataModel (Root)
├── fabric_asns ──┐
│                 ▼
├── mgmt_vrf ─────┼──► Device._fabric_asns
│                 │
└── topology      │    └──► Interface._device_hostname
    ├── spines    │         (via Device validator)
    └── leaves    │
                   ▼
            Interface._mgmt_vrf
            (for Management0 interfaces)
            │
            ├──► Interface._devices (P2P links only)
            │         └──► remote_interface lookup
```

## Injection Order

1. **FabricDataModel initialization**: Creates topology with all devices and interfaces
2. **inject_fabric_asns()**: Runs on FabricDataModel, injects `_fabric_asns` into all devices
3. **inject_mgmt_vrf()**: Runs on FabricDataModel, injects `_mgmt_vrf` into Management0 interfaces
4. **inject_devices()**: Runs on FabricDataModel, injects `_devices` into P2P interfaces (those with remote_device)
5. **inject_device_hostname()**: Runs on Device, injects `_device_hostname` into all interfaces

## Accessing Computed Fields

### Python
```python
from py_netauto.datamodel import FabricDataModel

fabric = FabricDataModel(**data)

# Device computed fields
device = fabric.topology.spines[0]
print(device.role)           # "spine"
print(device.fabric_asn)     # 64600
print(device.router_id)      # IPv4Address('10.255.0.1')

# Interface computed fields
interface = device.interfaces[0]
print(interface.description)     # "Management Interface | S1"
print(interface.mgmt_vrf)        # "MGMT"
print(interface.remote_interface) # "Ethernet1" (for P2P links)
```

### JSON Export
All computed fields are automatically included in JSON/YAML exports:
```json
{
  "hostname": "s1",
  "role": "spine",
  "fabric_asn": 64600,
  "router_id": "10.255.0.1",
  "interfaces": [
    {
      "name": "Management0",
      "description": "Management Interface | S1",
      "mgmt_vrf": "MGMT"
    }
  ]
}
```

## Error Handling

Computed fields raise `ValueError` when required dependencies are missing:

| Field | Error Condition | Error Message |
|-------|-----------------|---------------|
| `fabric_asn` | `_fabric_asns` is None | "Fabric ASNs not initialized..." |
| `fabric_asn` | No mapping for device | "No ASN mapping found for device..." |
| `router_id` | No Loopback0 interface | "Device 'X' missing required Loopback0..." |
| `vtep_ipv4` | No Loopback1 interface | "Device 'X' missing required Loopback1..." |
| `role` | Invalid hostname prefix | "Cannot determine role from hostname..." |
