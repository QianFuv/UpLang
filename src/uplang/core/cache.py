"""
Hash-based cache manager for tracking mod changes.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from uplang import __version__
from uplang.exceptions import CacheError
from uplang.utils.output import print_verbose


class CacheManager:
    """
    Manage hash-based cache for detecting mod changes.
    """

    CACHE_VERSION = __version__

    def __init__(self, cache_path: Path):
        self.cache_path = cache_path
        self.cache_data: dict[str, Any] = self._load_cache()

    def _load_cache(self) -> dict[str, Any]:
        """
        Load cache from file.
        """
        if not self.cache_path.exists():
            return self._create_empty_cache()

        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if data.get("version") != self.CACHE_VERSION:
                print_verbose(
                    f"Cache version mismatch, recreating cache "
                    f"(expected {self.CACHE_VERSION}, got {data.get('version')})"
                )
                return self._create_empty_cache()

            print_verbose(f"Loaded cache from {self.cache_path}")
            return data

        except Exception as e:
            print_verbose(f"Failed to load cache: {e}, creating new cache")
            return self._create_empty_cache()

    def _create_empty_cache(self) -> dict[str, Any]:
        """
        Create an empty cache structure.
        """
        return {
            "version": self.CACHE_VERSION,
            "last_updated": datetime.now().isoformat(),
            "mods": {},
        }

    def save(self) -> None:
        """
        Save cache to file.
        """
        try:
            self.cache_data["last_updated"] = datetime.now().isoformat()
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.cache_path, "w", encoding="utf-8", newline="\n") as f:
                json.dump(self.cache_data, f, indent=2, ensure_ascii=False)

            print_verbose(f"Saved cache to {self.cache_path}")

        except Exception as e:
            raise CacheError(
                f"Failed to save cache: {e}", context={"path": str(self.cache_path)}
            ) from e

    def is_changed(
        self, mod_id: str, en_us_hash: str | None, zh_cn_hash: str | None
    ) -> bool:
        """
        Check if a mod's language files have changed since last sync.
        """
        if mod_id not in self.cache_data["mods"]:
            return True

        cached = self.cache_data["mods"][mod_id]

        if en_us_hash and cached.get("en_us_hash") != en_us_hash:
            return True

        if zh_cn_hash and cached.get("zh_cn_hash") != zh_cn_hash:
            return True

        return False

    def update_mod(
        self,
        mod_id: str,
        jar_name: str,
        en_us_hash: str | None,
        zh_cn_hash: str | None,
    ) -> None:
        """
        Update cache entry for a mod.
        """
        self.cache_data["mods"][mod_id] = {
            "jar_name": jar_name,
            "en_us_hash": en_us_hash,
            "zh_cn_hash": zh_cn_hash,
            "last_sync": datetime.now().isoformat(),
        }

    def remove_mod(self, mod_id: str) -> None:
        """
        Remove a mod from the cache.
        """
        if mod_id in self.cache_data["mods"]:
            del self.cache_data["mods"][mod_id]

    def get_cached_mod_ids(self) -> set[str]:
        """
        Get all mod IDs in the cache.
        """
        return set(self.cache_data["mods"].keys())

    def clear(self) -> None:
        """
        Clear all cache data.
        """
        self.cache_data = self._create_empty_cache()
        print_verbose("Cache cleared")
