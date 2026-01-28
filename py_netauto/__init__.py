"""
Python network automation toolkit for Containerlab environments.

This package provides tools for network device configuration management,
testing, and automation using Nornir and Scrapli.
"""

__version__ = "0.0.1"

# Optional: Export commonly used items for convenience
from py_netauto.config import Settings
from py_netauto.utils.nornir_helpers import initialize_nornir

__all__ = [
    "Settings",
    "initialize_nornir",
]
