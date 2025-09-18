"""
Configuration management for UpLang with validation.

This module handles configuration loading, validation, and management
for UpLang projects, including application and project-specific settings.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, List
import json

from uplang.exceptions import ConfigurationError, ValidationError


@dataclass
class AppConfig:
    """Application-wide configuration settings."""
    log_level: str = "info"
    quiet_mode: bool = False
    no_color: bool = False
    max_workers: int = 4
    backup_enabled: bool = True


@dataclass
class ProjectConfig:
    """Project-specific configuration settings."""
    mods_directory: Path
    resource_pack_directory: Path
    state_file: Path
    config: AppConfig

    @classmethod
    def from_paths(cls, mods_dir: str, resource_pack_dir: str, config: Optional[AppConfig] = None) -> "ProjectConfig":
        """Create ProjectConfig from directory paths.

        Args:
            mods_dir: Path to mods directory
            resource_pack_dir: Path to resource pack directory
            config: Optional AppConfig instance

        Returns:
            Configured ProjectConfig instance
        """
        mods_path = Path(mods_dir).resolve()
        rp_path = Path(resource_pack_dir).resolve()
        state_file = rp_path / ".uplang_state.json"

        if config is None:
            config = AppConfig()

        return cls(
            mods_directory=mods_path,
            resource_pack_directory=rp_path,
            state_file=state_file,
            config=config
        )


class ConfigValidator:
    """Configuration validation utilities."""

    @staticmethod
    def validate_app_config(config: AppConfig) -> List[str]:
        """Validate AppConfig and return list of errors.

        Args:
            config: AppConfig instance to validate

        Returns:
            List of validation error messages
        """
        errors = []

        # Validate log level
        valid_levels = ['debug', 'info', 'warning', 'error']
        if config.log_level.lower() not in valid_levels:
            errors.append(f"Invalid log_level '{config.log_level}'. Must be one of: {valid_levels}")

        # Validate max_workers
        if config.max_workers < 1:
            errors.append(f"max_workers must be at least 1, got {config.max_workers}")
        if config.max_workers > 16:
            errors.append(f"max_workers should not exceed 16, got {config.max_workers}")

        return errors

    @staticmethod
    def validate_project_config(config: ProjectConfig) -> List[str]:
        """Validate ProjectConfig and return list of errors.

        Args:
            config: ProjectConfig instance to validate

        Returns:
            List of validation error messages
        """
        errors = []

        # Validate directories
        if not config.mods_directory.exists():
            errors.append(f"Mods directory does not exist: {config.mods_directory}")
        elif not config.mods_directory.is_dir():
            errors.append(f"Mods path is not a directory: {config.mods_directory}")

        # Check if resource pack directory is writable
        try:
            config.resource_pack_directory.mkdir(parents=True, exist_ok=True)
            # Test write access
            test_file = config.resource_pack_directory / ".uplang_write_test"
            test_file.touch()
            test_file.unlink()
        except (OSError, PermissionError) as e:
            errors.append(f"Resource pack directory is not writable: {config.resource_pack_directory} ({e})")

        # Validate app config
        app_errors = ConfigValidator.validate_app_config(config.config)
        errors.extend(app_errors)

        return errors

    @staticmethod
    def validate_and_raise(config: ProjectConfig) -> None:
        """Validate configuration and raise exception if invalid.

        Args:
            config: ProjectConfig instance to validate

        Raises:
            ValidationError: If configuration is invalid
        """
        errors = ConfigValidator.validate_project_config(config)
        if errors:
            raise ValidationError(
                f"Configuration validation failed: {len(errors)} errors found",
                context={'errors': errors}
            )


class ConfigManager:
    """Enhanced configuration manager with validation."""

    @staticmethod
    def load_project_config(config_path: Path) -> Dict[str, Any]:
        """Load project configuration with error handling.

        Args:
            config_path: Path to configuration file

        Returns:
            Configuration dictionary

        Raises:
            ConfigurationError: If configuration cannot be loaded
        """
        if not config_path.exists():
            return {}

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise ConfigurationError(
                f"Failed to load configuration from {config_path}",
                context={'path': str(config_path)},
                cause=e
            )

    @staticmethod
    def save_project_config(config_path: Path, data: Dict[str, Any]) -> None:
        """Save project configuration with error handling.

        Args:
            config_path: Path to save configuration file
            data: Configuration data to save

        Raises:
            ConfigurationError: If configuration cannot be saved
        """
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise ConfigurationError(
                f"Failed to save configuration to {config_path}",
                context={'path': str(config_path)},
                cause=e
            )

    @staticmethod
    def create_validated_config(mods_dir: str, resource_pack_dir: str,
                              app_config: Optional[AppConfig] = None) -> ProjectConfig:
        """Create and validate a project configuration.

        Args:
            mods_dir: Path to mods directory
            resource_pack_dir: Path to resource pack directory
            app_config: Optional application configuration

        Returns:
            Validated ProjectConfig instance

        Raises:
            ValidationError: If configuration is invalid
        """
        config = ProjectConfig.from_paths(mods_dir, resource_pack_dir, app_config)
        ConfigValidator.validate_and_raise(config)
        return config