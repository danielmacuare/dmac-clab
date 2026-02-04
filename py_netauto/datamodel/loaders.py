"""Data loading utilities for fabric data models.

This module provides functions to load fabric configuration data from
YAML and JSON files, with comprehensive error handling and validation.

Functions:
    load_from_yaml: Load fabric data from a YAML file.
    load_from_json: Load fabric data from a JSON file.
    load_fabric: Generic loader that auto-detects format from file extension.

Example:
    >>> from py_netauto.datamodel import load_from_yaml
    >>> fabric = load_from_yaml("datamodel.yml")
    >>> print(f"Loaded fabric: {fabric.fabric_name}")

    >>> from py_netauto.datamodel import load_fabric
    >>> fabric = load_fabric("datamodel.json")  # Auto-detects JSON format
"""

import json
from pathlib import Path

import yaml
from pydantic import ValidationError

from .fabric import FabricDataModel


def load_from_yaml(file_path: str | Path) -> FabricDataModel:
    """Load fabric configuration from a YAML file.

    Reads a YAML file, parses it, and validates it against the
    FabricDataModel schema. Provides clear error messages for
    common issues like missing files or invalid YAML syntax.

    Args:
        file_path: Path to the YAML file (string or Path object).

    Returns:
        FabricDataModel: Validated fabric data model instance.

    Raises:
        FileNotFoundError: If the YAML file does not exist.
        PermissionError: If the file cannot be read.
        yaml.YAMLError: If the YAML syntax is invalid.
        ValidationError: If the data fails Pydantic validation.

    Example:
        >>> fabric = load_from_yaml("configs/fabric.yml")
        >>> print(f"Loaded {len(fabric.topology.spines)} spines")

        >>> # Handles various path types
        >>> from pathlib import Path
        >>> fabric = load_from_yaml(Path("configs/fabric.yml"))
    """
    file_path = Path(file_path)

    # Check if file exists
    if not file_path.exists():
        msg = f"YAML file not found: {file_path}"
        raise FileNotFoundError(msg)

    # Check if it's a file (not a directory)
    if not file_path.is_file():
        msg = f"Path is not a file: {file_path}"
        raise IsADirectoryError(msg)

    try:
        # Read and parse YAML
        with file_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        msg = f"Invalid YAML syntax in {file_path}: {e}"
        raise yaml.YAMLError(msg) from e
    except UnicodeDecodeError as e:
        msg = f"File is not valid UTF-8 text: {file_path}"
        raise UnicodeDecodeError(e.encoding, e.object, e.start, e.end, msg) from e

    # Validate data is not None (empty file)
    if data is None:
        msg = f"YAML file is empty or contains no data: {file_path}"
        raise ValueError(msg)

    # Validate against FabricDataModel
    try:
        return FabricDataModel.model_validate(data)
    except ValidationError as e:
        # Enhance error message with file context
        error_details = []
        for error in e.errors():
            location = ".".join(str(x) for x in error["loc"])
            error_details.append(f"  - {location}: {error['msg']} (type: {error['type']})")

        msg = f"Validation failed for {file_path}:\n" + "\n".join(error_details) + f"\n\nOriginal error: {e}"
        raise ValidationError.from_exception_data(title="FabricDataModel", line_errors=e.errors()) from e


def load_from_json(file_path: str | Path) -> FabricDataModel:
    """Load fabric configuration from a JSON file.

    Reads a JSON file, parses it, and validates it against the
    FabricDataModel schema. Provides clear error messages for
    common issues like missing files or invalid JSON syntax.

    Args:
        file_path: Path to the JSON file (string or Path object).

    Returns:
        FabricDataModel: Validated fabric data model instance.

    Raises:
        FileNotFoundError: If the JSON file does not exist.
        PermissionError: If the file cannot be read.
        json.JSONDecodeError: If the JSON syntax is invalid.
        ValidationError: If the data fails Pydantic validation.

    Example:
        >>> fabric = load_from_json("configs/fabric.json")
        >>> print(f"Loaded {len(fabric.topology.spines)} spines")

        >>> # Handles various path types
        >>> from pathlib import Path
        >>> fabric = load_from_json(Path("configs/fabric.json"))
    """
    file_path = Path(file_path)

    # Check if file exists
    if not file_path.exists():
        msg = f"JSON file not found: {file_path}"
        raise FileNotFoundError(msg)

    # Check if it's a file (not a directory)
    if not file_path.is_file():
        msg = f"Path is not a file: {file_path}"
        raise IsADirectoryError(msg)

    try:
        # Read and parse JSON
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        msg = f"Invalid JSON syntax in {file_path} at line {e.lineno}, column {e.colno}: {e.msg}"
        raise json.JSONDecodeError(msg, e.doc, e.pos) from e
    except UnicodeDecodeError as e:
        msg = f"File is not valid UTF-8 text: {file_path}"
        raise UnicodeDecodeError(e.encoding, e.object, e.start, e.end, msg) from e

    # Validate data is not None (empty file)
    if data is None:
        msg = f"JSON file is empty or contains no data: {file_path}"
        raise ValueError(msg)

    # Validate against FabricDataModel
    try:
        return FabricDataModel.model_validate(data)
    except ValidationError as e:
        # Enhance error message with file context
        error_details = []
        for error in e.errors():
            location = ".".join(str(x) for x in error["loc"])
            error_details.append(f"  - {location}: {error['msg']} (type: {error['type']})")

        msg = f"Validation failed for {file_path}:\n" + "\n".join(error_details) + f"\n\nOriginal error: {e}"
        raise ValidationError.from_exception_data(title="FabricDataModel", line_errors=e.errors()) from e


def load_fabric(file_path: str | Path) -> FabricDataModel:
    """Load fabric configuration from a file (auto-detect format).

    Automatically detects the file format based on the file extension
    and calls the appropriate loader (.yml/.yaml -> YAML, .json -> JSON).

    Args:
        file_path: Path to the configuration file (string or Path object).

    Returns:
        FabricDataModel: Validated fabric data model instance.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file extension is not supported.
        Various errors from load_from_yaml or load_from_json.

    Example:
        >>> fabric = load_fabric("configs/fabric.yml")  # Loads as YAML
        >>> fabric = load_fabric("configs/fabric.json")  # Loads as JSON
    """
    file_path = Path(file_path)

    # Get file extension
    suffix = file_path.suffix.lower()

    # Route to appropriate loader
    if suffix in (".yaml", ".yml"):
        return load_from_yaml(file_path)
    if suffix == ".json":
        return load_from_json(file_path)
    supported = [".yaml", ".yml", ".json"]
    msg = f"Unsupported file extension '{suffix}' for {file_path}. Supported formats: {', '.join(supported)}"
    raise ValueError(msg)
