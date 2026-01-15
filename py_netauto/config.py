from pathlib import Path
from typing import ClassVar

from pydantic import DirectoryPath, FilePath, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute path to the repository's root directory
PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    # Default Values: Used if no vars and provided in the .env file - Relative form the PROJECT's ROOT
    NORNIR_BASE_PATH: DirectoryPath = Path("configs/nornir")
    NORNIR_CONFIG_FILE_PATH: FilePath = Path(NORNIR_BASE_PATH / "nornir.yaml")
    JINJA_TEMPLATES_FOLDER_PATH: DirectoryPath = Path(NORNIR_BASE_PATH / "templates")
    NORNIR_INVENTORY_HOSTS_PATH: FilePath = Path(NORNIR_BASE_PATH / "inventory/hosts.yml")
    NORNIR_INVENTORY_GROUPS_PATH: FilePath = Path(NORNIR_BASE_PATH / "inventory/groups.yml")
    GENERATED_CONFIGS_FOLDER_PATH: DirectoryPath = Path(NORNIR_BASE_PATH / "templates")

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(env_file=PROJECT_ROOT / ".env")

    # Convert any string provided by the user to an absolute path before validation
    @field_validator(
        "NORNIR_CONFIG_FILE_PATH",
        "JINJA_TEMPLATES_FOLDER_PATH",
        "NORNIR_INVENTORY_HOSTS_PATH",
        "NORNIR_INVENTORY_GROUPS_PATH",
        "GENERATED_CONFIGS_FOLDER_PATH",
        mode="before",
    )
    @classmethod
    def make_paths_absolute(cls, v: str | Path) -> Path:
        path = Path(v)
        if path.is_absolute():
            return path

        return (PROJECT_ROOT / path).resolve()


config: dict[str, Path] = Settings().model_dump()

JINJA_TEMPLATES_FOLDER_PATH: Path = config["JINJA_TEMPLATES_FOLDER_PATH"]
NORNIR_CONFIG_FILE_PATH: Path = config["NORNIR_CONFIG_FILE_PATH"]
NORNIR_INVENTORY_HOSTS_PATH: Path = config["NORNIR_INVENTORY_HOSTS_PATH"]
NORNIR_INVENTORY_GROUPS_PATH: Path = config["NORNIR_INVENTORY_GROUPS_PATH"]
GENERATED_CONFIGS_FOLDER_PATH: Path = config["GENERATED_CONFIGS_FOLDER_PATH"]


__all__ = [
    "JINJA_TEMPLATES_FOLDER_PATH",
    "NORNIR_CONFIG_FILE_PATH",
    "NORNIR_INVENTORY_GROUPS_PATH",
    "NORNIR_INVENTORY_HOSTS_PATH",
    "GENERATED_CONFIGS_FOLDER_PATH",
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
    print(f"Templates Dir:      {JINJA_TEMPLATES_FOLDER_PATH}")
    print(f"Generated Configs Folder Dir: {GENERATED_CONFIGS_FOLDER_PATH}")
    print("-" * 30)
