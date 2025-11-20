"""
Language file synchronizer.
"""

from ruamel.yaml.comments import CommentedMap

from uplang.core.comparator import LanguageComparator
from uplang.models import DiffResult, LanguageFile


class LanguageSynchronizer:
    """
    Synchronize language files while preserving key order and format.
    """

    def __init__(self):
        self.comparator = LanguageComparator()

    def synchronize_english(
        self, mod_en: LanguageFile, rp_en: LanguageFile | None
    ) -> tuple[LanguageFile, DiffResult]:
        """
        Synchronize English language file from mod to resource pack.
        """
        if rp_en is None:
            diff = DiffResult(
                added=set(mod_en.content.keys()),
                modified=set(),
                deleted=set(),
                unchanged=set(),
            )
            return mod_en, diff

        diff = self.comparator.compare(rp_en.content, mod_en.content)

        result_content = self._apply_changes(source=mod_en.content)

        from uplang.utils import calculate_dict_hash

        return (
            LanguageFile(
                mod_id=mod_en.mod_id,
                lang_code="en_us",
                content=result_content,
                content_hash=calculate_dict_hash(result_content),
            ),
            diff,
        )

    def synchronize_chinese(
        self,
        mod_en: LanguageFile,
        mod_zh: LanguageFile | None,
        rp_en: LanguageFile | None,
        rp_zh: LanguageFile | None,
        diff: DiffResult,
    ) -> LanguageFile:
        """
        Synchronize Chinese language file.
        """
        result_content = CommentedMap()

        if rp_zh is None:
            rp_zh_content = {}
        else:
            rp_zh_content = rp_zh.content

        if rp_en is None and rp_zh is not None:
            for key in mod_en.content.keys():
                if key in rp_zh_content:
                    result_content[key] = rp_zh_content[key]
                else:
                    if mod_zh and key in mod_zh.content:
                        result_content[key] = mod_zh.content[key]
                    else:
                        result_content[key] = mod_en.content[key]
        else:
            changed_keys = diff.added | diff.modified

            for key in mod_en.content.keys():
                if key in changed_keys:
                    if mod_zh and key in mod_zh.content:
                        result_content[key] = mod_zh.content[key]
                    else:
                        result_content[key] = mod_en.content[key]
                elif key in rp_zh_content:
                    result_content[key] = rp_zh_content[key]
                else:
                    if mod_zh and key in mod_zh.content:
                        result_content[key] = mod_zh.content[key]
                    else:
                        result_content[key] = mod_en.content[key]

        from uplang.utils import calculate_dict_hash

        return LanguageFile(
            mod_id=mod_en.mod_id,
            lang_code="zh_cn",
            content=result_content,
            content_hash=calculate_dict_hash(result_content),
        )

    def synchronize_chinese_as_primary(
        self, mod_zh: LanguageFile, rp_zh: LanguageFile | None
    ) -> tuple[LanguageFile, DiffResult]:
        """
        Synchronize Chinese language file when it's the primary language.
        """
        if rp_zh is None:
            diff = DiffResult(
                added=set(mod_zh.content.keys()),
                modified=set(),
                deleted=set(),
                unchanged=set(),
            )
            return mod_zh, diff

        diff = self.comparator.compare(rp_zh.content, mod_zh.content)

        result_content = self._apply_changes(source=mod_zh.content)

        from uplang.utils import calculate_dict_hash

        return (
            LanguageFile(
                mod_id=mod_zh.mod_id,
                lang_code="zh_cn",
                content=result_content,
                content_hash=calculate_dict_hash(result_content),
            ),
            diff,
        )

    def _apply_changes(self, source: dict) -> CommentedMap:
        """
        Apply changes using source content and key order.
        """
        result = CommentedMap()

        for key, value in source.items():
            result[key] = value

        return result

    def reorder_by_reference(
        self, target: dict, reference: dict
    ) -> CommentedMap:
        """
        Reorder target dictionary keys to match reference dictionary order.
        """
        result = CommentedMap()

        for key in reference.keys():
            if key in target:
                result[key] = target[key]

        for key in target.keys():
            if key not in result:
                result[key] = target[key]

        return result
