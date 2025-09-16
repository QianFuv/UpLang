from dataclasses import dataclass
from typing import Optional

@dataclass
class Mod:
    """Represents a single mod."""
    mod_id: str
    version: str
    file_path: str
    file_hash: Optional[str] = None