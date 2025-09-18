"""
Check command implementation
"""

from pathlib import Path

from uplang.commands.base import BaseCommand, CommandResult
from uplang.core.scanner import ModScanner
from uplang.core.extractor import LanguageExtractor
from uplang.core.synchronizer import LanguageSynchronizer
from uplang.core.state import StateManager
from uplang.exceptions import UpLangError, StateError


class CheckCommand(BaseCommand):

    def execute(self) -> CommandResult:
        """Execute the check command"""
        try:
            self.logger.section("Checking for Mod Updates")

            scanner = ModScanner(self.logger)
            extractor = LanguageExtractor(self.logger)
            synchronizer = LanguageSynchronizer(self.logger)
            state_manager = StateManager(self.logger)

            self.logger.subsection("Loading previous state")
            previous_state = state_manager.load_state(self.config.state_file)
            if not previous_state:
                return CommandResult(False, "No previous state found. Run 'uplang init' first.")

            self._validate_directories(previous_state)

            self.logger.subsection("Scanning current mods")
            current_mods = scanner.scan_directory(self.config.mods_directory)

            self.logger.subsection("Comparing with previous state")
            comparison = state_manager.compare_mods(current_mods, previous_state)

            if not comparison.has_changes:
                self.logger.info("No mod changes detected")
            else:
                self._process_changes(comparison, extractor, synchronizer)

            self.logger.subsection("Synchronizing all language files")
            sync_stats = self._synchronize_all_files(current_mods, synchronizer)

            self.logger.subsection("Saving state")
            state_manager.save_state(
                current_mods,
                self.config.state_file,
                self.config.mods_directory,
                self.config.resource_pack_directory
            )

            self._report_results(comparison, sync_stats, current_mods)

            return CommandResult(
                True,
                f"Check completed: {comparison.total_changes} mod changes, "
                f"{sync_stats.total_changes} key changes"
            )

        except UpLangError as e:
            return CommandResult(False, str(e))
        except Exception as e:
            self.logger.error(f"Unexpected error during check: {e}")
            return CommandResult(False, f"Unexpected error: {e}")

    def _validate_directories(self, previous_state):
        """Validate that directories match the previous state"""
        project_info = previous_state.get("project_info", {})

        old_mods_dir = project_info.get("mods_directory")
        if old_mods_dir and old_mods_dir != str(self.config.mods_directory):
            self.logger.warning(f"Mods directory changed: {old_mods_dir} -> {self.config.mods_directory}")

        old_rp_dir = project_info.get("resource_pack_directory")
        if old_rp_dir and old_rp_dir != str(self.config.resource_pack_directory):
            self.logger.warning(f"Resource pack directory changed: {old_rp_dir} -> {self.config.resource_pack_directory}")

    def _process_changes(self, comparison, extractor, synchronizer):
        """Process mod changes"""
        if comparison.new_mods:
            self.logger.info(f"Processing {len(comparison.new_mods)} new mods")
            for mod in comparison.new_mods:
                self._process_new_mod(mod, extractor)

        if comparison.updated_mods:
            self.logger.info(f"Processing {len(comparison.updated_mods)} updated mods")
            for mod in comparison.updated_mods:
                self._process_updated_mod(mod, extractor, synchronizer)

        if comparison.deleted_mods:
            self.logger.info(f"Found {len(comparison.deleted_mods)} deleted mods")

    def _process_new_mod(self, mod, extractor):
        """Process a new mod"""
        # First check if the mod has language files
        en_us_result = extractor.extract_language_file(mod, "en_us")
        if not en_us_result:
            self.logger.debug(f"No language files found for new mod {mod.display_name}, skipping")
            return

        # Only create directories if we have language files
        target_dir = self.config.resource_pack_directory / "assets" / mod.mod_id / "lang"
        target_dir.mkdir(parents=True, exist_ok=True)

        lang_path, content = en_us_result
        mod.has_lang_files = True
        mod.lang_files["en_us"] = lang_path

        en_us_path = target_dir / "en_us.json"
        zh_cn_path = target_dir / "zh_cn.json"

        with open(en_us_path, 'wb') as f:
            f.write(content)
        with open(zh_cn_path, 'wb') as f:
            f.write(content)

        self.logger.debug(f"Added new mod: {mod.display_name}")

    def _process_updated_mod(self, mod, extractor, synchronizer):
        """Process an updated mod"""
        en_us_result = extractor.extract_language_file(mod, "en_us")
        if not en_us_result:
            return

        _, content = en_us_result
        target_dir = self.config.resource_pack_directory / "assets" / mod.mod_id / "lang"
        en_us_path = target_dir / "en_us.json"
        zh_cn_path = target_dir / "zh_cn.json"

        # Update English file
        with open(en_us_path, 'wb') as f:
            f.write(content)

        # Try to extract Chinese translations from JAR
        zh_translations = None
        zh_cn_result = extractor.extract_language_file(mod, "zh_cn")
        if zh_cn_result:
            from uplang.json_utils import read_json_robust
            import tempfile

            # Write Chinese content to temporary file and read it
            _, zh_content = zh_cn_result
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.json', delete=False) as tmp_file:
                tmp_file.write(zh_content)
                tmp_path = Path(tmp_file.name)

            try:
                zh_translations = read_json_robust(tmp_path, self.logger)
                if zh_translations:
                    self.logger.debug(f"Found Chinese translations in {mod.display_name}")
            finally:
                tmp_path.unlink(missing_ok=True)

        # Synchronize with Chinese translations if available
        synchronizer.synchronize_file(zh_cn_path, en_us_path, zh_translations)
        self.logger.debug(f"Updated mod: {mod.display_name}")

    def _synchronize_all_files(self, mods, synchronizer):
        """Synchronize all language files"""
        file_pairs = []
        for mod in mods:
            target_dir = self.config.resource_pack_directory / "assets" / mod.mod_id / "lang"
            zh_cn_path = target_dir / "zh_cn.json"
            en_us_path = target_dir / "en_us.json"

            if en_us_path.exists():
                file_pairs.append((zh_cn_path, en_us_path))

        return synchronizer.synchronize_multiple(file_pairs)

    def _report_results(self, comparison, sync_stats, current_mods):
        """Report check results"""
        if comparison.has_changes:
            changes_data = []
            if comparison.new_mods:
                for mod in comparison.new_mods:
                    changes_data.append(["NEW", mod.display_name, mod.version])
            if comparison.updated_mods:
                for mod in comparison.updated_mods:
                    changes_data.append(["UPDATED", mod.display_name, mod.version])
            if comparison.deleted_mods:
                for mod in comparison.deleted_mods:
                    changes_data.append(["DELETED", mod.display_name, mod.version])

            self.logger.table("Mod Changes", ["Status", "Mod", "Version"], changes_data)

        if sync_stats.has_changes:
            self.logger.success(
                f"Synchronized {sync_stats.files_processed} files: "
                f"+{sync_stats.keys_added} -{sync_stats.keys_removed} keys"
            )

        unrecognized_mods = [mod for mod in current_mods if not mod.is_recognized]
        if unrecognized_mods:
            self.logger.subsection("Unrecognized Mods")
            for mod in unrecognized_mods:
                self.logger.warning(f"  {mod.display_name} ({mod.file_path.name})")

        self.logger.info(f"Log saved to: {self.logger.get_log_file()}")