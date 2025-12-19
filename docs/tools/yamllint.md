# yamllint

`yamllint` is a linter for YAML files that checks for syntax validity, key repetition, and cosmetic problems such as line length, trailing spaces, indentation, etc.

## Links
- Main repo: https://github.com/adrienverge/yamllint
- Documentation: https://yamllint.readthedocs.io/
- Latest Releases: https://github.com/adrienverge/yamllint/releases

## Installation

### Using pip (Recommended)
```bash
# Install yamllint
pip install yamllint

# Verify installation
yamllint --version
```

### Using package managers
```bash
# Ubuntu/Debian
sudo apt-get install yamllint

# CentOS/RHEL/Fedora
sudo dnf install yamllint

# macOS with Homebrew
brew install yamllint
```

## Configuration File

The `yamllint` command can be configured through a YAML configuration file. The configuration file can be placed in several locations:
- A file named `.yamllint`, `.yamllint.yml` or `.yamllint.yaml` in the current working directory or any parent directory
- `~/.config/yamllint/config`
- A custom path specified with the `-c` flag

**NOTE:** We use the `-c` flag to pass the custom path of the config file.
Example: `yamllint -c configs/.yamllint.yaml .`

## Basic Usage

### Check files for issues
```bash
# Check specific files
yamllint file1.yaml file2.yml

# Check all YAML files in current directory recursively
yamllint .

# Check with custom config
yamllint -c configs/.yamllint.yaml .

# Check and output in different formats
yamllint -f parsable .  # Machine-readable format
yamllint -f colored .   # Colored output (default)
yamllint -f github .    # GitHub Actions format
```

### Common flags
- `-c CONFIG_FILE`: Use custom configuration file
- `-f FORMAT`: Output format (standard, parsable, colored, github, auto)
- `-d CONFIG_DATA`: Use configuration from command line
- `--strict`: Return non-zero exit code on warnings as well as errors

## Configuration Rules

Our project uses a custom configuration file at `configs/.yamllint.yaml` with the following key settings:

- **Indentation**: **DISABLED** - yamlfmt handles indentation formatting
- **Line length**: Maximum 120 characters with exceptions for non-breakable content
- **Comments**: Require space after `#` and minimum 1 space from content
- **Ignored paths**: Excludes generated files and vendor directories

### Important: Indentation Conflict Resolution

**Note**: The `indentation` rule is disabled in our yamllint configuration to avoid conflicts with yamlfmt. Here's why:

- **yamlfmt** calculates indentation mathematically from the start of the line (4 spaces from parent element)
- **yamllint** expects "visual alignment" (offsetting from the start of the text of the parent mapping)

**Technical Conflict Example**:
```yaml
parent:
  - child: value  # yamlfmt indents to column 8, yamllint expects column 10
```

- yamllint calculates expected indentation as: parent text start (column 6) + 4 spaces = column 10
- yamlfmt calculates indentation as: parent dash (column 4) + 4 spaces = column 8

**Solution**: Let yamlfmt handle all indentation formatting, and yamllint focuses on other style rules like line length, comments, and syntax validation.

For detailed rule documentation, see: https://yamllint.readthedocs.io/en/stable/rules.html

## Integration with CI/CD

### prek hook
yamllint is integrated into our prek configuration (faster Rust-based alternative to pre-commit) to automatically check YAML files before commits. prek manages the yamllint installation automatically.

### Docker usage
```bash
# Run yamllint in Docker without installing
docker run --rm -v "$(pwd):/data" cytopia/yamllint .

# With custom config
docker run --rm -v "$(pwd):/data" cytopia/yamllint -c configs/.yamllint.yaml .
```

## Troubleshooting

### Common issues
1. **Indentation errors**: Ensure consistent use of spaces (not tabs) and proper nesting
2. **Line length**: Break long lines or use folded/literal scalars for long content
3. **Trailing spaces**: Remove whitespace at end of lines
4. **Document markers**: Add `---` at document start if required by your config

### Fixing issues automatically
While yamllint only reports issues, you can use `yamlfmt` to automatically fix formatting issues:
```bash
# Format files first, then lint
yamlfmt -c configs/.yamlfmt.yaml .
yamllint -c configs/.yamllint.yaml .
```