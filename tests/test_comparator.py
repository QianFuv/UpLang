"""
Tests for language file comparator.
"""

from uplang.core.comparator import LanguageComparator


def test_compare_empty_dicts():
    """
    Test comparing two empty dictionaries.
    """
    comparator = LanguageComparator()
    result = comparator.compare({}, {})

    assert len(result.added) == 0
    assert len(result.modified) == 0
    assert len(result.deleted) == 0
    assert len(result.unchanged) == 0
    assert not result.has_changes


def test_compare_added_keys():
    """
    Test detecting added keys.
    """
    comparator = LanguageComparator()
    old_dict = {"key1": "value1"}
    new_dict = {"key1": "value1", "key2": "value2", "key3": "value3"}

    result = comparator.compare(old_dict, new_dict)

    assert result.added == {"key2", "key3"}
    assert len(result.modified) == 0
    assert len(result.deleted) == 0
    assert result.unchanged == {"key1"}
    assert result.has_changes


def test_compare_modified_keys():
    """
    Test detecting modified keys.
    """
    comparator = LanguageComparator()
    old_dict = {"key1": "old_value", "key2": "value2"}
    new_dict = {"key1": "new_value", "key2": "value2"}

    result = comparator.compare(old_dict, new_dict)

    assert len(result.added) == 0
    assert result.modified == {"key1"}
    assert len(result.deleted) == 0
    assert result.unchanged == {"key2"}
    assert result.has_changes


def test_compare_deleted_keys():
    """
    Test detecting deleted keys.
    """
    comparator = LanguageComparator()
    old_dict = {"key1": "value1", "key2": "value2", "key3": "value3"}
    new_dict = {"key1": "value1"}

    result = comparator.compare(old_dict, new_dict)

    assert len(result.added) == 0
    assert len(result.modified) == 0
    assert result.deleted == {"key2", "key3"}
    assert result.unchanged == {"key1"}
    assert result.has_changes


def test_compare_mixed_changes():
    """
    Test detecting mixed changes (added, modified, deleted).
    """
    comparator = LanguageComparator()
    old_dict = {"key1": "old_value", "key2": "value2", "key3": "value3"}
    new_dict = {"key1": "new_value", "key2": "value2", "key4": "value4"}

    result = comparator.compare(old_dict, new_dict)

    assert result.added == {"key4"}
    assert result.modified == {"key1"}
    assert result.deleted == {"key3"}
    assert result.unchanged == {"key2"}
    assert result.has_changes
    assert result.total_changes == 3
