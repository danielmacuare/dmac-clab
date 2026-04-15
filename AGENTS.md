# AGENTS.md - AI Coding Agent Guidelines

This document provides essential information for AI coding agents working in this repository.

## Project Overview

Python network automation platform for Containerlab environments. Uses Pydantic data models,
Nornir tasks, and Jinja2 templates to manage multi-vendor network fabrics (Arista, Nokia, Juniper).

## Build/Lint/Test Commands

### Environment Setup
```bash
uv sync                           # Install all dependencies
uv run ansible-galaxy collection install arista.avd -p ansible/collections --force
```

### Python Virtual Environment

**CRITICAL: Always activate the virtual environment before running Python commands**

**IMPORTANT: Virtual environment activation persists for the entire terminal session. You only need to activate once per session, not before every command.**

```bash
# Activate virtual environment ONCE per terminal session
source .venv/bin/activate

# Then use standard Python commands normally (no need to reactivate)
python script.py                 # Run Python scripts
python -m module                 # Run Python modules  
python -c "import x"             # Run Python code
pip install package              # Install packages
py-netauto --help                # CLI commands
```

**Command Pattern for AI Agents:**

**Step 1: Activate virtual environment ONCE per session**
```bash
source .venv/bin/activate
```

**Step 2: Run multiple Python commands without reactivating**
```bash
# Running Python scripts
python py_netauto/datamodel/static_tests/main.py

# Running tests  
python -m pytest

# Checking imports
python -c "from py_netauto.datamodel import Device; print('✅ Import successful')"

# Running CLI commands
py-netauto --help
py-netauto datamodel validate fabric.yml
py-netauto render --help

# Running linting
ruff check .
```

**DO NOT use:**
- `source .venv/bin/activate && command` repeatedly (wasteful)
- `python` or `python3` without activating virtual environment first
- System Python (missing project dependencies)

### Linting and Formatting
```bash
# Activate virtual environment ONCE per session
source .venv/bin/activate

# Then run multiple linting commands
ruff check .                      # Check for linting issues
ruff check --fix .                # Auto-fix linting issues  
ruff format .                     # Format Python code

# Alternative: UV wrapper (when activation not preferred)
uv run ruff check .               # Check for linting issues
uv run ruff check --fix .         # Auto-fix linting issues
uv run ruff format .              # Format Python code
uv run ty check                   # Type checking
uv run yamllint -c configs/.yamllint.yaml .   # YAML linting
yamlfmt -conf configs/.yamlfmt.yaml .         # YAML formatting
prek run --all-files              # Run all pre-commit hooks
```

### Testing
```bash
# Activate virtual environment ONCE per session
source .venv/bin/activate

# Then run multiple test commands
python -m pytest                              # Run all tests
python -m pytest --cov=py_netauto             # Run with coverage
python -m pytest tests/unit/cli/test_filters.py                    # Run single test file
python -m pytest tests/unit/cli/test_filters.py::TestParseFilters  # Run single test class
python -m pytest tests/unit/cli/test_filters.py::TestParseFilters::test_single_filter  # Single test
python -m pytest -k "test_valid"              # Run tests matching pattern
python -m pytest -m unit                      # Run only unit tests (marker)
python -m pytest -m integration               # Run only integration tests (marker)

# Alternative: UV wrapper
uv run pytest                              # Run all tests
uv run pytest --cov=py_netauto             # Run with coverage
uv run pytest tests/unit/cli/test_filters.py                    # Run single test file
uv run pytest tests/unit/cli/test_filters.py::TestParseFilters  # Run single test class
uv run pytest tests/unit/cli/test_filters.py::TestParseFilters::test_single_filter  # Single test
uv run pytest -k "test_valid"              # Run tests matching pattern
uv run pytest -m unit                      # Run only unit tests (marker)
uv run pytest -m integration               # Run only integration tests (marker)
```

## Code Style Guidelines

### Python Version & Type Hints
- **Minimum**: Python 3.12+
- Use built-in generics: `list[str]`, `dict[str, int]`, `tuple[int, ...]`
- Use union operator: `str | None` instead of `Optional[str]`
- **Never** import from `typing` module for basic types

### Formatting Rules
- **Line length**: 120 characters
- **Quotes**: Double quotes (like Black)
- **Indentation**: 4 spaces
- **Trailing commas**: Required in multi-line structures

### Import Organization (isort)
```python
# 1. Standard library
from pathlib import Path

# 2. Third-party packages
from pydantic import BaseModel, Field

# 3. Local/first-party (py_netauto)
from py_netauto.datamodel import Device
```

### Docstrings (Google Style)
```python
def example_function(param1: str, param2: int = 0) -> bool:
    """
    Brief one-line summary (imperative mood, no period).

    Longer description if needed.

    Args:
        param1: Description of first parameter.
        param2: Description with default. Defaults to 0.

    Returns:
        Description of return value.

    Raises:
        ValueError: When this exception is raised.
    """
```

### Naming Conventions
- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/Methods**: `snake_case`
- **Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private attributes**: `_single_underscore`
- **Device hostnames**: `s1-s8` (spines), `l1-l128` (leaves)

### Error Handling
- Use specific exception types, not bare `except:`
- Provide clear error messages with context
- Document raised exceptions in docstrings
- Use `raise ValueError(msg) from None` to suppress exception chaining when appropriate

### Path Handling
- Use `pathlib.Path` instead of `os.path`
- Resolve paths relative to project root
- Support both absolute and relative paths

### Linting Suppressions
- **NEVER** add `# noqa` comments without explicit user approval
- Prefer fixing the underlying issue over suppressing warnings
- If suppression is truly needed, explain why and get approval first

## Key Ruff Rules Enabled

| Category | Rules | Purpose |
|----------|-------|---------|
| Style | E, W, N | PEP8 errors, warnings, naming |
| Import | I, ICN | isort, import conventions |
| Docs | D | Pydocstyle (Google convention) |
| Security | S, BLE | Bandit security, blind except |
| Bugs | B, C90 | Bugbear patterns, complexity |
| Modern | UP, FA | Pyupgrade, future annotations |
| Quality | SIM, PERF, FURB | Simplification, performance |
| Tests | PT | Pytest style |

### Ignored Rules
- `E501`: Line too long (formatter handles this)
- `D1`: Missing docstrings (not required everywhere)
- `FBT003`: Boolean positional args (acceptable)
- `TRY003`, `EM101`: Exception message style (too restrictive)

### Test File Exceptions
Test files (`test_*.py`) are exempt from: `S101` (assert), `D` (docstrings),
`ARG001` (unused args for fixtures), `PLR2004` (magic values)

## Project Structure

```
py_netauto/              # Main Python package
├── datamodel/           # Pydantic models (Device, Interface, Fabric)
├── cli/                 # Typer CLI commands
├── nornir_tasks/        # Nornir task implementations
└── utils/               # Helper utilities

tests/unit/              # Unit tests (mocked dependencies)
configs/                 # Tool configs (.ruff.toml, .yamllint.yaml)
clab/                    # Containerlab topology definitions
```

## Pydantic Model Patterns

```python
from pydantic import BaseModel, Field, computed_field, field_validator

class Device(BaseModel):
    """Network device with computed fields."""

    hostname: str = Field(description="Device hostname")
    _fabric_asns: dict[str, int] | None = None  # Private, injected

    @field_validator("hostname")
    @classmethod
    def validate_hostname(cls, v: str) -> str:
        """Validate and normalize hostname."""
        v = v.lower()
        if not v.startswith(("l", "s")):
            msg = f"Invalid hostname '{v}'"
            raise ValueError(msg)
        return v

    @computed_field
    @property
    def role(self) -> str:
        """Compute role from hostname prefix."""
        return "leaf" if self.hostname.startswith("l") else "spine"
```

## Testing Patterns

```python
import pytest

class TestDeviceValidation:
    """Test device validation logic."""

    def test_valid_hostname_accepted(self):
        """Valid hostname should be accepted."""
        device = Device(hostname="l1", interfaces=[])
        assert device.hostname == "l1"

    def test_invalid_hostname_raises_error(self):
        """Invalid hostname should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid hostname"):
            Device(hostname="invalid", interfaces=[])
```

## Common Mistakes to Avoid

1. **Don't import from typing**: Use `list[str] | None`, not `Optional[List[str]]`
2. **Don't use os.path**: Use `pathlib.Path` instead
3. **Don't add noqa without approval**: Fix the issue or ask first
4. **Don't forget trailing commas**: Required in multi-line structures
5. **Don't use bare except**: Always specify exception types
6. **Don't hardcode passwords**: Use `SecretStr` from Pydantic

## Additional Resources

- `.kiro/steering/code-style.md`: Detailed style guidelines
- `.kiro/steering/tech.md`: Technology stack and commands
- `configs/.ruff.toml`: Full Ruff configuration with rule explanations
