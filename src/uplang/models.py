"""
Data models for UpLang.

This module defines the core data structures used throughout UpLang,
including mod information, comparison results, and synchronization statistics.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Set
from enum import Enum


class ModType(Enum):
    """Enumeration of supported mod loader types."""
    FORGE = "forge"
    FABRIC = "fabric"
    UNKNOWN = "unknown"


class ModStatus(Enum):
    """Enumeration of mod status types during comparison."""
    NEW = "new"
    UPDATED = "updated"
    UNCHANGED = "unchanged"
    DELETED = "deleted"


@dataclass
class Mod:
    """Represents a Minecraft mod with metadata and file information."""
    mod_id: str  # Unique identifier for the mod
    version: str  # Version string from mod metadata
    file_path: Path  # Path to the JAR file
    mod_type: ModType = ModType.UNKNOWN  # Detected mod loader type
    file_hash: Optional[str] = None  # SHA256 hash of the JAR file
    has_lang_files: bool = False  # Whether mod contains language files
    lang_files: Dict[str, str] = field(default_factory=dict)  # Language file paths
    status: ModStatus = ModStatus.UNCHANGED  # Status during comparison

    def __hash__(self):
        """Return hash based on mod_id, version, and file_path."""
        return hash((self.mod_id, self.version, str(self.file_path)))

    def __eq__(self, other):
        """Check equality based on mod_id, version, and file_path."""
        if not isinstance(other, Mod):
            return False
        return (self.mod_id == other.mod_id and
                self.version == other.version and
                self.file_path == other.file_path)

    @property
    def is_recognized(self) -> bool:
        """Check if mod was recognized by scanning metadata."""
        return not self.mod_id.startswith("unrecognized_")

    @property
    def display_name(self) -> str:
        """Get display-friendly mod name."""
        if self.is_recognized:
            return self.mod_id
        return self.mod_id.replace("unrecognized_", "")


@dataclass
class ModComparisonResult:
    """Results of comparing current mods with previous state."""
    new_mods: Set[Mod] = field(default_factory=set)  # Newly discovered mods
    updated_mods: Set[Mod] = field(default_factory=set)  # Mods with changes
    deleted_mods: Set[Mod] = field(default_factory=set)  # Removed mods
    unchanged_mods: Set[Mod] = field(default_factory=set)  # Unmodified mods

    @property
    def has_changes(self) -> bool:
        """Check if there are any changes in the comparison."""
        return bool(self.new_mods or self.updated_mods or self.deleted_mods)

    @property
    def total_changes(self) -> int:
        """Get total number of changed mods."""
        return len(self.new_mods) + len(self.updated_mods) + len(self.deleted_mods)


@dataclass
class SyncStats:
    """Statistics for language file synchronization operations."""
    keys_added: int = 0  # Number of translation keys added
    keys_removed: int = 0  # Number of translation keys removed
    files_processed: int = 0  # Number of files successfully processed
    files_skipped: int = 0  # Number of files skipped
    errors: int = 0  # Number of errors encountered

    # Enhanced statistics for better tracking
    mods_with_changes: Set[str] = field(default_factory=set)  # Mod IDs with key changes
    new_mod_files: int = 0  # New language files created
    updated_mod_files: int = 0  # Existing language files updated

    @property
    def total_changes(self) -> int:
        """Get total number of key changes."""
        return self.keys_added + self.keys_removed

    @property
    def has_changes(self) -> bool:
        """Check if there were any synchronization changes."""
        return self.total_changes > 0

    @property
    def total_mods_affected(self) -> int:
        """Get total number of mods with changes."""
        return len(self.mods_with_changes)

    def add_mod_change(self, mod_id: str, is_new_file: bool = False):
        """Track a mod that had changes.

        Args:
            mod_id: The mod identifier that had changes
            is_new_file: Whether this was a new language file
        """
        self.mods_with_changes.add(mod_id)
        if is_new_file:
            self.new_mod_files += 1
        else:
            self.updated_mod_files += 1

    def merge(self, other: 'SyncStats'):
        """Merge another SyncStats into this one.

        Args:
            other: Another SyncStats instance to merge
        """
        self.keys_added += other.keys_added
        self.keys_removed += other.keys_removed
        self.files_processed += other.files_processed
        self.files_skipped += other.files_skipped
        self.errors += other.errors
        self.mods_with_changes.update(other.mods_with_changes)
        self.new_mod_files += other.new_mod_files
        self.updated_mod_files += other.updated_mod_files