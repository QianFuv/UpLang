"""Business logic for web translation interface."""

from pathlib import Path
from typing import Any

from uplang.core.extractor import LanguageExtractor
from uplang.models import LanguageFile
from uplang.utils.json_handler import JSONHandler


class TranslationService:
    """Service for managing translations in web interface."""

    def __init__(self, resourcepack_dir: Path):
        self.resourcepack_dir = Path(resourcepack_dir)
        self.extractor = LanguageExtractor()
        self.json_handler = JSONHandler()

    def get_all_mods(self) -> list[dict[str, Any]]:
        """Get all mods in resource pack with untranslated counts."""
        mods_info = []
        assets_dir = self.resourcepack_dir / "assets"

        if not assets_dir.exists():
            return []

        for mod_dir in assets_dir.iterdir():
            if not mod_dir.is_dir():
                continue

            mod_id = mod_dir.name
            lang_dir = mod_dir / "lang"

            if not lang_dir.exists():
                continue

            en_file_path = lang_dir / "en_us.json"
            if not en_file_path.exists():
                continue

            untranslated_count = self._count_untranslated(mod_id)

            try:
                en_content = self.json_handler.load(en_file_path)
                total_keys = len(en_content)
            except Exception:
                total_keys = 0

            mods_info.append(
                {
                    "mod_id": mod_id,
                    "total_keys": total_keys,
                    "untranslated_count": untranslated_count,
                    "translated_count": total_keys - untranslated_count,
                }
            )

        return sorted(mods_info, key=lambda x: x["mod_id"])

    def get_untranslated_items(self, mod_id: str) -> list[dict[str, Any]]:
        """Get all untranslated items for a mod."""
        untranslated_items = []

        try:
            en_file = self.extractor.load_from_resource_pack(
                self.resourcepack_dir, mod_id, "en_us"
            )
            zh_file = self.extractor.load_from_resource_pack(
                self.resourcepack_dir, mod_id, "zh_cn"
            )
        except Exception:
            return []

        if not en_file:
            return []

        zh_content = zh_file.content if zh_file else {}

        for key, en_value in en_file.content.items():
            zh_value = zh_content.get(key)

            if zh_value is None or zh_value == en_value:
                untranslated_items.append(
                    {
                        "key": key,
                        "english": en_value,
                        "chinese": zh_value if zh_value else "",
                    }
                )

        return untranslated_items

    def get_all_items(self, mod_id: str) -> list[dict[str, Any]]:
        """Get all translation items for a mod (both translated and untranslated)."""
        all_items = []

        try:
            en_file = self.extractor.load_from_resource_pack(
                self.resourcepack_dir, mod_id, "en_us"
            )
            zh_file = self.extractor.load_from_resource_pack(
                self.resourcepack_dir, mod_id, "zh_cn"
            )
        except Exception:
            return []

        if not en_file:
            return []

        zh_content = zh_file.content if zh_file else {}

        for key, en_value in en_file.content.items():
            zh_value = zh_content.get(key, "")
            is_translated = zh_value and zh_value != en_value

            all_items.append(
                {
                    "key": key,
                    "english": en_value,
                    "chinese": zh_value,
                    "is_translated": is_translated,
                }
            )

        return all_items

    def save_translations(self, mod_id: str, translations: dict[str, str]) -> bool:
        """Save translations for a mod."""
        try:
            en_file = self.extractor.load_from_resource_pack(
                self.resourcepack_dir, mod_id, "en_us"
            )
            if not en_file:
                return False

            zh_file = self.extractor.load_from_resource_pack(
                self.resourcepack_dir, mod_id, "zh_cn"
            )

            zh_content = zh_file.content.copy() if zh_file else {}

            zh_content.update(translations)

            reordered_content = self._reorder_by_reference(zh_content, en_file.content)

            zh_lang_file = LanguageFile(
                mod_id=mod_id,
                lang_code="zh_cn",
                content=reordered_content,
                content_hash=None,
            )

            self.extractor.save_to_resource_pack(self.resourcepack_dir, zh_lang_file)

            return True
        except Exception as e:
            print(f"Error saving translations: {e}")
            return False

    def _count_untranslated(self, mod_id: str) -> int:
        """Count untranslated items for a mod."""
        try:
            en_file = self.extractor.load_from_resource_pack(
                self.resourcepack_dir, mod_id, "en_us"
            )
            zh_file = self.extractor.load_from_resource_pack(
                self.resourcepack_dir, mod_id, "zh_cn"
            )
        except Exception:
            return 0

        if not en_file:
            return 0

        zh_content = zh_file.content if zh_file else {}
        untranslated_count = 0

        for key, en_value in en_file.content.items():
            zh_value = zh_content.get(key)
            if zh_value is None or zh_value == en_value:
                untranslated_count += 1

        return untranslated_count

    def _reorder_by_reference(
        self, target: dict[str, str], reference: dict[str, str]
    ) -> dict[str, str]:
        """Reorder target dict keys to match reference dict order."""
        reordered = {}

        for key in reference:
            if key in target:
                reordered[key] = target[key]

        for key in target:
            if key not in reordered:
                reordered[key] = target[key]

        return reordered
