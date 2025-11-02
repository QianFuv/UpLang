"""
Language file comparator using set operations.
"""

from uplang.models import DiffResult


class LanguageComparator:
    """
    Compare two language files and identify differences.
    """

    def compare(self, old_dict: dict, new_dict: dict) -> DiffResult:
        """
        Compare two language files using efficient set operations.
        """
        old_keys = set(old_dict.keys())
        new_keys = set(new_dict.keys())

        added = new_keys - old_keys
        deleted = old_keys - new_keys
        common_keys = old_keys & new_keys
        modified = {k for k in common_keys if old_dict[k] != new_dict[k]}
        unchanged = common_keys - modified

        return DiffResult(
            added=added, modified=modified, deleted=deleted, unchanged=unchanged
        )
