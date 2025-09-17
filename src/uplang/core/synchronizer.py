"""
Language file synchronization functionality
"""

import json
from pathlib import Path
from typing import Dict, Any

from rich.progress import Progress, BarColumn, TextColumn, TaskProgressColumn

from uplang.exceptions import SynchronizationError
from uplang.logger import UpLangLogger
from uplang.models import SyncStats
from uplang.json_utils import read_json_robust, write_json_safe


class LanguageSynchronizer:

    def __init__(self, logger: UpLangLogger):
        self.logger = logger

    def synchronize_file(self, zh_cn_path: Path, en_us_path: Path) -> SyncStats:
        """Synchronize a Chinese language file with its English counterpart"""
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

            zh_data = {}
            if zh_cn_path.exists():
                loaded_data = read_json_robust(zh_cn_path, self.logger)
                if isinstance(loaded_data, dict):
                    zh_data = loaded_data
                else:
                    self.logger.warning(f"Invalid Chinese file format: {zh_cn_path}")

            keys_to_add = {key: value for key, value in en_data.items() if key not in zh_data}
            keys_to_remove = {key for key in zh_data if key not in en_data}

            if keys_to_add or keys_to_remove:
                for key, value in keys_to_add.items():
                    zh_data[key] = value
                    stats.keys_added += 1

                for key in keys_to_remove:
                    del zh_data[key]
                    stats.keys_removed += 1

                write_json_safe(zh_cn_path, zh_data, self.logger)
                self.logger.debug(f"Synchronized {zh_cn_path}: +{stats.keys_added} -{stats.keys_removed}")

            stats.files_processed += 1
            return stats

        except Exception as e:
            self.logger.error(f"Failed to synchronize {zh_cn_path}: {e}")
            stats.errors += 1
            return stats

    def synchronize_multiple(self, file_pairs: list) -> SyncStats:
        """Synchronize multiple language file pairs with progress tracking"""
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

            for zh_path, en_path in file_pairs:
                stats = self.synchronize_file(Path(zh_path), Path(en_path))
                total_stats.keys_added += stats.keys_added
                total_stats.keys_removed += stats.keys_removed
                total_stats.files_processed += stats.files_processed
                total_stats.files_skipped += stats.files_skipped
                total_stats.errors += stats.errors

                progress.advance(task)

        return total_stats



def synchronize_language_file(zh_cn_path: str, en_us_path: str):
    """Legacy function for backward compatibility"""
    from uplang.logger import get_logger
    synchronizer = LanguageSynchronizer(get_logger())
    synchronizer.synchronize_file(Path(zh_cn_path), Path(en_us_path))