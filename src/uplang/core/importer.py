"""
Translation importer for importing from resource pack zip files.
"""

from dataclasses import dataclass, field
from pathlib import Path
from zipfile import ZipFile

from uplang.core.extractor import LanguageExtractor
from uplang.exceptions import UpLangError
from uplang.models import LanguageFile
from uplang.utils import calculate_dict_hash
from uplang.utils.output import print_info, print_success, print_verbose


@dataclass
class ImportResult:
    """
    Result of importing translations.
    """

    total_mods: int = 0
    keys_imported: int = 0
    keys_skipped: int = 0
    keys_unchanged: int = 0
    errors: list[str] = field(default_factory=list)


class TranslationImporter:
    """
    Import translations from resource pack zip files.
    """

    def __init__(self):
        self.extractor = LanguageExtractor()

    def import_from_zip(
        self,
        zip_path: Path,
        resourcepack_dir: Path,
        dry_run: bool = False,
        overwrite: bool = False,
    ) -> ImportResult:
        """
        Import translations from a resource pack zip file.
        """
        result = ImportResult()

        try:
            with ZipFile(zip_path, "r") as zip_file:
                zh_files = [
                    name
                    for name in zip_file.namelist()
                    if name.startswith("assets/") and "/lang/zh_cn.json" in name
                ]

                result.total_mods = len(zh_files)
                print_verbose(f"Found {len(zh_files)} Chinese translation files in zip")

                for zh_file_path in zh_files:
                    try:
                        mod_id = self._extract_mod_id(zh_file_path)
                        self._import_mod_translations(
                            zip_file,
                            zh_file_path,
                            mod_id,
                            resourcepack_dir,
                            result,
                            dry_run,
                            overwrite,
                        )
                    except Exception as e:
                        error_msg = f"{zh_file_path}: {e}"
                        result.errors.append(error_msg)
                        print_verbose(f"Error: {error_msg}")

        except Exception as e:
            raise UpLangError(f"Failed to read zip file: {e}") from e

        return result

    def _extract_mod_id(self, file_path: str) -> str:
        """
        Extract mod ID from file path like 'assets/modid/lang/zh_cn.json'.
        """
        parts = file_path.split("/")
        if len(parts) >= 4 and parts[0] == "assets" and parts[2] == "lang":
            return parts[1]
        raise ValueError(f"Invalid file path format: {file_path}")

    def _import_mod_translations(
        self,
        zip_file: ZipFile,
        zh_file_path: str,
        mod_id: str,
        resourcepack_dir: Path,
        result: ImportResult,
        dry_run: bool,
        overwrite: bool,
    ) -> None:
        """
        Import translations for a single mod.
        """
        rp_en = self.extractor.load_from_resource_pack(
            resourcepack_dir, mod_id, "en_us"
        )

        if rp_en is None:
            print_verbose(f"{mod_id}: Skipped (mod not in resource pack)")
            result.total_mods -= 1
            return

        with zip_file.open(zh_file_path) as f:
            zip_zh_content = self.extractor.json_handler.load_from_bytes(f.read())

        rp_zh = self.extractor.load_from_resource_pack(
            resourcepack_dir, mod_id, "zh_cn"
        )

        keys_to_import = self._identify_keys_to_import(
            zip_zh_content,
            rp_en,
            rp_zh,
            overwrite,
        )

        if not keys_to_import:
            print_verbose(f"{mod_id}: No keys to import")
            return

        merged_zh_content = {}

        if rp_zh:
            merged_zh_content = dict(rp_zh.content)

        keys_changed = 0
        for key in keys_to_import:
            if key in zip_zh_content:
                old_value = merged_zh_content.get(key)
                new_value = zip_zh_content[key]
                merged_zh_content[key] = new_value

                if old_value == new_value:
                    result.keys_unchanged += 1
                else:
                    keys_changed += 1
                    result.keys_imported += 1

        if rp_en:
            from uplang.core.synchronizer import LanguageSynchronizer

            synchronizer = LanguageSynchronizer()
            merged_zh_content = synchronizer.reorder_by_reference(
                merged_zh_content, rp_en.content
            )

        if not dry_run:
            if keys_changed > 0:
                merged_zh = LanguageFile(
                    mod_id=mod_id,
                    lang_code="zh_cn",
                    content=merged_zh_content,
                    content_hash=calculate_dict_hash(merged_zh_content),
                )
                self.extractor.save_to_resource_pack(resourcepack_dir, merged_zh)
                print_success(f"{mod_id}: Imported {keys_changed} keys")
            else:
                print_verbose(
                    f"{mod_id}: All {len(keys_to_import)} keys already "
                    "have correct values"
                )
        else:
            if keys_changed > 0:
                print_info(f"{mod_id}: Would import {keys_changed} keys")
            else:
                print_verbose(
                    f"{mod_id}: All {len(keys_to_import)} keys already "
                    "have correct values"
                )

    def _identify_keys_to_import(
        self,
        zip_zh_content: dict,
        rp_en: LanguageFile | None,
        rp_zh: LanguageFile | None,
        overwrite: bool,
    ) -> set[str]:
        """
        Identify which keys should be imported.
        """
        if overwrite:
            return set(zip_zh_content.keys())

        if rp_en is None or rp_zh is None:
            return set()

        keys_to_import = set()

        for key in zip_zh_content:
            if (
                key in rp_en.content
                and key in rp_zh.content
                and rp_zh.content[key] == rp_en.content[key]
            ):
                keys_to_import.add(key)

        return keys_to_import
