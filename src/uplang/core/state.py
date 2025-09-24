"""
Project state management functionality
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from uplang.exceptions import StateError
from uplang.logger import UpLangLogger
from uplang.models import Mod, ModComparisonResult, ModStatus
from uplang.version import get_cached_version


class StateManager:

    def __init__(self, logger: UpLangLogger):
        self.logger = logger

    def save_state(self, mods: List[Mod], state_file: Path, mods_dir: Path, resource_pack_dir: Path) -> bool:
        """Save current project state to file"""
        try:
            state_data = {
                "version": get_cached_version(),
                "timestamp": datetime.now().isoformat(),
                "project_info": {
                    "mods_directory": str(mods_dir),
                    "resource_pack_directory": str(resource_pack_dir)
                },
                "mods_map": {
                    mod.mod_id: {
                        "mod_id": mod.mod_id,
                        "version": mod.version,
                        "file_path": str(mod.file_path),
                        "file_hash": mod.file_hash,
                        "mod_type": mod.mod_type.value,
                        "has_lang_files": mod.has_lang_files,
                        "lang_files": mod.lang_files
                    }
                    for mod in mods
                }
            }

            state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)

            self.logger.debug(f"Saved state with {len(mods)} mods to {state_file}")
            return True

        except OSError as e:
            raise StateError(f"Failed to save state: {e}")

    def load_state(self, state_file: Path) -> Optional[Dict[str, Any]]:
        """Load project state from file"""
        if not state_file.exists():
            return None

        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.logger.debug(f"Loaded state from {state_file}")
            return data

        except (json.JSONDecodeError, OSError) as e:
            self.logger.warning(f"Failed to load state file: {e}")
            return None

    def compare_mods(self, current_mods: List[Mod], previous_state: Dict[str, Any]) -> ModComparisonResult:
        """Compare current mods with previous state based on file hash changes"""
        result = ModComparisonResult()

        old_mods_map = previous_state.get("mods_map", {})
        current_mods_map = {mod.mod_id: mod for mod in current_mods}

        old_mod_ids = set(old_mods_map.keys())
        current_mod_ids = set(current_mods_map.keys())

        # Step 1: Identify new mods (exist in current but not in previous)
        for mod_id in current_mod_ids - old_mod_ids:
            mod = current_mods_map[mod_id]
            mod.status = ModStatus.NEW
            result.new_mods.add(mod)

        # Step 2: Identify deleted mods (exist in previous but not in current)
        for mod_id in old_mod_ids - current_mod_ids:
            old_mod_data = old_mods_map[mod_id]
            deleted_mod = self._create_mod_from_data(old_mod_data)
            deleted_mod.status = ModStatus.DELETED
            result.deleted_mods.add(deleted_mod)

        # Step 3: Check existing mods for updates based on file hash changes
        for mod_id in old_mod_ids.intersection(current_mod_ids):
            current_mod = current_mods_map[mod_id]
            old_mod_data = old_mods_map[mod_id]

            # Compare file hash to detect any changes to the mod file
            old_hash = old_mod_data.get("file_hash")
            current_hash = current_mod.file_hash

            if old_hash != current_hash:
                current_mod.status = ModStatus.UPDATED
                result.updated_mods.add(current_mod)
                self.logger.debug(f"Mod {mod_id} updated: hash changed from {old_hash} to {current_hash}")
            else:
                current_mod.status = ModStatus.UNCHANGED
                result.unchanged_mods.add(current_mod)

        return result

    def _create_mod_from_data(self, mod_data: Dict[str, Any]) -> Mod:
        """Create a Mod object from saved data"""
        from uplang.models import ModType

        return Mod(
            mod_id=mod_data["mod_id"],
            version=mod_data["version"],
            file_path=Path(mod_data["file_path"]),
            mod_type=ModType(mod_data.get("mod_type", "unknown")),
            file_hash=mod_data.get("file_hash"),
            has_lang_files=mod_data.get("has_lang_files", False),
            lang_files=mod_data.get("lang_files", {})
        )


def save_state(mods: List[Mod], state_file: str, mods_dir: str, resource_pack_dir: str):
    """Legacy function for backward compatibility"""
    from uplang.logger import get_logger
    manager = StateManager(get_logger())
    manager.save_state(mods, Path(state_file), Path(mods_dir), Path(resource_pack_dir))


def load_state(state_file: str) -> Optional[Dict[str, Any]]:
    """Legacy function for backward compatibility"""
    from uplang.logger import get_logger
    manager = StateManager(get_logger())
    return manager.load_state(Path(state_file))
