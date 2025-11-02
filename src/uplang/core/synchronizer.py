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

        result_content = self._apply_changes(
            base=rp_en.content, source=mod_en.content, diff=diff
        )

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

        changed_keys = diff.added | diff.modified

        for key in rp_zh_content.keys():
            if key not in diff.deleted:
                if key in changed_keys:
                    if mod_zh and key in mod_zh.content:
                        result_content[key] = mod_zh.content[key]
                    else:
                        result_content[key] = mod_en.content[key]
                else:
                    result_content[key] = rp_zh_content[key]

        for key in diff.added:
            if key not in result_content:
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

    def _apply_changes(
        self, base: dict, source: dict, diff: DiffResult
    ) -> CommentedMap:
        """
        Apply changes to base dictionary while preserving key order.
        """
        result = CommentedMap()

        for key in base.keys():
            if key not in diff.deleted:
                result[key] = source.get(key, base[key])

        for key in diff.added:
            if key not in result:
                result[key] = source[key]

        return result
