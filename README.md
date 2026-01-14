# Containerlab Network Topology Labs

This repository contains network topology labs built with Containerlab for testing and demonstrating multi-vendor network architectures, including VXLAN-EVPN deployments.

## Overview

Containerized network lab environments featuring:
- Multi-vendor network device simulation (Nokia SR Linux, Arista cEOS, Juniper vJunos)
- VXLAN-EVPN 3-stage Clos fabric topology
- Support for both virtual routers and switches
- Network automation and configuration management

## Use Cases

- Network architecture testing and validation
- Multi-vendor interoperability testing
- VXLAN-EVPN deployment scenarios
- Network automation practice

## Project Structure

```
clab/
├── clab-multivendor/          # Multi-vendor topology lab
│   ├── lab.clab.yml           # Main topology definition
│   ├── ansible-inventory.yml  # Auto-generated Ansible inventory
│   ├── ceos/                  # Arista cEOS specific files
│   ├── srl/                   # Nokia SR Linux specific files
│   ├── vjrouter/              # Juniper vJunos Router specific files
│   └── vjswitch/              # Juniper vJunos Switch specific files
│
└── vxlan-evpn/                # VXLAN-EVPN topology labs
    └── vxlan-evpn-3-stage.clab.yml  # 3-stage Clos fabric topology
```

## Network Operating Systems

- **Nokia SR Linux**: `ghcr.io/nokia/srlinux`
- **Arista cEOS**: `ceos:4.33.1F`
- **Juniper vJunos Router**: `vrnetlab/juniper_vjunos-router:24.2R1-S2.5`
- **Juniper vJunos Switch**: `vrnetlab/juniper_vjunos-switch:24.4R1.9` and `vrnetlab/vr-vjunosswitch:23.2R1.14`
- **Linux hosts**: `aninchat/host:v1`

## Lab Topologies


## Getting Started


### Prerequisites

- [Containerlab](https://containerlab.dev/) installed
- Docker or Podman runtime
- Sufficient system resources for running multiple network containers
- [Python UV](https://docs.astral.sh/uv/getting-started/installation/) installed


### Install project dependencies

```bash
uv sync

uv run ansible-galaxy collection install arista.avd -p ansible/collections --force

```

### Containerlab Commands

```bash
# Deploying a lab
sudo containerlab deploy -t clab/clab-multivendor/lab.clab.yml
sudo containerlab deploy -t clab/vxlan-evpn/vxlan-evpn-3-stage.clab.yml

# Inspecting Running Labs
sudo containerlab inspect

# Executing commands directly
sudo containerlab exec -t <topology-file>.clab.yml -n <node-name> -- <command>

# Destroying a Lab
sudo containerlab destroy -t <topology-file>.clab.yml
```

## General Conventions Conventions

### MGMT IP Conventions

Device management IPs follow predictable patterns:
- Spine devices: `.101`, `.102`, etc.
- Leaf devices: `.11`, `.12`, `.13`, etc.
- Host devices: `.51`, `.52`, etc.

## Configuration Management

### Containerlab Configuration

- Topology definitions use `.clab.yml` extension
- Device configurations stored in vendor-specific subdirectories
- Ansible inventory auto-generated for automation workflows

### Python Package Configuration

The `py_netauto` package uses environment-based configuration for flexibility across different environments.

#### Quick Start

1. **Copy the example configuration**:
   ```bash
   cp .env.example .env
   ```

2. **Customize settings** (optional):
   ```bash
   # .env
   NORNIR_CONFIG_FILE_PATH=configs/nornir/nornir.yaml
   ```

3. **Use the package**:
   ```python
   from py_netauto.utils.nornir_helpers import initialize_nornir
   
   # Configuration loads automatically
   nr = initialize_nornir()
   ```

#### Configuration Options

- **`NORNIR_CONFIG_FILE_PATH`**: Path to Nornir YAML configuration file
  - Default: `configs/nornir/nornir.yaml`
  - Supports relative (to project root) or absolute paths

#### How It Works

Configuration is loaded in this priority order:
1. `.env` file (if present)
2. System environment variables
3. Default values

The `.env` file is excluded from git to prevent committing sensitive settings.

📖 **For detailed configuration documentation, see [docs/configuration.md](docs/configuration.md)**

## License

See LICENSE file for details.
