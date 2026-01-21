# py_netauto

A Python package for network automation utilities, designed for use with Containerlab network topologies and multi-vendor network device management.

## TO-DO
-Fix scrpali_conifg_device commit workflow
    - I need to add an option to only diff and another one to push config.
    - When diffing the config, the config session needs to be closed
    - Check what error do you get back when the device can't allow any more config sessions to be created.
        - When you see that error, then create a workflow to delete all the config sessions.
- password from the env file is not working. Test this by removing the password from the defaults.yml file and only using the password comning from the env file
- Test that passwords are working from the env var and remove them from the groups or default vars
- Configure Leaf5 with scrapli. (Done)
- Use nornir-scrapli-cfg to push config (idempotent config replace)
    - Contuinue tshooting why pushing to leafe 5 won't work. I need to update second_auth. Before commiting (replace) I need to make sure I'm updating the template to reflect what containerlab pushes to the devices.
- Replace basedpyright by ty

## Overview

`py_netauto` provides a set of tools and utilities for network automation tasks, including:

- **Environment-based configuration management** using Pydantic settings
- **Nornir integration** with flexible initialization options
- **Configuration rendering** using Jinja2 templates
- **Network device inventory management**
- **Multi-vendor support** for network automation workflows

## Features

### 🔧 Configuration Management
- Environment variable-based configuration with `.env` file support
- Automatic path resolution (relative to project root or absolute)
- Pydantic validation for configuration settings
- Flexible Nornir initialization (config file or individual inventory files)

### 📋 Inventory Management
- Host listing and inventory exploration
- Support for Nornir SimpleInventory plugin
- Device role-based organization

### 🎨 Template Rendering
- Jinja2-based configuration template rendering
- Device role-specific templates (leaf, spine, host, default)
- Automated configuration file generation

## Quick Start

### 1. Environment Setup

Copy the example configuration:
```bash
cp .env.example .env
```

Customize settings for your lab environment:
```bash
# .env
NORNIR_BASE_PATH="clab/arista/dmac/evpn-vxlan-l3gw/nornir"
JINJA_TEMPLATES_FOLDER_PATH="${NORNIR_BASE_PATH}/templates"
GENERATED_CONFIGS_FOLDER_PATH="${NORNIR_BASE_PATH}/output"
```

### 2. Basic Usage

#### Initialize Nornir
```python
from py_netauto.utils.nornir_helpers import initialize_nornir

# Configuration loads automatically from environment
nr = initialize_nornir()
```

#### List Inventory Hosts
```python
from py_netauto.nornir_tasks.lists_hosts import main

# List all hosts in inventory
main()
```

#### Render Device Configurations
```python
from py_netauto.nornir_tasks.render_config import main

# Render configurations for all devices
main()
```

## Package Structure

```
py_netauto/
├── __init__.py
├── config.py                  # Environment-based configuration
├── utils/
│   ├── __init__.py
│   ├── inventory.py           # Inventory management utilities
│   └── nornir_helpers.py      # Nornir initialization helpers
└── nornir_tasks/
    ├── __init__.py
    ├── lists_hosts.py         # Host listing tasks
    └── render_config.py       # Configuration rendering tasks
```

## Configuration

### Environment Variables

All paths can be relative (to project root where `pyproject.toml` is located) or absolute. Variable substitution using `${VARIABLE_NAME}` syntax is supported.

| Variable | Description | Default |
|----------|-------------|---------|
| `NORNIR_BASE_PATH` | Base directory for Nornir project files | `configs/nornir` |
| `NORNIR_CONFIG_FILE_PATH` | Path to Nornir YAML configuration file (optional) | `None` |
| `JINJA_TEMPLATES_FOLDER_PATH` | Directory containing Jinja2 templates | `${NORNIR_BASE_PATH}/templates` |
| `GENERATED_CONFIGS_FOLDER_PATH` | Output directory for rendered configurations | `${NORNIR_BASE_PATH}/templates` |
| `NORNIR_INVENTORY_HOSTS_PATH` | Path to Nornir hosts inventory file | `${NORNIR_BASE_PATH}/inventory/hosts.yml` |
| `NORNIR_INVENTORY_GROUPS_PATH` | Path to Nornir groups inventory file | `${NORNIR_BASE_PATH}/inventory/groups.yml` |
| `NORNIR_INVENTORY_DEFAULTS_PATH` | Path to Nornir defaults inventory file | `${NORNIR_BASE_PATH}/inventory/defaults.yml` |

#### Configuration Modes

The package supports two configuration modes:

1. **Config File Mode**: Set `NORNIR_CONFIG_FILE_PATH` to use a single Nornir configuration file
2. **Individual Files Mode**: Leave `NORNIR_CONFIG_FILE_PATH` unset to use separate inventory files

#### Example Configuration

```bash
# .env file example

# Base path for your Nornir project
NORNIR_BASE_PATH="clab/arista/dmac/evpn-vxlan-l3gw/nornir"

# Template and output directories (using variable substitution)
JINJA_TEMPLATES_FOLDER_PATH="${NORNIR_BASE_PATH}/templates"
GENERATED_CONFIGS_FOLDER_PATH="${NORNIR_BASE_PATH}/output"

# Option 1: Use a single Nornir config file
# NORNIR_CONFIG_FILE_PATH="${NORNIR_BASE_PATH}/config.yml"

# Option 2: Use individual inventory files (default)
NORNIR_INVENTORY_HOSTS_PATH="${NORNIR_BASE_PATH}/inventory/hosts.yml"
NORNIR_INVENTORY_GROUPS_PATH="${NORNIR_BASE_PATH}/inventory/groups.yml"
NORNIR_INVENTORY_DEFAULTS_PATH="${NORNIR_BASE_PATH}/inventory/defaults.yml"
```

### Configuration Validation

Check your current configuration:
```bash
python -m py_netauto.config
```

This will display all resolved paths and validate your configuration.

## Template System

### Supported Device Roles

The package supports role-based template rendering:

- **leaf**: Uses `leaves.j2` template
- **spine**: Uses `spines.j2` template  
- **host**: Uses `hosts.j2` template
- **default**: Uses `defaults.j2` template (fallback)

### Template Location

Templates are stored in the configured templates directory (default: `configs/nornir/templates/`).

## Command Line Usage

### List Hosts
```bash
python -m py_netauto.nornir_tasks.lists_hosts
```

### Render Configurations
```bash
python -m py_netauto.nornir_tasks.render_config
```

### Verify Configuration
```bash
python -m py_netauto.config
```

## Integration with Containerlab

This package is designed to work seamlessly with Containerlab topologies:

1. **Auto-generated inventories**: Works with `ansible-inventory.yml` files generated by Containerlab
2. **Multi-vendor support**: Compatible with Nokia SR Linux, Arista cEOS, and Juniper vJunos devices
3. **Flexible configuration**: Adapts to different lab environments through environment variables

## Development

### Dependencies

- Python 3.12+
- Nornir 3.5+
- Pydantic Settings 2.12+
- Jinja2 (via nornir-jinja2)

### Code Style

This package follows Google-style docstrings and uses Ruff for linting and formatting. See the project's steering guidelines for detailed code style requirements.

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

### Using Config File Mode
```python
import os
# Use a single Nornir configuration file
os.environ['NORNIR_CONFIG_FILE_PATH'] = 'clab/arista/dmac/evpn-vxlan-l3gw/nornir/config.yml'

from py_netauto.utils.nornir_helpers import initialize_nornir
nr = initialize_nornir()
```

### Filtering Hosts by Role
```python
from py_netauto.utils.nornir_helpers import initialize_nornir

nr = initialize_nornir()

# Filter spine devices
spines = nr.filter(role="spine")
print(f"Found {len(spines.inventory.hosts)} spine devices")
```

## License

See the main project LICENSE file for details.