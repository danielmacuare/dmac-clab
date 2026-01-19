from pathlib import Path
from typing import ClassVar, Optional

from pydantic import DirectoryPath, FilePath, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute path to the repository's root directory
PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    # Default Values: Used if no vars and provided in the .env file - Relative from the PROJECT's ROOT
    NORNIR_BASE_PATH: DirectoryPath = Path("configs/nornir")
    NORNIR_CONFIG_FILE_PATH: FilePath | None = None  # Optional - if None, use individual inventory files
    JINJA_TEMPLATES_FOLDER_PATH: DirectoryPath = Path(NORNIR_BASE_PATH / "templates")
    NORNIR_INVENTORY_HOSTS_PATH: FilePath = Path(NORNIR_BASE_PATH / "inventory/hosts.yml")
    NORNIR_INVENTORY_GROUPS_PATH: FilePath = Path(NORNIR_BASE_PATH / "inventory/groups.yml")
    NORNIR_INVENTORY_DEFAULTS_PATH: FilePath = Path(NORNIR_BASE_PATH / "inventory/defaults.yml")
    GENERATED_CONFIGS_FOLDER_PATH: DirectoryPath = Path(NORNIR_BASE_PATH / "templates")

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        extra="ignore",  # Ignore extra fields from .env (like NORNIR_BASE_PATH used for composition)
    )

    # Convert any string provided by the user to an absolute path before validation
    @field_validator(
        "NORNIR_CONFIG_FILE_PATH",
        "JINJA_TEMPLATES_FOLDER_PATH",
        "NORNIR_INVENTORY_HOSTS_PATH",
        "NORNIR_INVENTORY_GROUPS_PATH",
        "NORNIR_INVENTORY_DEFAULTS_PATH",
        "GENERATED_CONFIGS_FOLDER_PATH",
        mode="before",
    )
    @classmethod
    def make_paths_absolute(cls, env_var: str | Path | None) -> Path | None:
        """
        Convert a path to an absolute path relative to the project root.

        Args:
            env_var: A string path, Path object, or None to convert.

        Returns:
            An absolute Path object relative to PROJECT_ROOT, or None if input is None.
            If the input path is already absolute, it is returned as-is.

        """
        if env_var is None:
            return None
        path = Path(env_var)
        if path.is_absolute():
            return path

        return (PROJECT_ROOT / path).resolve()


config: dict[str, Path | None] = Settings().model_dump()

JINJA_TEMPLATES_FOLDER_PATH: Path = config["JINJA_TEMPLATES_FOLDER_PATH"]
NORNIR_CONFIG_FILE_PATH: Path | None = config["NORNIR_CONFIG_FILE_PATH"]
NORNIR_INVENTORY_HOSTS_PATH: Path = config["NORNIR_INVENTORY_HOSTS_PATH"]
NORNIR_INVENTORY_GROUPS_PATH: Path = config["NORNIR_INVENTORY_GROUPS_PATH"]
NORNIR_INVENTORY_DEFAULTS_PATH: Path = config["NORNIR_INVENTORY_DEFAULTS_PATH"]
GENERATED_CONFIGS_FOLDER_PATH: Path = config["GENERATED_CONFIGS_FOLDER_PATH"]


__all__ = [
    "GENERATED_CONFIGS_FOLDER_PATH",
    "JINJA_TEMPLATES_FOLDER_PATH",
    "NORNIR_CONFIG_FILE_PATH",
    "NORNIR_INVENTORY_DEFAULTS_PATH",
    "NORNIR_INVENTORY_GROUPS_PATH",
    "NORNIR_INVENTORY_HOSTS_PATH",
    "PROJECT_ROOT",
]

if __name__ == "__main__":
    print("-" * 30)
    print("CONFIG VERIFICATION")
    print("-" * 30)
    print(f"Project Root:       {PROJECT_ROOT}")
    print(f"Config File:        {NORNIR_CONFIG_FILE_PATH}")
    print(f"Inventory Hosts:    {NORNIR_INVENTORY_HOSTS_PATH}")
    print(f"Inventory Groups:   {NORNIR_INVENTORY_GROUPS_PATH}")
    print(f"Inventory Defaults: {NORNIR_INVENTORY_DEFAULTS_PATH}")
    print(f"Templates Dir:      {JINJA_TEMPLATES_FOLDER_PATH}")
    print(f"Generated Configs Folder Dir: {GENERATED_CONFIGS_FOLDER_PATH}")
    print("-" * 30)
