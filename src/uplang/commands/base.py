"""
Base command classes and utilities
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

from uplang.config import ProjectConfig
from uplang.logger import UpLangLogger


@dataclass
class CommandResult:
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class BaseCommand(ABC):

    def __init__(self, config: ProjectConfig, logger: UpLangLogger):
        self.config = config
        self.logger = logger

    @abstractmethod
    def execute(self) -> CommandResult:
        """Execute the command and return result"""
        pass

    def _ensure_directories(self) -> bool:
        """Ensure required directories exist"""
        try:
            self.config.resource_pack_directory.mkdir(parents=True, exist_ok=True)
            assets_dir = self.config.resource_pack_directory / "assets"
            assets_dir.mkdir(exist_ok=True)
            return True
        except OSError as e:
            self.logger.error(f"Failed to create directories: {e}")
            return False