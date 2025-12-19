from pathlib import Path

from nornir import InitNornir

# 1. Get the absolute path of this helper file
# 2. Move up 3 levels to reach the project root
_HELPER_PATH = Path(__file__).resolve()
PROJECT_ROOT = _HELPER_PATH.parents[2]

# 3. Define the Nornir Config Path as a Constant
NORNIR_CONFIG_PATH = PROJECT_ROOT / "configs" / "nornir" / "nornir.yaml"


def get_nornir():
    """Initializes Nornir using the predefined NORNIR_CONFIG_PATH."""
    # Verify the constant path exists before attempting to load
    if not NORNIR_CONFIG_PATH.exists():
        error_msg = (
            f"\n[!] Nornir config not found at: {NORNIR_CONFIG_PATH}\nCheck if the file exists and is named correctly."
        )
        raise FileNotFoundError(error_msg)

    print(f"Loading Nornir config from: {NORNIR_CONFIG_PATH}")

    # InitNornir expects the config_file as a string
    return InitNornir(config_file=str(NORNIR_CONFIG_PATH))
