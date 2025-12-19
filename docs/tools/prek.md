# prek

`prek` is a faster, Rust-based alternative to pre-commit that manages git hooks and tool dependencies automatically. It provides better performance, automatic tool installation, and full compatibility with existing pre-commit configurations.

## Links
- Main repo: https://github.com/j178/prek
- Documentation: https://prek.j178.dev/
- Latest Releases: https://github.com/j178/prek/releases

## Why prek over pre-commit?

- **Faster execution**: Built in Rust for better performance
- **Automatic tool management**: No need to manually install yamlfmt, yamllint, ruff, etc.
- **Zero dependencies**: Single binary with no Python/Node.js requirements
- **Full compatibility**: Drop-in replacement for existing `.pre-commit-config.yaml` files
- **Better user experience**: Improved error messages and progress indicators

## Installation

### Standalone installer (Recommended)
```bash
# Linux/macOS
curl -LsSf https://prek.j178.dev/install.sh | sh

# Windows (PowerShell)
irm https://prek.j178.dev/install.ps1 | iex
```

### Using pip/uv
```bash
# Using uv (recommended)
uv tool install prek

# Using pip
pip install prek

# Using pipx
pipx install prek
```

### Using package managers
```bash
# Homebrew (macOS/Linux)
brew install j178/tap/prek

# Cargo
cargo install prek

# npm
npm install -g prek
```

## Basic Usage

### Install git hooks
```bash
# Install prek git hooks (replaces pre-commit install)
prek install
```

### Run hooks manually
```bash
# Run on all files
prek run --all-files

# Run on staged files only
prek run

# Run specific hooks
prek run yamlfmt ruff

# List available hooks
prek list
```

### Update hook versions
```bash
# Auto-update to latest versions
prek auto-update
```

## Configuration

prek uses the same `.pre-commit-config.yaml` configuration file as pre-commit. Our project configuration includes:

- **yamlfmt**: YAML formatting with custom config at `configs/.yamlfmt.yaml`
- **yamllint**: YAML linting with custom config at `configs/.yamllint.yaml` 
- **ruff**: Python linting and formatting with config at `configs/.ruff.toml`

### Key differences from pre-commit

1. **No `language: system` needed**: prek automatically manages tool installation
2. **Faster execution**: Rust-based implementation with built-in optimizations
3. **Better dependency management**: Uses uv for Python tools, automatic Go/Rust toolchain management
4. **Workspace mode**: Can handle multiple projects in a single repository

## Migration from pre-commit

The migration is seamless:

1. **Install prek** using one of the methods above
2. **Uninstall pre-commit hooks**: `pre-commit uninstall` (if previously installed)
3. **Install prek hooks**: `prek install`
4. **Configuration**: No changes needed - existing `.pre-commit-config.yaml` works as-is

## Environment Variables

- `PREK_HOME`: Override prek data directory (default: `~/.cache/prek`)
- `PREK_SKIP`: Skip specific hooks (e.g., `PREK_SKIP=yamlfmt,ruff`)
- `PREK_COLOR`: Control colored output (`auto`, `always`, `never`)
- `PREK_NO_CONCURRENCY`: Disable parallel execution

## Troubleshooting

### Tool installation issues
prek automatically installs and manages tools. If you encounter issues:

```bash
# Clear prek cache
prek cache clean

# Reinstall hooks
prek install --force
```

### Performance optimization
```bash
# Use built-in fast hooks when available
export PREK_NO_FAST_PATH=false

# Enable parallel execution (default)
unset PREK_NO_CONCURRENCY
```

## Integration with CI/CD

### GitHub Actions
```yaml
- name: Run prek
  uses: j178/prek-action@v1
  with:
    version: latest
```

### Manual CI setup
```bash
# Install prek
curl -LsSf https://prek.j178.dev/install.sh | sh

# Run hooks
prek run --all-files
```