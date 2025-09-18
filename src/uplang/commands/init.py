"""
Init command implementation.

This module implements the initialization command that sets up
a new UpLang project by scanning mods and creating the resource pack structure.
"""

import shutil
from pathlib import Path

from uplang.commands.base import BaseCommand, CommandResult
from uplang.exceptions import UpLangError, handle_errors


class InitCommand(BaseCommand):
    """Command to initialize a new UpLang project."""

    @handle_errors(UpLangError)
    def execute(self) -> CommandResult:
        """Execute the init command with enhanced dependency injection.

        This method performs a complete initialization of the project,
        including mod scanning, resource pack setup, and state saving.

        Returns:
            CommandResult indicating success/failure and processing summary
        """
        try:
            if not self._ensure_directories():
                return CommandResult(False, "Failed to create required directories")

            self.logger.section("Initializing UpLang Project")

            # Get services from container
            scanner = self.container.get_scanner()
            extractor = self.container.get_extractor()
            synchronizer = self.container.get_synchronizer()
            state_manager = self.container.get_state_manager()

            self.logger.subsection("Scanning mods")
            current_mods = scanner.scan_directory(self.config.mods_directory)

            if not current_mods:
                return CommandResult(False, "No mods found in directory")

            self.logger.subsection("Cleaning up resource pack")
            self._cleanup_resource_pack(current_mods)

            self.logger.subsection("Processing mods")
            processed_count = 0
            for mod in current_mods:
                if self._process_mod(mod, extractor, synchronizer):
                    processed_count += 1

            self.logger.subsection("Final cleanup")
            self._cleanup_mods_without_lang_files(current_mods)

            self.logger.subsection("Saving state")
            state_manager.save_state(
                current_mods,
                self.config.state_file,
                self.config.mods_directory,
                self.config.resource_pack_directory
            )

            self._report_results(current_mods, processed_count)

            return CommandResult(
                True,
                f"Successfully initialized with {processed_count} mods"
            )

        except UpLangError as e:
            return CommandResult(False, str(e))
        except Exception as e:
            self.logger.error(f"Unexpected error during initialization: {e}")
            return CommandResult(False, f"Unexpected error: {e}")

    def _cleanup_resource_pack(self, current_mods):
        """Remove assets for deleted mods and mods without language files.

        Args:
            current_mods: List of currently detected mods
        """
        assets_dir = self.config.resource_pack_directory / "assets"
        if not assets_dir.exists():
            return

        # Get mod IDs that have language files
        current_mod_ids_with_lang = set()
        current_mod_ids_all = {mod.mod_id for mod in current_mods}

        # We'll determine which mods have language files after processing
        # For now, collect existing directories
        existing_mod_dirs = set()
        for mod_dir in assets_dir.iterdir():
            if mod_dir.is_dir() and (mod_dir / "lang").exists():
                existing_mod_dirs.add(mod_dir.name)

        # Remove directories for mods that no longer exist at all
        deleted_mod_ids = existing_mod_dirs - current_mod_ids_all
        if deleted_mod_ids:
            self.logger.info(f"Removing {len(deleted_mod_ids)} deleted mod assets")
            for mod_id in deleted_mod_ids:
                mod_asset_dir = assets_dir / mod_id
                try:
                    shutil.rmtree(mod_asset_dir)
                    self.logger.debug(f"Removed assets for deleted mod: {mod_id}")
                except OSError as e:
                    self.logger.warning(f"Failed to remove {mod_asset_dir}: {e}")

    def _cleanup_mods_without_lang_files(self, current_mods):
        """Remove assets for mods that don't have language files.

        Args:
            current_mods: List of currently detected mods
        """
        assets_dir = self.config.resource_pack_directory / "assets"
        if not assets_dir.exists():
            return

        # Get mod IDs that have language files
        mod_ids_with_lang = {mod.mod_id for mod in current_mods if mod.has_lang_files}

        # Find existing directories for mods that no longer have language files
        mods_to_cleanup = []
        for mod_dir in assets_dir.iterdir():
            if (mod_dir.is_dir() and
                (mod_dir / "lang").exists() and
                mod_dir.name not in mod_ids_with_lang):
                # Check if this mod exists but has no language files
                mod_exists = any(mod.mod_id == mod_dir.name for mod in current_mods)
                if mod_exists:
                    mods_to_cleanup.append(mod_dir.name)

        if mods_to_cleanup:
            self.logger.info(f"Removing {len(mods_to_cleanup)} mod assets without language files")
            for mod_id in mods_to_cleanup:
                mod_asset_dir = assets_dir / mod_id
                try:
                    shutil.rmtree(mod_asset_dir)
                    self.logger.debug(f"Removed assets for mod without language files: {mod_id}")
                except OSError as e:
                    self.logger.warning(f"Failed to remove {mod_asset_dir}: {e}")

    def _process_mod(self, mod, extractor, synchronizer) -> bool:
        """Process a single mod by extracting and synchronizing language files.

        Args:
            mod: Mod object to process
            extractor: Language file extractor service
            synchronizer: Language file synchronizer service

        Returns:
            True if mod was processed successfully, False if skipped
        """
        # First check if the mod has any language files before creating directories
        en_us_result = extractor.extract_language_file(mod, "en_us")
        if not en_us_result:
            self.logger.debug(f"No language files found for {mod.display_name}, skipping")
            return False

        # Only create directories if we have language files
        target_dir = self.config.resource_pack_directory / "assets" / mod.mod_id / "lang"
        target_dir.mkdir(parents=True, exist_ok=True)

        self._cleanup_old_lang_files(target_dir)

        en_us_path = target_dir / "en_us.json"
        zh_cn_path = target_dir / "zh_cn.json"

        # Extract and write en_us.json
        lang_path, content = en_us_result
        mod.has_lang_files = True
        mod.lang_files["en_us"] = lang_path

        with open(en_us_path, 'wb') as f:
            f.write(content)

        # Handle zh_cn.json
        if not zh_cn_path.exists():
            zh_cn_result = extractor.extract_language_file(mod, "zh_cn")
            if zh_cn_result:
                zh_lang_path, zh_content = zh_cn_result
                mod.lang_files["zh_cn"] = zh_lang_path
                with open(zh_cn_path, 'wb') as f:
                    f.write(zh_content)
            else:
                with open(zh_cn_path, 'wb') as f:
                    f.write(content)

        synchronizer.synchronize_file(zh_cn_path, en_us_path)
        return True

    def _cleanup_old_lang_files(self, target_dir: Path):
        """Remove old language files except en_us.json and zh_cn.json.

        Args:
            target_dir: Directory containing language files to clean
        """
        for file_path in target_dir.glob("*.json"):
            if file_path.name not in ["en_us.json", "zh_cn.json"]:
                try:
                    file_path.unlink()
                    self.logger.debug(f"Removed old language file: {file_path.name}")
                except OSError as e:
                    self.logger.warning(f"Failed to remove {file_path}: {e}")

    def _report_results(self, mods, processed_count):
        """Report initialization results including statistics and warnings.

        Args:
            mods: List of all detected mods
            processed_count: Number of mods successfully processed
        """
        unrecognized_mods = [mod for mod in mods if not mod.is_recognized]
        mods_without_lang = [mod for mod in mods if not mod.has_lang_files]

        self.logger.success(f"Processed {processed_count} mods with language files out of {len(mods)} total mods")

        if mods_without_lang:
            self.logger.info(f"Skipped {len(mods_without_lang)} mods without language files")

        if unrecognized_mods:
            self.logger.subsection("Unrecognized Mods")
            for mod in unrecognized_mods:
                lang_status = "with language files" if mod.has_lang_files else "no language files"
                self.logger.warning(f"  {mod.display_name} ({mod.file_path.name}) - {lang_status}")

        self.logger.info(f"Log saved to: {self.logger.get_log_file()}")