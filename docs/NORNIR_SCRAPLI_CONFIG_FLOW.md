# How nornir-scrapli Loads Configuration from Nornir Inventory

This document explains in detail how nornir-scrapli tasks (like `cfg_load_config`, `send_command`, etc.) retrieve configuration parameters from the Nornir inventory and pass them to Scrapli.

## Overview

The configuration flow happens in several stages:

1. **Nornir Task Execution** - You call a nornir-scrapli task
2. **Connection Request** - The task requests a Scrapli connection
3. **Parameter Resolution** - Nornir resolves connection parameters from inventory
4. **Connection Creation** - Scrapli connection is created with resolved parameters
5. **Task Execution** - The task executes using the established connection

---

## Detailed Flow

### Stage 1: Task Invocation

When you call a nornir-scrapli task:

```python
from nornir_scrapli.tasks import cfg_load_config

# Inside your Nornir task function
task.run(task=cfg_load_config, config=config, replace=True, privilege_level="privilege_exec")
```

### Stage 2: Connection Retrieval

The task immediately tries to get a Scrapli connection:

**File**: `.venv/lib/python3.12/site-packages/nornir_scrapli/tasks/cfg/load_config.py`

```python
def cfg_load_config(task: Task, config: str, replace: bool = False, **kwargs: Any) -> Result:
    # First line: Get or create the scrapli_cfg connection
    scrapli_cfg_conn = ScrapliConfig.get_connection(task=task)
    
    # Then use it to load config
    scrapli_response = scrapli_cfg_conn.load_config(config=config, replace=replace, **kwargs)
```

### Stage 3: Connection Parameter Resolution

**File**: `.venv/lib/python3.12/site-packages/nornir_scrapli/connection.py`

The `ScrapliConfig.get_connection()` method does the following:

```python
@staticmethod
def get_connection(task: Task) -> ScrapliCfgPlatform:
    try:
        # Try to get existing connection
        connection = task.host.get_connection("scrapli_cfg", task.nornir.config)
    except AttributeError:
        # If it doesn't exist, spawn a new one
        task.host.connections["scrapli_cfg"] = ScrapliConfig.spawn(task=task)
        connection = task.host.get_connection("scrapli_cfg", task.nornir.config)
    
    return connection
```

When `task.host.get_connection()` is called, it triggers Nornir's connection parameter resolution.

**File**: `.venv/lib/python3.12/site-packages/nornir/core/inventory.py`

```python
def get_connection(self, connection: str, configuration: Config) -> Any:
    if connection not in self.connections:
        # Get connection parameters from inventory
        conn = self.get_connection_parameters(connection)
        
        # Open the connection with resolved parameters
        self.open_connection(
            connection=connection,
            configuration=configuration,
            hostname=conn.hostname,
            port=conn.port,
            username=conn.username,
            password=conn.password,
            platform=conn.platform,
            extras=conn.extras,
        )
    return self.connections[connection].connection
```

### Stage 4: Parameter Resolution Hierarchy

**File**: `.venv/lib/python3.12/site-packages/nornir/core/inventory.py`

The `get_connection_parameters()` method resolves parameters in this order:

```python
def get_connection_parameters(self, connection: Optional[str] = None) -> ConnectionOptions:
    if not connection:
        # Use host-level attributes directly
        d = ConnectionOptions(
            hostname=self.hostname,
            port=self.port,
            username=self.username,
            password=self.password,
            platform=self.platform,
            extras={},
        )
    else:
        # Resolve connection-specific options recursively
        r = self._get_connection_options_recursively(connection)
        if r is not None:
            d = ConnectionOptions(
                hostname=r.hostname if r.hostname is not None else self.hostname,
                port=r.port if r.port is not None else self.port,
                username=r.username if r.username is not None else self.username,
                password=r.password if r.password is not None else self.password,
                platform=r.platform if r.platform is not None else self.platform,
                extras=r.extras if r.extras is not None else {},
            )
```

The `_get_connection_options_recursively()` method implements the resolution hierarchy:

```python
def _get_connection_options_recursively(self, connection: str) -> Optional[ConnectionOptions]:
    # 1. Start with host-level connection_options
    p = self.connection_options.get(connection)
    if p is None:
        p = ConnectionOptions(None, None, None, None, None, None)

    # 2. Check each group (in order) for connection_options
    for g in self.groups:
        sp = g._get_connection_options_recursively(connection)
        if sp is not None:
            # Only override if current value is None
            p.hostname = p.hostname if p.hostname is not None else sp.hostname
            p.port = p.port if p.port is not None else sp.port
            p.username = p.username if p.username is not None else sp.username
            p.password = p.password if p.password is not None else sp.password
            p.platform = p.platform if p.platform is not None else sp.platform
            p.extras = p.extras if p.extras is not None else sp.extras

    # 3. Finally check defaults.connection_options
    sp = self.defaults.connection_options.get(connection, None)
    if sp is not None:
        p.hostname = p.hostname if p.hostname is not None else sp.hostname
        p.port = p.port if p.port is not None else sp.port
        p.username = p.username if p.username is not None else sp.username
        p.password = p.password if p.password is not None else sp.password
        p.platform = p.platform if p.platform is not None else sp.platform
        p.extras = p.extras if p.extras is not None else sp.extras
    return p
```

**Resolution Order** (first non-None value wins):
1. Host-level `connection_options["scrapli"]`
2. Group-level `connection_options["scrapli"]` (first group to last)
3. Defaults-level `connection_options["scrapli"]`
4. Host-level attributes (`host.username`, `host.password`, etc.)

### Stage 5: Scrapli Connection Creation

**File**: `.venv/lib/python3.12/site-packages/nornir_scrapli/connection.py`

Once parameters are resolved, the `ScrapliCore.open()` method creates the actual Scrapli connection:

```python
def open(
    self,
    hostname: Optional[str],
    username: Optional[str],
    password: Optional[str],
    port: Optional[int],
    platform: Optional[str],
    extras: Optional[Dict[str, Any]] = None,
    configuration: Optional[Config] = None,
) -> None:
    extras = extras or {}
    global_config = configuration.dict() if configuration else {}

    # Build parameters dict for Scrapli
    parameters: Dict[str, Any] = {
        "host": hostname,
        "auth_username": username or "",
        "auth_password": password or "",
        "port": port or 22,
        "ssh_config_file": global_config.get("ssh", {}).get("config_file", False),
    }

    # Merge extras (from connection_options) - these override global config
    parameters.update(extras)

    # Map platform names (e.g., "eos" -> "arista_eos")
    final_platform: str = PLATFORM_MAP.get(platform, platform)

    # Create Scrapli connection
    connection = Scrapli(**parameters, platform=final_platform)
    connection.open()
    self.connection = connection
```

**Key Points**:
- `extras` dict from `connection_options["scrapli"]["extras"]` is merged into parameters
- `extras` overrides global Nornir config settings
- Parameters are mapped to Scrapli's expected argument names:
  - `username` → `auth_username`
  - `password` → `auth_password`
  - `hostname` → `host`

---

## Configuration Mapping

### From Nornir Inventory to Scrapli

| Nornir Inventory | Scrapli Parameter | Source |
|------------------|-------------------|--------|
| `hostname` | `host` | Host/Group/Defaults |
| `username` | `auth_username` | Host/Group/Defaults |
| `password` | `auth_password` | Host/Group/Defaults |
| `port` | `port` | Host/Group/Defaults |
| `platform` | `platform` | Host/Group/Defaults (mapped via PLATFORM_MAP) |
| `connection_options["scrapli"]["extras"]` | `**kwargs` | Merged directly into Scrapli parameters |

### Platform Mapping

nornir-scrapli automatically maps common platform names:

```python
PLATFORM_MAP = {
    "ios": "cisco_iosxe",
    "nxos": "cisco_nxos",
    "iosxr": "cisco_iosxr",
    "eos": "arista_eos",
    "junos": "juniper_junos",
}
```

---

## Example Configuration Flow

### Inventory Files

**hosts.yml**:
```yaml
l1:
    hostname: l1
    groups:
        - leaf_group
        - fabric
```

**groups.yml**:
```yaml
fabric:
    platform: arista_eos
    connection_options:
        scrapli:
            platform: arista_eos
            port: 22
            extras:
                auth_strict_key: False
                timeout_ops: 30
                ssh_config_file: "/etc/ssh/ssh_config.d/clab-evl3gw-dmac.conf"
                transport: "paramiko"
```

**defaults.yml**:
```yaml
username: admin
password: admin
```

### Python Code

```python
from py_netauto.utils.nornir_helpers import initialize_nornir

# Initialize Nornir
nr = initialize_nornir()

# Inject password into defaults
nr.inventory.defaults.password = "admin"
```

### Resolution Flow for Host "l1"

When `cfg_load_config` is called for host "l1":

1. **Task calls** `ScrapliConfig.get_connection(task)`
2. **Connection doesn't exist**, so it calls `ScrapliConfig.spawn(task)`
3. **Spawn gets** the underlying scrapli connection via `task.host.get_connection("scrapli", ...)`
4. **Nornir resolves** connection parameters for "scrapli":
   - Checks `l1.connection_options["scrapli"]` → Not found
   - Checks `leaf_group.connection_options["scrapli"]` → Not found
   - Checks `fabric.connection_options["scrapli"]` → **FOUND**:
     - `platform: arista_eos`
     - `port: 22`
     - `extras: {auth_strict_key: False, timeout_ops: 30, ssh_config_file: "...", transport: "paramiko"}`
   - Checks `defaults.connection_options["scrapli"]` → Not found
   - Falls back to host attributes for missing values:
     - `hostname: l1` (from host)
     - `username: admin` (from defaults)
     - `password: admin` (from defaults, injected via Python)
5. **Nornir calls** `ScrapliCore.open()` with resolved parameters
6. **ScrapliCore builds** Scrapli parameters:
   ```python
   {
       "host": "l1",
       "auth_username": "admin",
       "auth_password": "admin",
       "port": 22,
       "ssh_config_file": False,  # From global config (not set)
       # Then extras are merged:
       "auth_strict_key": False,
       "timeout_ops": 30,
       "ssh_config_file": "/etc/ssh/ssh_config.d/clab-evl3gw-dmac.conf",  # Overrides!
       "transport": "paramiko",
   }
   ```
7. **Scrapli connection** is created with these parameters
8. **ScrapliCfg wraps** the Scrapli connection
9. **Task executes** using the ScrapliCfg connection

---

## Key Takeaways

1. **Connection parameters are resolved hierarchically**: Host → Groups → Defaults → Host attributes

2. **`extras` dict is powerful**: Anything in `connection_options["scrapli"]["extras"]` is passed directly to Scrapli

3. **`extras` overrides global config**: If you set `ssh_config_file` in extras, it overrides the global Nornir SSH config

4. **Password can be set multiple ways**:
   - In inventory files (not recommended for security)
   - Via `nr.inventory.defaults.password = "..."` (runtime injection)
   - Via `connection_options["scrapli"]["extras"]["auth_password"]` (not recommended)

5. **Platform mapping happens automatically**: You can use "eos" and it becomes "arista_eos"

6. **ScrapliCfg reuses the Scrapli connection**: It doesn't create a new connection, it wraps the existing one

---

## Common Issues

### Issue: Password not being used

**Symptom**: Authentication fails even though password is set

**Possible Causes**:
1. Password is set at wrong level (e.g., only in host, but connection_options overrides it)
2. `extras` dict contains conflicting auth settings
3. SSH config file is being used instead of password auth
4. Transport type doesn't support password auth properly

**Solution**: Check the resolution order and ensure password is set at the right level

### Issue: SSH config file not being used

**Symptom**: Scrapli uses default SSH config instead of custom one

**Possible Causes**:
1. `ssh_config_file` is set in global Nornir config but not in `extras`
2. `extras` dict doesn't contain `ssh_config_file`

**Solution**: Set `ssh_config_file` in `connection_options["scrapli"]["extras"]` to override global config

### Issue: Platform not recognized

**Symptom**: `NornirScrapliInvalidPlatform` exception

**Possible Causes**:
1. Platform not set in inventory
2. Platform name is not in PLATFORM_MAP and not a valid Scrapli platform

**Solution**: Use a valid platform name or add mapping to PLATFORM_MAP

---

## Debugging Tips

1. **Enable Scrapli logging**:
   ```python
   import logging
   logging.basicConfig(filename="scrapli.log", level=logging.DEBUG)
   ```

2. **Print resolved parameters**:
   ```python
   conn_params = task.host.get_connection_parameters("scrapli")
   print(f"Hostname: {conn_params.hostname}")
   print(f"Username: {conn_params.username}")
   print(f"Password: {conn_params.password}")
   print(f"Platform: {conn_params.platform}")
   print(f"Extras: {conn_params.extras}")
   ```

3. **Check connection options at each level**:
   ```python
   print(f"Host connection_options: {task.host.connection_options}")
   for group in task.host.groups:
       print(f"Group {group.name} connection_options: {group.connection_options}")
   print(f"Defaults connection_options: {task.host.defaults.connection_options}")
   ```

4. **Verify password inheritance**:
   ```python
   print(f"Host password: {task.host.password}")
   print(f"Defaults password: {task.host.defaults.password}")
   ```
