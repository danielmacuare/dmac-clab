# Nornir Inventory Variable Precedence

This document explains how Nornir resolves variable values when the same variable is defined at multiple levels in the inventory hierarchy.

## Precedence Order

Nornir follows a strict precedence order when resolving variable values:

```
Host > Groups (last to first) > Defaults
```

**Highest Priority**: Host-level definitions  
**Medium Priority**: Group-level definitions (last group in the list wins)  
**Lowest Priority**: Defaults-level definitions

## How It Works

### 1. Host Level (Highest Priority)

Variables defined directly on a host in `hosts.yml` always take precedence over group and default values.

```yaml
# hosts.yml
l2:
    hostname: 172.100.100.62
    password: admin-host  # This wins!
    groups:
        - leaf_group
        - fabric
```

### 2. Group Level (Medium Priority)

When a host belongs to multiple groups, the **last group in the list** has higher priority.

```yaml
# hosts.yml
l1:
    hostname: 172.100.100.61
    groups:
        - leaf_group  # Checked first
        - fabric      # Checked second - wins if both define the same variable
```

```yaml
# groups.yml
leaf_group:
    platform: junos  # Lower priority

fabric:
    platform: arista_eos  # Higher priority - this wins for l1
```

**Result**: For host `l1`, `platform` will be `arista_eos` because `fabric` is listed after `leaf_group`.

### 3. Defaults Level (Lowest Priority)

Variables in `defaults.yml` are used only when not defined at host or group level.

```yaml
# defaults.yml
username: "admin"  # Used unless overridden by group or host
password: "admin"  # Used unless overridden by group or host
```

## Variable Types

Nornir handles two types of variables differently:

### Special Attributes

These are Nornir-reserved attributes stored directly on inventory objects:

- `hostname`
- `username`
- `password`
- `platform`
- `port`
- `connection_options`

**Precedence**: Follows the standard Host > Groups > Defaults order.

### Data Variables

Custom variables stored in the `data:` section:

```yaml
# groups.yml
fabric:
    data:
        bgp_asn: 65000
        ecmp_paths: 64
```

**Precedence**: Also follows Host > Groups > Defaults order, but these are merged rather than overridden.

## Practical Examples

### Example 1: Password Override

```yaml
# defaults.yml
password: "default-pass"

# groups.yml
fabric:
    password: "fabric-pass"

# hosts.yml
l2:
    password: "host-pass"
    groups:
        - fabric
```

**Result for l2**: `password = "host-pass"` (host wins)  
**Result for l1** (no host-level password): `password = "fabric-pass"` (group wins)

### Example 2: Multiple Groups

```yaml
# groups.yml
leaf_group:
    platform: junos

fabric:
    platform: arista_eos

# hosts.yml
l1:
    groups:
        - leaf_group
        - fabric
```

**Result**: `platform = "arista_eos"` (fabric is last in the group list)

### Example 3: Partial Override

```yaml
# defaults.yml
username: "admin"
password: "admin"

# groups.yml
fabric:
    password: "fabric-pass"
    # username not defined here

# hosts.yml
l1:
    groups:
        - fabric
    # Neither username nor password defined
```

**Result for l1**:
- `username = "admin"` (from defaults, not overridden)
- `password = "fabric-pass"` (from fabric group)

## Connection Options

Connection options follow the same precedence but are **merged** rather than completely overridden:

```yaml
# groups.yml
fabric:
    connection_options:
        scrapli:
            platform: arista_eos
            port: 22

# hosts.yml
l1:
    connection_options:
        scrapli:
            port: 2222  # Only overrides port, keeps platform
```

**Result**: Both `platform: arista_eos` and `port: 2222` are used.

## Debugging Precedence

Use the `debug_inventory.py` script to see exactly where each variable comes from:

```bash
uv run python py_netauto/utils/debug_inventory.py
```

The script shows:
- All sources where a variable is defined
- Which source was selected based on precedence
- The final value used by Nornir

### Example Output

```
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Variable Name ┃ Value        ┃ Source                      ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ password      │ admin-host   │ defaults, group: fabric,    │
│               │              │ host                        │
│               │              │ → Selected from: host       │
└───────────────┴──────────────┴─────────────────────────────┘
```

This shows that `password` is defined in three places, but the host-level value was selected.

## Best Practices

1. **Use Defaults for Common Values**: Put organization-wide defaults in `defaults.yml`
2. **Use Groups for Role-Based Config**: Define role-specific values in groups
3. **Use Host for Exceptions**: Only override at host level when necessary
4. **Order Groups Carefully**: Remember that the last group in the list has higher priority
5. **Document Overrides**: Comment why you're overriding a value at a higher level

## References

- [Nornir Inventory Documentation](https://nornir.readthedocs.io/en/latest/tutorial/inventory.html)
- [Nornir Inventory Data Model](https://nornir.readthedocs.io/en/latest/ref/api/inventory.html)
