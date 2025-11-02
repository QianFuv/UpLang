"""
Hash calculation utilities.
"""

import hashlib
import json
from pathlib import Path
from typing import Any


def calculate_hash(file_path: Path) -> str:
    """
    Calculate SHA256 hash of a file.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def calculate_dict_hash(data: dict[str, Any]) -> str:
    """
    Calculate SHA256 hash of a dictionary.
    """
    json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(json_str.encode("utf-8", errors="surrogatepass")).hexdigest()
