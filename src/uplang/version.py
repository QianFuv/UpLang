"""
Version management for UpLang.

This module provides centralized version information retrieval from
installed package metadata via importlib.metadata.
"""

from importlib.metadata import version as get_installed_version
from typing import Optional


def get_version() -> str:
    """Get the current version from package metadata.

    Returns:
        Version string from package metadata, fallback to "unknown" if not found
    """
    try:
        return get_installed_version("uplang")
    except Exception:
        return "unknown"


# Cache the version to avoid repeated file reads
_cached_version: Optional[str] = None


def get_cached_version() -> str:
    """Get cached version or fetch it if not cached.

    Returns:
        Cached version string
    """
    global _cached_version
    if _cached_version is None:
        _cached_version = get_version()
    return _cached_version