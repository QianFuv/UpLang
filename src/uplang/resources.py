"""
Resource management utilities with context managers
"""

import zipfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from uplang.exceptions import FileSystemError, handle_errors
from uplang.models import Mod


class ResourceManager:
    """Enhanced resource management with proper lifecycle handling"""

    @staticmethod
    @contextmanager
    def jar_file(mod: Mod) -> Generator[zipfile.ZipFile, None, None]:
        """Context manager for JAR file access"""
        jar_file = None
        try:
            jar_file = zipfile.ZipFile(mod.file_path, 'r')
            yield jar_file
        except (zipfile.BadZipFile, OSError) as e:
            raise FileSystemError(
                f"Failed to open JAR file: {mod.file_path}",
                context={'mod_id': mod.mod_id, 'file_path': str(mod.file_path)},
                cause=e
            )
        finally:
            if jar_file:
                jar_file.close()

    @staticmethod
    @contextmanager
    def multiple_jar_files(mods: list[Mod]) -> Generator[dict[str, zipfile.ZipFile], None, None]:
        """Context manager for multiple JAR files"""
        jar_files = {}
        try:
            for mod in mods:
                try:
                    jar_files[mod.mod_id] = zipfile.ZipFile(mod.file_path, 'r')
                except (zipfile.BadZipFile, OSError):
                    # Skip problematic files but continue with others
                    continue
            yield jar_files
        finally:
            for jar_file in jar_files.values():
                try:
                    jar_file.close()
                except Exception:
                    # Ignore cleanup errors
                    pass

    @staticmethod
    @contextmanager
    @handle_errors(FileSystemError)
    def safe_write_file(file_path: Path, backup: bool = True) -> Generator[Path, None, None]:
        """Context manager for safe file writing with backup"""
        backup_path = None
        temp_path = file_path.with_suffix(file_path.suffix + '.tmp')

        try:
            # Create backup if file exists and backup is requested
            if backup and file_path.exists():
                backup_path = file_path.with_suffix(file_path.suffix + '.backup')
                file_path.rename(backup_path)

            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            yield temp_path

            # Move temp file to final location
            temp_path.rename(file_path)

            # Remove backup on success
            if backup_path and backup_path.exists():
                backup_path.unlink()

        except Exception as e:
            # Cleanup temp file
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)

            # Restore backup if available
            if backup_path and backup_path.exists():
                backup_path.rename(file_path)

            raise FileSystemError(
                f"Failed to write file safely: {file_path}",
                context={'temp_path': str(temp_path), 'backup_path': str(backup_path)},
                cause=e
            )

    @staticmethod
    @contextmanager
    def batch_file_operations(file_paths: list[Path], backup: bool = True) -> Generator[dict[Path, Path], None, None]:
        """Context manager for batch file operations with rollback capability"""
        operations = {}
        backups = {}

        try:
            # Prepare all operations
            for file_path in file_paths:
                temp_path = file_path.with_suffix(file_path.suffix + '.tmp')
                operations[file_path] = temp_path

                if backup and file_path.exists():
                    backup_path = file_path.with_suffix(file_path.suffix + '.backup')
                    file_path.rename(backup_path)
                    backups[file_path] = backup_path

            yield operations

            # Commit all operations
            for original_path, temp_path in operations.items():
                if temp_path.exists():
                    temp_path.rename(original_path)

            # Remove backups on success
            for backup_path in backups.values():
                if backup_path.exists():
                    backup_path.unlink()

        except Exception as e:
            # Rollback all operations
            for original_path, temp_path in operations.items():
                if temp_path.exists():
                    temp_path.unlink(missing_ok=True)

            # Restore backups
            for original_path, backup_path in backups.items():
                if backup_path.exists():
                    backup_path.rename(original_path)

            raise FileSystemError(
                f"Batch file operations failed, rolled back {len(operations)} operations",
                context={'operations_count': len(operations), 'backups_count': len(backups)},
                cause=e
            )


@contextmanager
def managed_jar_access(mod: Mod) -> Generator[zipfile.ZipFile, None, None]:
    """Convenience function for JAR file access"""
    with ResourceManager.jar_file(mod) as jar:
        yield jar


@contextmanager
def managed_file_write(file_path: Path, backup: bool = True) -> Generator[Path, None, None]:
    """Convenience function for safe file writing"""
    with ResourceManager.safe_write_file(file_path, backup) as temp_path:
        yield temp_path