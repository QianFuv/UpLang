"""
Version management for UpLang.

This module provides centralized version information retrieval.
"""

import tomllib
from pathlib import Path
from typing import Optional


def get_version() -> str:
    """Get the current version from pyproject.toml.

    Returns:
        Version string from pyproject.toml, fallback to "unknown" if not found
    """
    try:
        # Find pyproject.toml by traversing up from this file
        current_path = Path(__file__).parent
        for _ in range(5):  # Limit search depth
            pyproject_path = current_path / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path, 'rb') as f:
                    data = tomllib.load(f)
                return data.get('project', {}).get('version', 'unknown')
            current_path = current_path.parent

        # If not found, try relative to the source directory
        src_dir = Path(__file__).parent.parent.parent
        pyproject_path = src_dir / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path, 'rb') as f:
                data = tomllib.load(f)
            return data.get('project', {}).get('version', 'unknown')

    except Exception:
        pass

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