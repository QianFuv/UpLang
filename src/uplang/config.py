"""
Configuration management for UpLang
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any
import json


@dataclass
class AppConfig:
    log_level: str = "info"
    quiet_mode: bool = False
    no_color: bool = False
    max_workers: int = 4
    backup_enabled: bool = True


@dataclass
class ProjectConfig:
    mods_directory: Path
    resource_pack_directory: Path
    state_file: Path
    config: AppConfig

    @classmethod
    def from_paths(cls, mods_dir: str, resource_pack_dir: str, config: Optional[AppConfig] = None) -> "ProjectConfig":
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


class ConfigManager:

    @staticmethod
    def load_project_config(config_path: Path) -> Dict[str, Any]:
        if not config_path.exists():
            return {}

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    @staticmethod
    def save_project_config(config_path: Path, data: Dict[str, Any]) -> bool:
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False