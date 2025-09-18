"""
Base command classes and utilities with dependency injection.

This module provides the base command class and result structures
used by all UpLang commands, with dependency injection support.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

from uplang.config import ProjectConfig
from uplang.container import ServiceContainer


@dataclass
class CommandResult:
    """Result object returned by command execution."""
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class BaseCommand(ABC):
    """Enhanced base command with dependency injection.

    Provides common functionality for all commands including
    configuration management, logging, and service container access.
    """

    def __init__(self, config: ProjectConfig, container: Optional[ServiceContainer] = None):
        """Initialize command with configuration and optional container."""
        self.config = config
        self.container = container or ServiceContainer(config)
        self.logger = self.container.get_logger()

    @abstractmethod
    def execute(self) -> CommandResult:
        """Execute the command and return result.

        Returns:
            CommandResult indicating success/failure and any data
        """
        pass

    def _ensure_directories(self) -> bool:
        """Ensure required directories exist with enhanced error handling.

        Returns:
            True if directories were created successfully, False otherwise
        """
        try:
            self.config.resource_pack_directory.mkdir(parents=True, exist_ok=True)
            assets_dir = self.config.resource_pack_directory / "assets"
            assets_dir.mkdir(exist_ok=True)
            return True
        except OSError as e:
            self.logger.error(f"Failed to create directories: {e}")
            return False

    def get_service_summary(self) -> Dict[str, str]:
        """Get summary of available services for debugging.

        Returns:
            Dictionary mapping service names to class names
        """
        return {
            'scanner': str(type(self.container.get_scanner()).__name__),
            'extractor': str(type(self.container.get_extractor()).__name__),
            'synchronizer': str(type(self.container.get_synchronizer()).__name__),
            'state_manager': str(type(self.container.get_state_manager()).__name__),
            'logger': str(type(self.container.get_logger()).__name__)
        }