"""
Service container for dependency injection
"""

from typing import Dict, Any, TypeVar, Type, Optional

from uplang.config import ProjectConfig
from uplang.logger import UpLangLogger
from uplang.core.scanner import ModScanner
from uplang.core.extractor import LanguageExtractor
from uplang.core.synchronizer import LanguageSynchronizer
from uplang.core.state import StateManager

T = TypeVar('T')


class ServiceContainer:
    """Dependency injection container for UpLang services"""

    def __init__(self, config: ProjectConfig):
        self.config = config
        self._services: Dict[str, Any] = {}
        self._logger: Optional[UpLangLogger] = None

    def get_logger(self) -> UpLangLogger:
        """Get or create logger instance"""
        if self._logger is None:
            self._logger = UpLangLogger()
            if hasattr(self.config, 'resource_pack_directory'):
                self._logger.setup(
                    self.config.resource_pack_directory,
                    log_level=self.config.config.log_level,
                    quiet=self.config.config.quiet_mode,
                    no_color=self.config.config.no_color
                )
        return self._logger

    def get_scanner(self) -> ModScanner:
        """Get ModScanner instance"""
        if 'scanner' not in self._services:
            self._services['scanner'] = ModScanner(self.get_logger())
        return self._services['scanner']

    def get_extractor(self) -> LanguageExtractor:
        """Get LanguageExtractor instance"""
        if 'extractor' not in self._services:
            self._services['extractor'] = LanguageExtractor(self.get_logger())
        return self._services['extractor']

    def get_synchronizer(self) -> LanguageSynchronizer:
        """Get LanguageSynchronizer instance"""
        if 'synchronizer' not in self._services:
            self._services['synchronizer'] = LanguageSynchronizer(self.get_logger())
        return self._services['synchronizer']

    def get_state_manager(self) -> StateManager:
        """Get StateManager instance"""
        if 'state_manager' not in self._services:
            self._services['state_manager'] = StateManager(self.get_logger())
        return self._services['state_manager']

    def register_service(self, name: str, service: Any) -> None:
        """Register a custom service"""
        self._services[name] = service

    def get_service(self, name: str, service_type: Type[T]) -> Optional[T]:
        """Get a registered service by name"""
        service = self._services.get(name)
        return service if isinstance(service, service_type) else None

    def clear_services(self) -> None:
        """Clear all cached services (useful for testing)"""
        self._services.clear()
        self._logger = None


class ServiceFactory:
    """Factory for creating services with proper dependencies"""

    @staticmethod
    def create_container(config: ProjectConfig) -> ServiceContainer:
        """Create a fully configured service container"""
        return ServiceContainer(config)

    @staticmethod
    def create_services_for_command(config: ProjectConfig) -> tuple:
        """Create all services needed for commands"""
        container = ServiceFactory.create_container(config)
        return (
            container.get_scanner(),
            container.get_extractor(),
            container.get_synchronizer(),
            container.get_state_manager(),
            container.get_logger()
        )