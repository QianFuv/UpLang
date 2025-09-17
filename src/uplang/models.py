"""
Data models for UpLang
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Set
from enum import Enum


class ModType(Enum):
    FORGE = "forge"
    FABRIC = "fabric"
    UNKNOWN = "unknown"


class ModStatus(Enum):
    NEW = "new"
    UPDATED = "updated"
    UNCHANGED = "unchanged"
    DELETED = "deleted"


@dataclass
class Mod:
    mod_id: str
    version: str
    file_path: Path
    mod_type: ModType = ModType.UNKNOWN
    file_hash: Optional[str] = None
    has_lang_files: bool = False
    lang_files: Dict[str, str] = field(default_factory=dict)
    status: ModStatus = ModStatus.UNCHANGED

    def __hash__(self):
        return hash((self.mod_id, self.version, str(self.file_path)))

    def __eq__(self, other):
        if not isinstance(other, Mod):
            return False
        return (self.mod_id == other.mod_id and
                self.version == other.version and
                self.file_path == other.file_path)

    @property
    def is_recognized(self) -> bool:
        return not self.mod_id.startswith("unrecognized_")

    @property
    def display_name(self) -> str:
        if self.is_recognized:
            return self.mod_id
        return self.mod_id.replace("unrecognized_", "")


@dataclass
class ModComparisonResult:
    new_mods: Set[Mod] = field(default_factory=set)
    updated_mods: Set[Mod] = field(default_factory=set)
    deleted_mods: Set[Mod] = field(default_factory=set)
    unchanged_mods: Set[Mod] = field(default_factory=set)

    @property
    def has_changes(self) -> bool:
        return bool(self.new_mods or self.updated_mods or self.deleted_mods)

    @property
    def total_changes(self) -> int:
        return len(self.new_mods) + len(self.updated_mods) + len(self.deleted_mods)


@dataclass
class SyncStats:
    keys_added: int = 0
    keys_removed: int = 0
    files_processed: int = 0
    files_skipped: int = 0
    errors: int = 0

    @property
    def total_changes(self) -> int:
        return self.keys_added + self.keys_removed

    @property
    def has_changes(self) -> bool:
        return self.total_changes > 0