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

### Multi-Vendor Lab
### VXLAN-EVPN 3-Stage Clos

## Getting Started

### Prerequisites

- [Containerlab](https://containerlab.dev/) installed
- Docker or Podman runtime
- Sufficient system resources for running multiple network containers

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

- Topology definitions use `.clab.yml` extension
- Device configurations stored in vendor-specific subdirectories
- Ansible inventory auto-generated for automation workflows

## License

See LICENSE file for details.
