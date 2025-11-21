"""
Synchronization result models.
"""

from dataclasses import dataclass, field


@dataclass
class DiffResult:
    """
    Result of comparing two language files.
    """

    added: set[str] = field(default_factory=set)
    modified: set[str] = field(default_factory=set)
    deleted: set[str] = field(default_factory=set)
    unchanged: set[str] = field(default_factory=set)

    @property
    def has_changes(self) -> bool:
        """
        Check if there are any changes.
        """
        return bool(self.added or self.modified or self.deleted)

    @property
    def total_changes(self) -> int:
        """
        Total number of changes.
        """
        return len(self.added) + len(self.modified) + len(self.deleted)

    def __str__(self) -> str:
        return f"+{len(self.added)} ~{len(self.modified)} -{len(self.deleted)}"


@dataclass
class SyncResult:
    """
    Result of synchronizing a mod's language files.
    """

    mod_id: str
    success: bool = True
    skipped: bool = False
    added_keys: int = 0
    modified_keys: int = 0
    deleted_keys: int = 0
    error: str | None = None

    @property
    def total_changes(self) -> int:
        """
        Total number of changes.
        """
        return self.added_keys + self.modified_keys + self.deleted_keys

    def __str__(self) -> str:
        if self.skipped:
            return f"{self.mod_id}: skipped (no changes)"
        if not self.success:
            return f"{self.mod_id}: failed ({self.error})"
        return (
            f"{self.mod_id}: "
            f"+{self.added_keys} ~{self.modified_keys} -{self.deleted_keys}"
        )
