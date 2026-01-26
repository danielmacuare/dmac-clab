# Network Configuration CLI

A command-line interface for the py_netauto package that provides an intuitive user experience for network device configuration management. The CLI supports configuration rendering, dry-run validation, and configuration deployment with sophisticated filtering capabilities.

## Features

- **Configuration Rendering**: Generate device configurations from Jinja2 templates
- **Dry-Run Validation**: Preview configuration changes before deployment
- **Safe Deployment**: Commit configurations with explicit confirmation
- **Advanced Filtering**: Target specific devices using Nornir's F() filter expressions
- **Session Management**: Detect and abort stale configuration sessions
- **Rich Output**: Color-coded results, tables, and syntax-highlighted diffs
- **Path Flexibility**: Override template and output directories at runtime

## Installation

The CLI is automatically installed with the py_netauto package:

```bash
# Install dependencies
uv sync

# Run the CLI
uv run py-netauto --help
```

## Quick Start

### 1. Render Configurations

Generate configuration files from Jinja2 templates:

```bash
# Render all devices
uv run py-netauto render

# Render only leaf devices
uv run py-netauto render --filter role=leaf

# Render with custom output directory
uv run py-netauto render --output-dir ./custom-configs
```

### 2. Preview Changes (Dry-Run)

Preview configuration changes without committing:

```bash
# Dry-run for all devices (default behavior)
uv run py-netauto push

# Dry-run for specific devices
uv run py-netauto push --filter "name=spine1|spine2"
```

### 3. Deploy Configurations

Commit configuration changes to devices:

```bash
# Commit with confirmation prompt
uv run py-netauto push --commit --filter role=leaf

# Commit without confirmation (use with caution!)
uv run py-netauto push --commit --force
```

### 4. Manage Sessions

List active configuration sessions:

```bash
# List sessions on all devices
uv run py-netauto sessions list

# List sessions on specific devices
uv run py-netauto sessions list --filter role=spine
```

Abort stale configuration sessions:

```bash
# Abort sessions on all devices
uv run py-netauto sessions abort

# Abort sessions on specific devices
uv run py-netauto sessions abort --filter role=spine
```

## Commands

### `render` - Render Configurations

Generate device configurations from Jinja2 templates.

**Usage:**
```bash
uv run py-netauto render [OPTIONS]
```

**Options:**
- `--filter, -f TEXT`: Filter devices (e.g., `role=leaf`, `name=spine1`)
- `--output-dir, -o PATH`: Override default output directory
- `--templates-dir, -t PATH`: Override default templates directory
- `--verbose, -v`: Enable verbose output

**Examples:**
```bash
# Render all devices
uv run py-netauto render

# Render leaf devices only
uv run py-netauto render --filter role=leaf

# Render with custom paths
uv run py-netauto render \
  --output-dir ./configs \
  --templates-dir ./templates

# Complex filtering: leaf devices named l1 or l2
uv run py-netauto render \
  --filter role=leaf \
  --filter "name=l1|l2"
```

### `push` - Push Configurations

Push configurations to network devices with dry-run or commit mode.

**Usage:**
```bash
uv run py-netauto push [OPTIONS]
```

**Options:**
- `--filter, -f TEXT`: Filter devices
- `--dry-run, -d`: Perform dry-run without committing (default: True)
- `--commit, -c`: Commit configuration changes to devices
- `--output-dir, -o PATH`: Override output directory path
- `--force`: Skip confirmation prompts
- `--verbose, -v`: Enable verbose output

**Examples:**
```bash
# Dry-run for all devices (safe, default behavior)
uv run py-netauto push

# Dry-run for specific devices
uv run py-netauto push --filter role=leaf

# Commit changes with confirmation
uv run py-netauto push --commit --filter "name=spine1|spine2"

# Commit without confirmation (dangerous!)
uv run py-netauto push --commit --force

# Use custom config directory
uv run py-netauto push --output-dir ./custom-configs
```

### `sessions list` - List Configuration Sessions

List all active configuration sessions on devices.

**Usage:**
```bash
uv run py-netauto sessions list [OPTIONS]
```

**Options:**
- `--filter, -f TEXT`: Filter devices
- `--verbose, -v`: Enable verbose output (shows raw command output)

**Examples:**
```bash
# List sessions on all devices
uv run py-netauto sessions list

# List sessions on specific devices
uv run py-netauto sessions list --filter role=leaf

# List with verbose output
uv run py-netauto sessions list --verbose
```

### `sessions abort` - Abort Configuration Sessions

Interactively abort configuration sessions on devices. The command first checks for active sessions, displays them, and offers options to abort all sessions or select specific ones.

**Usage:**
```bash
uv run py-netauto sessions abort [OPTIONS]
```

**Options:**
- `--filter, -f TEXT`: Filter devices
- `--force`: Skip confirmation prompts and abort all sessions
- `--verbose, -v`: Enable verbose output

**Interactive Workflow:**

1. **Check for sessions**: Automatically queries devices for active sessions
2. **Display sessions**: Shows all active sessions across filtered devices
3. **Choose action**:
   - Abort ALL sessions on all devices
   - Select specific sessions to abort (numbered list)
   - Cancel operation

**Examples:**
```bash
# Interactive abort (shows sessions and prompts for choice)
uv run py-netauto sessions abort

# Interactive abort on specific devices
uv run py-netauto sessions abort --filter role=leaf

# Force mode: abort all sessions without prompts
uv run py-netauto sessions abort --force

# Verbose mode: show detailed session information
uv run py-netauto sessions abort --verbose
```

**Sample Interactive Session:**
```
Active Configuration Sessions:

📋 l1: 2 session(s)
   • DMAC-L1 - pending
   • SMAC-L1 - pending

Total: 2 session(s) across 1 device(s)

What would you like to do?
  [1] Abort ALL sessions on all devices
  [2] Select specific sessions to abort
  [3] Cancel

Enter your choice [3]: 2

Select sessions to abort:

#    Device    Session Name    Status
1    l1        DMAC-L1         pending
2    l1        SMAC-L1         pending

Sessions to abort: 1

⚠ WARNING: About to abort 1 session(s)
   • l1: DMAC-L1

Proceed with abort? [y/n]: y

Session Abort Results:

✓ l1 (DMAC-L1): Aborted successfully
```

## Filtering

The CLI supports sophisticated device filtering using Nornir's F() filter expressions.

### Filter Syntax

- **Simple filter**: `key=value`
- **OR operation**: Use pipe `|` within a filter value
- **AND operation**: Use multiple `--filter` flags

### Filter Examples

**Simple Filters:**
```bash
# Single attribute filter
uv run py-netauto render --filter role=leaf

# Filter by name
uv run py-netauto push --filter name=spine1

# Filter by platform
uv run py-netauto render --filter platform=arista_eos
```

**OR Operations (pipe within filter):**
```bash
# Devices that are EITHER leaf OR spine
uv run py-netauto render --filter "role=leaf|spine"

# Devices named EITHER l1 OR l2 OR l3
uv run py-netauto push --filter "name=l1|l2|l3"
```

**AND Operations (multiple filters):**
```bash
# Devices that are BOTH leaf role AND named l1
uv run py-netauto render --filter role=leaf --filter name=l1

# Leaf devices in DC1 group with arista platform
uv run py-netauto push \
  --filter role=leaf \
  --filter group=DC1 \
  --filter platform=arista_eos
```

**Complex Combinations (AND + OR):**
```bash
# Leaf devices that are named l1 OR l2
uv run py-netauto render \
  --filter role=leaf \
  --filter "name=l1|l2"

# Devices that are (leaf OR spine) AND arista platform
uv run py-netauto push \
  --filter "role=leaf|spine" \
  --filter platform=arista_eos

# Devices in DC1 that are (leaf OR spine) AND named (l1 OR s1)
uv run py-netauto render \
  --filter group=DC1 \
  --filter "role=leaf|spine" \
  --filter "name=l1|s1"
```

### Supported Filter Attributes

You can filter by any attribute in your Nornir inventory:

- `role`: Device role (e.g., `leaf`, `spine`, `host`)
- `name`: Device hostname
- `platform`: Device platform (e.g., `arista_eos`, `nokia_srl`, `juniper_junos`)
- `group`: Device group (e.g., `DC1_LEAVES`, `DC2_SPINES`)
- Any custom host attribute defined in your inventory

## Path Overrides

Override default paths for templates and output directories:

### Output Directory Override

```bash
# Use custom output directory for rendered configs
uv run py-netauto render --output-dir ./my-configs

# Push from custom config directory
uv run py-netauto push --output-dir ./my-configs
```

### Templates Directory Override

```bash
# Use custom templates directory
uv run py-netauto render --templates-dir ./my-templates
```

### Path Resolution

- **Absolute paths**: Used as-is
- **Relative paths**: Resolved from project root
- **Default paths**: From environment variables or config

## Workflows

### Standard Workflow

1. **Render configurations**:
   ```bash
   uv run py-netauto render --filter role=leaf
   ```

2. **Preview changes (dry-run)**:
   ```bash
   uv run py-netauto push --filter role=leaf
   ```

3. **Review diffs and commit**:
   ```bash
   uv run py-netauto push --commit --filter role=leaf
   ```

### Troubleshooting Workflow

If devices have stale sessions:

1. **List active sessions**:
   ```bash
   uv run py-netauto sessions list --filter role=leaf
   ```

2. **Interactively abort sessions**:
   ```bash
   # Interactive mode: choose which sessions to abort
   uv run py-netauto sessions abort --filter role=leaf
   
   # Or force mode: abort all sessions immediately
   uv run py-netauto sessions abort --filter role=leaf --force
   ```

3. **Retry push operation**:
   ```bash
   uv run py-netauto push --commit --filter role=leaf
   ```

## Output

The CLI provides rich, color-coded output:

- **Device Lists**: Tables showing filtered devices with hostname, role, and platform
- **Configuration Diffs**: Syntax-highlighted diffs showing additions and deletions
- **Operation Summaries**: Statistics showing total devices, successes, and failures
- **Error Messages**: Clear error messages with actionable guidance

## Safety Features

- **Dry-run by default**: Push operations default to dry-run mode
- **Explicit confirmation**: Commit operations require confirmation (unless `--force`)
- **Graceful degradation**: Continue with remaining devices if some fail
- **Clear warnings**: Bold warnings for destructive operations
- **Exit codes**: Non-zero exit codes on failure for scripting

## Error Handling

The CLI provides clear error messages with actionable guidance:

### Invalid Filter Syntax
```
❌ Invalid filter syntax: Missing '=' in filter expression 'roleleaf'

Valid filter format: key=value

Examples:
  --filter role=leaf
  --filter 'role=leaf|spine'
  --filter role=leaf --filter name=l1
```

### Missing Configuration Files
```
❌ Error: No configuration files (*.cfg) found in output directory: ./configs

Tip: Run 'py-netauto render' first to generate configuration files
```

### Path Errors
```
❌ Path error: Templates directory not found: ./templates

Tip: Use --templates-dir to specify a different path
```

## Environment Configuration

The CLI respects environment variables from `.env`:

- `NORNIR_CONFIG_PATH`: Path to Nornir configuration file
- `JINJA_TEMPLATES_FOLDER_PATH`: Default templates directory
- `GENERATED_CONFIGS_FOLDER_PATH`: Default output directory

## Supported Platforms

- **Arista EOS**: Full support for configuration management and session handling

**Note**: Session management (list and abort) is currently only implemented for Arista EOS devices. Configuration rendering and push operations work with any platform supported by nornir-scrapli.

## Troubleshooting

### Command Not Found

If `py-netauto` command is not found, use `uv run`:

```bash
uv run py-netauto --help
```

### No Devices Match Filter

Check your filter syntax and inventory:

```bash
# List all devices (no filter)
uv run py-netauto render --verbose

# Check filter syntax
uv run py-netauto render --filter role=leaf --verbose
```

### Permission Errors

Ensure output directory is writable:

```bash
# Use custom output directory
uv run py-netauto render --output-dir ~/configs
```

### Connection Failures

Enable verbose mode for detailed error messages:

```bash
uv run py-netauto push --verbose
```

### Too Many Open Sessions

List sessions to see what's active:

```bash
uv run py-netauto sessions list
```

Abort stale sessions before pushing:

```bash
uv run py-netauto sessions abort
```

## Advanced Usage

### Scripting

Use exit codes for scripting:

```bash
#!/bin/bash

# Render configurations
if uv run py-netauto render --filter role=leaf; then
    echo "Render successful"
    
    # Dry-run
    if uv run py-netauto push --filter role=leaf; then
        echo "Dry-run successful, ready to commit"
        
        # Commit with force (no confirmation)
        uv run py-netauto push --commit --force --filter role=leaf
    fi
fi
```

### Batch Operations

Process multiple device groups:

```bash
# Render all device types
for role in leaf spine host; do
    echo "Rendering $role devices..."
    uv run py-netauto render --filter role=$role
done
```

### Custom Paths

Use different template sets:

```bash
# Production templates
uv run py-netauto render \
  --templates-dir ./templates/production \
  --output-dir ./configs/production

# Staging templates
uv run py-netauto render \
  --templates-dir ./templates/staging \
  --output-dir ./configs/staging
```

## Contributing

When adding new CLI commands:

1. Create command module in `py_netauto/cli/commands/`
2. Follow Google-style docstrings
3. Include usage examples in docstrings
4. Add comprehensive error handling
5. Register command in `py_netauto/cli/__init__.py`
6. Update this README

## See Also

- [Nornir Documentation](https://nornir.readthedocs.io/)
- [Nornir Filtering Deep Dive](https://nornir.readthedocs.io/en/latest/howto/filtering_deep_dive.html)
- [Typer Documentation](https://typer.tiangolo.com/)
- [Rich Documentation](https://rich.readthedocs.io/)
