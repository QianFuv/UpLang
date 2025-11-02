"""
Mod data model.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ModType(Enum):
    """
    Type of mod loader.
    """

    FORGE = "forge"
    FABRIC = "fabric"
    NEOFORGE = "neoforge"
    UNKNOWN = "unknown"


@dataclass
class Mod:
    """
    Represents a Minecraft mod.
    """

    mod_id: str
    name: str
    version: str
    jar_path: Path
    mod_type: ModType = ModType.UNKNOWN

    def __str__(self) -> str:
        return f"{self.name} ({self.mod_id}) v{self.version}"
