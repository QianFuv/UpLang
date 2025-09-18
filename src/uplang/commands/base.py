"""
Base command classes and utilities with dependency injection
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

from uplang.config import ProjectConfig
from uplang.logger import UpLangLogger
from uplang.container import ServiceContainer
from uplang.exceptions import handle_errors, ConfigurationError


@dataclass
class CommandResult:
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class BaseCommand(ABC):
    """Enhanced base command with dependency injection"""

    def __init__(self, config: ProjectConfig, container: Optional[ServiceContainer] = None):
        self.config = config
        self.container = container or ServiceContainer(config)
        self.logger = self.container.get_logger()

    @abstractmethod
    def execute(self) -> CommandResult:
        """Execute the command and return result"""
        pass

    def _ensure_directories(self) -> bool:
        """Ensure required directories exist with enhanced error handling"""
        try:
            self.config.resource_pack_directory.mkdir(parents=True, exist_ok=True)
            assets_dir = self.config.resource_pack_directory / "assets"
            assets_dir.mkdir(exist_ok=True)
            return True
        except OSError as e:
            self.logger.error(f"Failed to create directories: {e}")
            return False

    def get_service_summary(self) -> Dict[str, str]:
        """Get summary of available services for debugging"""
        return {
            'scanner': str(type(self.container.get_scanner()).__name__),
            'extractor': str(type(self.container.get_extractor()).__name__),
            'synchronizer': str(type(self.container.get_synchronizer()).__name__),
            'state_manager': str(type(self.container.get_state_manager()).__name__),
            'logger': str(type(self.container.get_logger()).__name__)
        }