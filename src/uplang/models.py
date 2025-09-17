from dataclasses import dataclass, field
from typing import Optional, Dict

@dataclass
class Mod:
    """Represents a single mod."""
    mod_id: str
    version: str
    file_path: str
    file_hash: Optional[str] = None
    has_lang_files: bool = False
    lang_files: Dict[str, str] = field(default_factory=dict)