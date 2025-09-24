"""
Language file synchronization functionality.

This module provides functionality to synchronize Chinese and English
language files, maintaining translation integrity and key ordering.
"""

from collections import OrderedDict
from pathlib import Path
from typing import Dict, Optional

from rich.progress import Progress, BarColumn, TextColumn, TaskProgressColumn

from uplang.logger import UpLangLogger
from uplang.models import SyncStats
from uplang.json_utils import read_json_robust, write_json_safe


class LanguageSynchronizer:
    """Synchronizer for Minecraft mod language files."""

    def __init__(self, logger: UpLangLogger):
        """Initialize LanguageSynchronizer with logger."""
        self.logger = logger

    def synchronize_file(self, zh_cn_path: Path, en_us_path: Path, zh_translations: Optional[Dict[str, str]] = None, mod_id: Optional[str] = None) -> SyncStats:
        """Synchronize a Chinese language file with its English counterpart.

        This method ensures that the Chinese file contains all keys from the English file
        while preserving existing translations and maintaining key order.

        Args:
            zh_cn_path: Path to Chinese language file
            en_us_path: Path to English language file
            zh_translations: Optional dict of Chinese translations for new keys
            mod_id: Optional mod identifier for enhanced statistics

        Returns:
            SyncStats object containing synchronization statistics
        """
        stats = SyncStats()

        try:
            if not en_us_path.exists():
                self.logger.warning(f"English file not found: {en_us_path}")
                stats.files_skipped += 1
                return stats

            en_data = read_json_robust(en_us_path, self.logger)
            if not en_data:
                stats.files_skipped += 1
                return stats

            zh_data = OrderedDict()
            if zh_cn_path.exists():
                loaded_data = read_json_robust(zh_cn_path, self.logger)
                if isinstance(loaded_data, dict):
                    zh_data = OrderedDict(loaded_data)
                else:
                    self.logger.warning(f"Invalid Chinese file format: {zh_cn_path}")

            keys_to_add = {key: value for key, value in en_data.items() if key not in zh_data}
            keys_to_remove = {key for key in zh_data if key not in en_data}

            # Determine if this is a new file (Chinese file doesn't exist)
            is_new_file = not zh_cn_path.exists()

            if keys_to_add or keys_to_remove:
                # Create a new OrderedDict to maintain the order from en_data first
                new_zh_data = OrderedDict()

                # First, add all keys from en_data in their original order
                for key, value in en_data.items():
                    if key in zh_data:
                        # Keep existing translation
                        new_zh_data[key] = zh_data[key]
                    else:
                        # Add new key with Chinese translation if available, otherwise English value
                        if zh_translations and key in zh_translations:
                            new_zh_data[key] = zh_translations[key]
                        else:
                            new_zh_data[key] = value
                        stats.keys_added += 1

                # Count removed keys
                for key in keys_to_remove:
                    stats.keys_removed += 1

                zh_data = new_zh_data

                write_json_safe(zh_cn_path, zh_data, self.logger)
                self.logger.debug(f"Synchronized {zh_cn_path}: +{stats.keys_added} -{stats.keys_removed}")

                # Track mod changes if mod_id provided and there were changes
                if mod_id and (stats.keys_added > 0 or stats.keys_removed > 0):
                    stats.add_mod_change(mod_id, is_new_file)

            stats.files_processed += 1
            return stats

        except Exception as e:
            self.logger.error(f"Failed to synchronize {zh_cn_path}: {e}")
            stats.errors += 1
            return stats

    def synchronize_multiple(self, file_pairs: list) -> SyncStats:
        """Synchronize multiple language file pairs with progress tracking.

        Args:
            file_pairs: List of tuples containing (zh_cn_path, en_us_path) or (zh_cn_path, en_us_path, mod_id)

        Returns:
            Aggregated SyncStats for all processed files
        """
        total_stats = SyncStats()

        if not file_pairs:
            return total_stats

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.logger.console,
            disable=self.logger._quiet_mode
        ) as progress:
            task = progress.add_task("Synchronizing files...", total=len(file_pairs))

            for file_pair in file_pairs:
                # Support both (zh_path, en_path) and (zh_path, en_path, mod_id) formats
                if len(file_pair) == 3:
                    zh_path, en_path, mod_id = file_pair
                else:
                    zh_path, en_path = file_pair
                    mod_id = None

                stats = self.synchronize_file(Path(zh_path), Path(en_path), mod_id=mod_id)
                total_stats.merge(stats)

                progress.advance(task)

        return total_stats



def synchronize_language_file(zh_cn_path: str, en_us_path: str):
    """Legacy function for backward compatibility.

    Args:
        zh_cn_path: Path to Chinese language file
        en_us_path: Path to English language file
    """
    from uplang.logger import get_logger
    synchronizer = LanguageSynchronizer(get_logger())
    synchronizer.synchronize_file(Path(zh_cn_path), Path(en_us_path), mod_id=None)