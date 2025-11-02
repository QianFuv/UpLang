"""
Path and filename utilities.
"""

import re
from pathlib import Path


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.
    """
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
    filename = re.sub(r"\s+", "_", filename)
    filename = filename.strip("._")
    return filename or "unnamed"


def extract_mod_id(jar_path: Path) -> str:
    """
    Extract mod ID from JAR filename.
    """
    stem = jar_path.stem
    stem = re.sub(r"-\d+.*$", "", stem)
    stem = re.sub(r"[^a-z0-9_]", "_", stem.lower())
    return stem or "unknown"
