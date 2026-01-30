# Network Automation Lab & Tooling

A comprehensive network automation platform combining containerized lab environments with Python-based configuration management and validation tools.

## Overview

This repository provides:
- **Containerlab Topologies**: Multi-vendor network device simulation (Nokia SR Linux, Arista cEOS, Juniper vJunos)
- **VXLAN-EVPN Labs**: 3-stage Clos fabric architectures with L3 gateway scenarios
- **Python Automation Package** (`py_netauto`): Type-safe data models, configuration rendering, and device management
- **Pydantic Data Models**: Validated fabric configurations with computed fields and multiple export formats
- **Ansible Integration**: AVD-based configuration generation and deployment
- **Nornir Tasks**: Device configuration, template rendering, and operational tasks

## Use Cases

- Network architecture testing and validation
- Multi-vendor interoperability testing
- VXLAN-EVPN deployment scenarios (L2/L3 gateway, DMAC routing)
- Network automation development and testing
- Configuration template development with Jinja2
- Data model validation and export workflows
- Ansible playbook development for network devices

## Project Structure

```
├── py_netauto/                    # Python automation package
│   ├── datamodel/                 # Pydantic data models (NEW)
│   │   ├── device.py              # Device models with computed fields
│   │   ├── interface.py           # Interface configuration models
│   │   ├── network.py             # Network infrastructure models
│   │   ├── topology.py            # Fabric topology structure
│   │   ├── fabric.py              # Root fabric data model
│   │   └── FABRIC_ASN_DATAFLOW.md # ASN injection documentation
│   ├── cli/                       # CLI commands
│   │   └── commands/              # Command implementations
│   ├── nornir_tasks/              # Nornir task implementations
│   └── utils/                     # Helper utilities
│
├── clab/                          # Containerlab topologies
│   ├── arista/                    # Arista-specific labs
│   │   ├── avd/                   # Arista AVD-based deployments
│   │   │   └── evpn-vxlan-l3gw/   # L3 gateway EVPN-VXLAN topology
│   │   └── dmac/                  # DMAC routing scenarios
│   │       └── evpn-vxlan-l3gw/   # DMAC L3 gateway topology
│   ├── crb/                       # Campus/CRB topologies
│   ├── images/                    # Container images and vrnetlab
│   └── base-configs/              # Base configuration scripts
│
├── ansible/                       # Ansible automation
│   ├── collections/               # Installed collections (Arista AVD)
│   └── requirements.yml           # Collection dependencies
│
├── configs/                       # Configuration management
│   ├── nornir/                    # Nornir configuration
│   │   ├── config.yml             # Nornir settings
│   │   ├── inventory/             # Inventory files
│   │   ├── templates/             # Jinja2 templates
│   │   └── outputs/               # Generated configurations
│   ├── .ruff.toml                 # Python linting config
│   ├── .yamllint.yaml             # YAML linting rules
│   └── .yamlfmt.yaml              # YAML formatting rules
│
├── tests/                         # Test suite
│   └── unit/                      # Unit tests
│       ├── cli/                   # CLI command tests
│       └── datamodel/             # Data model tests (planned)
│
├── docs/                          # Documentation
│   ├── configuration.md           # Detailed configuration guide
│   └── tools/                     # Tool-specific documentation
│
└── .kiro/                         # Kiro specs and steering
    ├── specs/                     # Feature specifications
    │   └── fabric-datamodel-refactor/  # Data model refactor spec
    └── steering/                  # Project guidelines
```

## Key Features

### Pydantic Data Models (NEW)

Type-safe, validated network fabric configurations with automatic field computation:

- **Computed Fields**: Device roles, router IDs, VTEP IPs, interface descriptions, VRF assignments
- **Validation**: ASN ranges, IP addresses, hostname patterns, duplicate detection
- **Dependency Injection**: Fabric-wide ASN assignments injected into devices
- **Export Formats**: JSON, YAML, Python dict, CSV, Nornir inventory (planned)

**Example Usage**:
```python
from pathlib import Path
import yaml
from py_netauto.datamodel import FabricDataModel

# Load fabric configuration
yaml_path = Path("datamodel.yml")
with yaml_path.open() as f:
    data = yaml.safe_load(f)

fabric = FabricDataModel(**data)

# Access computed fields
for device in fabric.topology.spines:
    print(f"{device.hostname}: role={device.role}, asn={device.fabric_asn}")
```


### Containerlab Topologies

Multi-vendor network device simulation with realistic topologies:

- **Arista AVD**: Full EVPN-VXLAN deployments with Ansible AVD collection
- **DMAC Routing**: Distributed MAC routing scenarios
- **Multi-DC**: Cross-datacenter L3 gateway configurations
- **Auto-generated Inventories**: Ansible and Nornir inventories from topology files

### Network Automation

Python-based automation with Nornir and Ansible:

- **Configuration Rendering**: Jinja2 templates with device-specific data
- **Device Management**: Configuration push, backup, and validation
- **Operational Tasks**: Show commands, state collection, testing
- **CLI Interface**: `py-netauto` command-line tool (in development)

## Network Operating Systems

Supported network device images:

- **Nokia SR Linux**: `ghcr.io/nokia/srlinux`
- **Arista cEOS**: `ceos:4.33.1F`, `ceos:4.34.3.1M`, `ceos:4.35.0.1F`
- **Juniper vJunos Router**: `vrnetlab/juniper_vjunos-router:24.2R1-S2.5`
- **Juniper vJunos Switch**: `vrnetlab/juniper_vjunos-switch:23.2R1.14`, `vrnetlab/juniper_vjunos-switch:24.4R1.9`
- **Linux Hosts**: `aninchat/host:v1`

## Lab Topologies

### Arista EVPN-VXLAN L3 Gateway

**Location**: `clab/arista/avd/evpn-vxlan-l3gw/`

Full-featured EVPN-VXLAN deployment using Arista AVD:
- 2 datacenters (DC1, DC2)
- 2 spines + 4 leaves per DC
- Border leaves for inter-DC connectivity
- WAN router for external connectivity
- Ansible AVD-generated configurations

**Deploy**:
```bash
cd clab/arista/avd/evpn-vxlan-l3gw
sudo containerlab deploy -t topology.yaml
```

### DMAC EVPN-VXLAN L3 Gateway

**Location**: `clab/arista/dmac/evpn-vxlan-l3gw/`

Distributed MAC routing scenario:
- 2 spines + 5 leaves
- Pydantic data model-driven configuration
- Nornir-based configuration rendering
- Custom templates for DMAC routing

**Deploy**:
```bash
cd clab/arista/dmac/evpn-vxlan-l3gw
sudo containerlab deploy -t evl3gw.topology.yaml
```

### Juniper CRB Topology

**Location**: `clab/crb/`

Juniper vJunos switch fabric:
- 2 spines + 5 leaves
- Campus/CRB architecture
- Pre-configured startup configs

**Deploy**:
```bash
cd clab/crb
sudo containerlab deploy -t crb.clab.yaml
```

## Getting Started

### Prerequisites

- [Containerlab](https://containerlab.dev/) installed
- Docker or Podman runtime
- [Python UV](https://docs.astral.sh/uv/getting-started/installation/) for package management
- Sufficient system resources (8GB+ RAM recommended for multi-device labs)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd dmac-clab
   ```

2. **Install Python dependencies**:
   ```bash
   uv sync
   ```

3. **Install Ansible collections**:
   ```bash
   uv run ansible-galaxy collection install arista.avd -p ansible/collections --force
   ```

4. **Configure environment** (optional):
   ```bash
   cp .env.example .env
   # Edit .env to customize paths
   ```

### Quick Start

**Deploy a lab**:
```bash
# Arista AVD EVPN-VXLAN
cd clab/arista/avd/evpn-vxlan-l3gw
sudo containerlab deploy -t topology.yaml

# DMAC scenario
cd clab/arista/dmac/evpn-vxlan-l3gw
sudo containerlab deploy -t evl3gw.topology.yaml
```

**Inspect running labs**:
```bash
sudo containerlab inspect
```

**Access devices**:
```bash
# SSH to device (password: admin)
ssh admin@<device-ip>

# Execute command directly
sudo containerlab exec -t topology.yaml -n s1 -- Cli -c "show version"
```

**Destroy lab**:
```bash
sudo containerlab destroy -t topology.yaml
```

## Python Package (`py_netauto`)

### Data Models

The `py_netauto.datamodel` package provides Pydantic-based models for network fabric configuration:

**Models**:
- `FabricDataModel`: Root model with complete fabric configuration
- `Topology`: Spine and leaf device organization
- `Device`: Network device with computed fields (role, fabric_asn, router_id, vtep_ip)
- `Interface`: Network interface with IP addressing
- `ReservedSupernets`: IP address pool allocations
- `ManagementPool`: Management network configuration

**Computed Fields**:
- `Device.role`: Automatically determined from hostname (s* → spine, l* → leaf)
- `Device.fabric_asn`: Retrieved from fabric-wide ASN mapping via dependency injection
- `Device.router_id`: Extracted from Loopback0 IP (planned)
- `Device.vtep_ip`: Extracted from Loopback1 IP for leaves (planned)
- `Interface.description`: Auto-generated based on interface type and remote device (planned)
- `Interface.vrf`: Assigned based on interface name (Management0 → MGMT) (planned)

**Validation**:
- Hostname patterns: `s1-s8` for spines, `l1-l128` for leaves
- ASN ranges: 1-4294967295 (planned)
- IP address format validation (planned)
- Duplicate IP detection (planned)
- Remote device reference validation (planned)

**Example**:
```python
from py_netauto.datamodel import Device, Interface

# Create device with interfaces
device = Device(
    hostname="l1",
    interfaces=[
        Interface(name="Management0", ipv4="172.100.100.61/24"),
        Interface(name="Loopback0", ipv4="10.255.0.11/32"),
        Interface(name="Loopback1", ipv4="10.255.1.11/32"),
    ]
)

# Inject fabric ASNs (normally done by FabricDataModel)
device._fabric_asns = {"spines": 64600, "l1": 65001}

# Access computed fields
print(f"Role: {device.role}")           # "leaf"
print(f"ASN: {device.fabric_asn}")      # 65001
```

**Status**: Phase 1 (~35% complete) - See [`.kiro/specs/fabric-datamodel-refactor/tasks.md`](.kiro/specs/fabric-datamodel-refactor/tasks.md)

### CLI Commands (Planned)

```bash
# Validate data model
py-netauto datamodel validate fabric.yml

# Export to different formats
py-netauto datamodel export fabric.yml --format json
py-netauto datamodel export fabric.yml --format nornir --output-dir inventory/

# Show fabric information
py-netauto datamodel show fabric.yml --format table
```

### Nornir Tasks

Located in `py_netauto/nornir_tasks/`:
- `render_config.py`: Render Jinja2 templates with device data
- `scrapli_config_device.py`: Push configurations to devices
- `scrapli_get_device_info.py`: Collect device information
- `lists_hosts.py`: List and filter inventory hosts

## Naming Conventions

### Device Management IPs

Management IPs follow predictable patterns:
- **Spine devices**: `.101`, `.102`, etc.
- **Leaf devices**: `.11`, `.12`, `.13`, etc.
- **Host devices**: `.51`, `.52`, etc.

### Hostnames

- **Spines**: `s1` through `s8` (validated by data models)
- **Leaves**: `l1` through `l128` (validated by data models)
- Lowercase only, no leading zeros

### File Naming

- **Topology files**: `*.clab.yml` or `*.yaml`
- **Configuration files**: `*.cfg`, `*.txt`, or `*.yaml`
- **Templates**: `*.j2` for Jinja2 templates
- **Python modules**: lowercase with underscores

## Configuration Management

### Environment-Based Configuration

The project uses `.env` files for flexible configuration:

1. **Copy example configuration**:
   ```bash
   cp .env.example .env
   ```

2. **Customize settings**:
   ```bash
   # .env
   NORNIR_CONFIG_FILE_PATH=configs/nornir/config.yml
   ```

3. **Configuration loads automatically**:
   ```python
   from py_netauto.utils.nornir_helpers import initialize_nornir
   nr = initialize_nornir()  # Uses .env settings
   ```

**Priority**: `.env` file → Environment variables → Defaults

### Nornir Configuration

**Location**: `configs/nornir/`

- `config.yml`: Nornir settings (inventory plugin, logging, etc.)
- `inventory/hosts.yml`: Device inventory
- `inventory/groups.yml`: Group definitions
- `inventory/defaults.yml`: Default credentials
- `templates/`: Jinja2 configuration templates
- `outputs/`: Generated configurations

### Containerlab Configuration

- Topology definitions use `.clab.yml` or `.yaml` extension
- Device configurations stored in vendor-specific subdirectories
- Ansible inventory auto-generated for automation workflows
- Auto-generated files in `clab-<topology-name>/` directory

### Code Quality Tools

**Location**: `configs/`

- `.ruff.toml`: Python linting and formatting (120 char line length, Google docstrings)
- `.yamllint.yaml`: YAML validation rules
- `.yamlfmt.yaml`: YAML formatting configuration
- `.pre-commit-config.yaml`: Pre-commit hooks with prek

**Run checks**:
```bash
# Python
uv run ruff check .
uv run ruff format .

# YAML
uv run yamllint -c configs/.yamllint.yaml .
yamlfmt -conf configs/.yamlfmt.yaml .

# All pre-commit hooks
prek run --all-files
```

## Documentation

- **Configuration Guide**: [`docs/configuration.md`](docs/configuration.md) - Detailed configuration documentation
- **Data Flow**: [`py_netauto/datamodel/FABRIC_ASN_DATAFLOW.md`](py_netauto/datamodel/FABRIC_ASN_DATAFLOW.md) - ASN injection pattern
- **Nornir Flow**: [`docs/NORNIR_SCRAPLI_CONFIG_FLOW.md`](docs/NORNIR_SCRAPLI_CONFIG_FLOW.md) - Configuration push workflow
- **Tool Guides**: [`docs/tools/`](docs/tools/) - yamlfmt, yamllint, prek documentation

## Development

### Project Guidelines

Located in `.kiro/steering/`:
- `product.md`: Project purpose and use cases
- `structure.md`: Directory layout and naming conventions
- `tech.md`: Technology stack and common commands
- `code-style.md`: Python and YAML style guidelines

### Feature Specifications

Located in `.kiro/specs/`:
- `fabric-datamodel-refactor/`: Pydantic data model refactor (in progress)
  - `requirements.md`: User stories and acceptance criteria
  - `design.md`: Architecture and implementation details
  - `tasks.md`: Implementation task list with progress tracking

### Testing

```bash
# Run unit tests
uv run pytest

# Run with coverage
uv run pytest --cov=py_netauto

# Run specific test file
uv run pytest tests/unit/cli/test_filters.py
```

## Contributing

1. Follow code style guidelines in `.kiro/steering/code-style.md`
2. Run linting and formatting before committing
3. Add tests for new functionality
4. Update documentation as needed

## License

See LICENSE file for details.
