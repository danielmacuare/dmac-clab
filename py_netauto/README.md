
# py_netauto

A Python package for network automation utilities, designed for use with Containerlab network topologies and multi-vendor network device management.

## Overview

`py_netauto` provides a comprehensive set of tools and utilities for network automation tasks, including:

- **Pydantic Data Models** for fabric configuration validation and management
- **CLI Commands** for rendering, pushing, validating, and exporting network configurations
- **Environment-based configuration management** using Pydantic settings
- **Nornir integration** with flexible initialization options
- **Configuration rendering** using Jinja2 templates
- **Multi-vendor support** for network automation workflows

## Features

### 🏗️ Fabric Data Models
- **Pydantic-based validation** for network fabric configurations
- **Computed fields** for automatic router ID, VTEP IP, and ASN assignment
- **JSON Schema export** with examples for API documentation
- **Multi-format export** (JSON, YAML, JSON Schema, Python dict)

### 🔧 Configuration Management
- **Environment variable-based configuration** with `.env` file support
- **Automatic path resolution** (relative to project root or absolute)
- **Pydantic validation** for configuration settings
- **Flexible Nornir initialization** (config file or individual inventory files)

### 📋 Network Operations
- **Configuration rendering** from Jinja2 templates
- **Configuration deployment** to network devices (dry-run and commit modes)
- **Session management** for network device configuration sessions
- **Device filtering** with flexible filter expressions

### 🌐 Multi-vendor Support
- **Nokia SR Linux**, **Arista cEOS**, and **Juniper vJunos** devices
- **Containerlab integration** with auto-generated inventories
- **Role-based configuration** (spine, leaf, host templates)

## Quick Start

### 1. Environment Setup

```bash
# Activate virtual environment (once per session)
source .venv/bin/activate

# Install dependencies
uv sync
```

Copy the example configuration:
```bash
cp .env.example .env
```

### 2. CLI Commands

#### Data Model Operations
```bash
# Validate a fabric data model
py-netauto datamodel validate fabric.yml --verbose

# Export to different formats
py-netauto datamodel export fabric.yml --format json --output fabric.json
py-netauto datamodel export fabric.yml --format yaml --pretty
py-netauto datamodel export fabric.yml --format json-schema --output schema.json
py-netauto datamodel export fabric.yml --format python  # prints to stdout
```

#### Configuration Management
```bash
# Render device configurations from templates
py-netauto render --filter role=leaf --verbose

# Push configurations (dry-run by default)
py-netauto push --filter role=spine --dry-run

# Commit configurations to devices
py-netauto push --filter name=leaf1 --commit --verbose
```

#### Session Management
```bash
# List active configuration sessions
py-netauto sessions list

# Abort all pending sessions
py-netauto sessions abort
```

### 3. Python API Usage

#### Initialize Nornir
```python
from py_netauto.utils.nornir_helpers import initialize_nornir

# Configuration loads automatically from environment
nr = initialize_nornir()
```

#### Work with Data Models
```python
from py_netauto.datamodel import load_fabric

# Load and validate fabric data model
fabric = load_fabric("fabric.yml")

# Access computed fields
for device in fabric.topology.spines:
    print(f"Device: {device.hostname}, ASN: {device.fabric_asn}, Router ID: {device.router_id}")
```

## CLI Command Reference

### Main Commands

| Command | Description | Example |
|---------|-------------|---------|
| `render` | Render device configurations from Jinja2 templates | `py-netauto render --filter role=leaf -v` |
| `push` | Push configurations to network devices (dry-run by default) | `py-netauto push --filter name=spine1 --commit` |
| `sessions` | Manage configuration sessions on devices | `py-netauto sessions list` |
| `datamodel` | Fabric data model validation and export | `py-netauto datamodel validate fabric.yml` |

### Data Model Commands

| Command | Description | Options |
|---------|-------------|---------|
| `datamodel validate` | Validate fabric data model file | `--strict`, `--show-warnings`, `--verbose` |
| `datamodel export` | Export to various formats | `--format`, `--output`, `--pretty`, `--verbose` |

### Available Export Formats

| Format | Description | Output | Example |
|--------|-------------|--------|---------|
| `json` | JSON with computed fields | File or stdout | `--format json --output fabric.json` |
| `yaml` | YAML with computed fields | File or stdout | `--format yaml --pretty` |
| `json-schema` | JSON Schema for API documentation | File or stdout | `--format json-schema --output schema.json` |
| `python` | Python dictionary representation | Stdout only | `--format python` |

*Coming soon: `csv`, `nornir`*

### Render Command Options

| Option | Short | Description | Example |
|--------|-------|-------------|---------|
| `--filter` | `-f` | Filter devices by role or name | `--filter role=leaf` |
| `--output-dir` | `-o` | Override output directory | `--output-dir /tmp/configs` |
| `--templates-dir` | `-t` | Override templates directory | `--templates-dir custom/templates` |
| `--verbose` | `-v` | Enable verbose output | `-v` |

### Push Command Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--filter` | `-f` | Filter devices by role or name | All devices |
| `--dry-run` | `-d` | Explicitly enable dry-run mode | Enabled |
| `--commit` | `-c` | Commit configuration changes | Disabled |
| `--output-dir` | `-o` | Override output directory | From config |
| `--force` |  | Skip confirmation prompts | Disabled |
| `--verbose` | `-v` | Enable verbose output | Disabled |

### Filter Expressions

Use flexible filtering for device selection:

```bash
# Single filter by role
py-netauto render --filter role=leaf

# Single filter by name
py-netauto push --filter name=spine1 --commit

# Multiple filters (AND logic)
py-netauto render --filter role=spine,name=spine1

# OR filters (use pipe character)
py-netauto render --filter 'role=leaf|spine'
```

## Package Structure

```
py_netauto/
├── __init__.py
├── config.py                  # Environment-based configuration
├── datamodel/                 # Pydantic data models
│   ├── device.py             # Device and interface models
│   ├── fabric.py             # Root fabric data model
│   ├── network.py            # Network infrastructure models
│   ├── topology.py           # Topology structure models
│   ├── loaders.py            # Data loading utilities
│   └── exporters/            # Export functionality
│       ├── json_exporter.py
│       ├── yaml_exporter.py
│       └── json_schema_exporter.py
├── cli/                      # CLI commands
│   ├── __init__.py
│   └── commands/
│       ├── datamodel.py      # Data model CLI commands
│       ├── render.py         # Configuration rendering
│       ├── push.py           # Configuration deployment
│       └── sessions.py       # Session management
├── utils/
│   ├── nornir_helpers.py     # Nornir initialization helpers
│   └── debug_inventory.py    # Inventory debugging utilities
└── nornir_tasks/
    ├── lists_hosts.py        # Host listing tasks
    ├── render_config.py      # Configuration rendering tasks
    └── scrapli_config_device.py  # Device configuration tasks
```

## Configuration

### Environment Variables

All paths can be relative (to project root where `pyproject.toml` is located) or absolute. Variable substitution using `${VARIABLE_NAME}` syntax is supported.

| Variable | Description | Default |
|----------|-------------|---------|
| `NORNIR_BASE_PATH` | Base directory for Nornir project files | `configs/nornir` |
| `NORNIR_CONFIG_FILE_PATH` | Path to Nornir YAML configuration file (optional) | `None` |
| `JINJA_TEMPLATES_FOLDER_PATH` | Directory containing Jinja2 templates | `${NORNIR_BASE_PATH}/templates` |
| `GENERATED_CONFIGS_FOLDER_PATH` | Output directory for rendered configurations | `${NORNIR_BASE_PATH}/outputs` |
| `NORNIR_INVENTORY_HOSTS_PATH` | Path to Nornir hosts inventory file | `${NORNIR_BASE_PATH}/inventory/hosts.yml` |
| `NORNIR_INVENTORY_GROUPS_PATH` | Path to Nornir groups inventory file | `${NORNIR_BASE_PATH}/inventory/groups.yml` |
| `NORNIR_INVENTORY_DEFAULTS_PATH` | Path to Nornir defaults inventory file | `${NORNIR_BASE_PATH}/inventory/defaults.yml` |

### Configuration Validation

Check your current configuration:
```bash
python -m py_netauto.config
```

This will display all resolved paths and validate your configuration.

## Data Model Features

### Computed Fields

The data models automatically compute important network parameters:

- **Device Role**: Automatically determined from hostname (s1-s8 = spine, l1-l128 = leaf)
- **Router ID**: Extracted from Loopback0 interface IP address
- **VTEP IP**: Extracted from Loopback1 interface IP address (leaf devices only)
- **Fabric ASN**: BGP ASN assignment based on device role and fabric mapping
- **Interface Descriptions**: Auto-generated based on interface type and connectivity

### Validation Features

- **Hostname validation**: Enforces naming conventions (s1-s8, l1-l128)
- **IP uniqueness**: Ensures no duplicate IP addresses across the fabric
- **Pool allocation**: Validates IPs are within designated pools
- **Remote device references**: Verifies all remote_device references exist
- **Required interfaces**: Ensures Loopback0 (all devices) and Loopback1 (leaves) exist

### Example Data Model

```yaml
schema_version: "1.0.1"
fabric_name: "dc1-fabric"
mgmt_vrf: "MGMT"
fabric_asns:
  spines: 64600
  l1: 65001
  l2: 65002
topology:
  spines:
    - hostname: s1
      interfaces:
        - name: Loopback0
          ipv4: 10.255.0.1/32
        - name: Ethernet1
          ipv4: 10.254.1.0/31
          remote_device: l1
  leaves:
    - hostname: l1
      interfaces:
        - name: Loopback0
          ipv4: 10.255.0.11/32
        - name: Loopback1
          ipv4: 10.255.1.11/32
```

## Integration with Containerlab

This package is designed to work seamlessly with Containerlab topologies:

1. **Auto-generated inventories**: Works with `ansible-inventory.yml` files generated by Containerlab
2. **Multi-vendor support**: Compatible with Nokia SR Linux, Arista cEOS, and Juniper vJunos devices
3. **Flexible configuration**: Adapts to different lab environments through environment variables
4. **Template system**: Role-based templates for different device types

## Development

### Dependencies

- Python 3.12+
- Nornir 3.5+
- Pydantic Settings 2.12+
- Typer 0.15+ (CLI framework)
- Rich 13.0+ (CLI formatting)
- Jinja2 (via nornir-jinja2)

### Code Style

This package follows Google-style docstrings and uses Ruff for linting and formatting. See `AGENTS.md` for detailed development guidelines.

## Examples

### Custom Configuration Path
```python
import os
# Set base path for a specific lab
os.environ['NORNIR_BASE_PATH'] = 'clab/arista/dmac/evpn-vxlan-l3gw/nornir'
os.environ['JINJA_TEMPLATES_FOLDER_PATH'] = '${NORNIR_BASE_PATH}/templates'

from py_netauto.utils.nornir_helpers import initialize_nornir
nr = initialize_nornir()
```

### Working with Data Models
```python
from py_netauto.datamodel import load_fabric
from py_netauto.datamodel.exporters import export_json, export_yaml

# Load fabric data model
fabric = load_fabric("fabric.yml")

# Export to different formats
export_json(fabric, "fabric.json", pretty=True)
export_yaml(fabric, "fabric.yaml", pretty=True)

# Access computed fields
for device in fabric.topology.leaves:
    print(f"Leaf {device.hostname}: VTEP IP = {device.vtep_ipv4}")
```

### CLI Automation Examples
```bash
# Validate and export data model
py-netauto datamodel validate fabric.yml --verbose --strict
py-netauto datamodel export fabric.yml --format json-schema --output api-schema.json

# Render configurations for specific devices
py-netauto render --filter role=leaf --output-dir /tmp/configs --verbose

# Deploy configurations with dry-run first, then commit
py-netauto push --filter name=spine1 --dry-run --verbose
py-netauto push --filter name=spine1 --commit --verbose

# Export to multiple formats
py-netauto datamodel export fabric.yml --format json --output fabric.json --pretty
py-netauto datamodel export fabric.yml --format yaml --output fabric.yaml --pretty
py-netauto datamodel export fabric.yml --format python  # prints to stdout
```

## License

See the main project LICENSE file for details.