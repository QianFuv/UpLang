"""
Tests for language file synchronizer.
"""

import pytest
from ruamel.yaml.comments import CommentedMap

from uplang.core.synchronizer import LanguageSynchronizer
from uplang.models import LanguageFile, DiffResult


@pytest.fixture
def synchronizer():
    """
    Create a LanguageSynchronizer instance.
    """
    return LanguageSynchronizer()


@pytest.fixture
def mod_en():
    """
    Create a sample mod English language file.
    """
    return LanguageFile(
        mod_id="testmod",
        lang_code="en_us",
        content={"key1": "value1", "key2": "value2", "key3": "value3"},
        content_hash="hash123",
    )


@pytest.fixture
def mod_zh():
    """
    Create a sample mod Chinese language file.
    """
    return LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={"key1": "值1", "key2": "值2", "key3": "值3"},
        content_hash="hash456",
    )


def test_synchronize_english_no_existing(synchronizer, mod_en):
    """
    Test synchronizing English when no resource pack file exists.
    """
    result_file, diff = synchronizer.synchronize_english(mod_en, None)

    assert result_file.mod_id == "testmod"
    assert result_file.lang_code == "en_us"
    assert result_file.content == mod_en.content
    assert diff.added == {"key1", "key2", "key3"}
    assert len(diff.modified) == 0
    assert len(diff.deleted) == 0


def test_synchronize_english_no_changes(synchronizer, mod_en):
    """
    Test synchronizing English with no changes.
    """
    rp_en = LanguageFile(
        mod_id="testmod",
        lang_code="en_us",
        content={"key1": "value1", "key2": "value2", "key3": "value3"},
        content_hash="hash123",
    )

    result_file, diff = synchronizer.synchronize_english(mod_en, rp_en)

    assert result_file.content == mod_en.content
    assert len(diff.added) == 0
    assert len(diff.modified) == 0
    assert len(diff.deleted) == 0
    assert not diff.has_changes


def test_synchronize_english_with_additions(synchronizer):
    """
    Test synchronizing English with added keys.
    """
    mod_en = LanguageFile(
        mod_id="testmod",
        lang_code="en_us",
        content={"key1": "value1", "key2": "value2", "key3": "value3"},
        content_hash="hash1",
    )
    rp_en = LanguageFile(
        mod_id="testmod",
        lang_code="en_us",
        content={"key1": "value1"},
        content_hash="hash2",
    )

    result_file, diff = synchronizer.synchronize_english(mod_en, rp_en)

    assert diff.added == {"key2", "key3"}
    assert "key2" in result_file.content
    assert "key3" in result_file.content


def test_synchronize_english_with_modifications(synchronizer):
    """
    Test synchronizing English with modified keys.
    """
    mod_en = LanguageFile(
        mod_id="testmod",
        lang_code="en_us",
        content={"key1": "new_value"},
        content_hash="hash1",
    )
    rp_en = LanguageFile(
        mod_id="testmod",
        lang_code="en_us",
        content={"key1": "old_value"},
        content_hash="hash2",
    )

    result_file, diff = synchronizer.synchronize_english(mod_en, rp_en)

    assert diff.modified == {"key1"}
    assert result_file.content["key1"] == "new_value"


def test_synchronize_english_with_deletions(synchronizer):
    """
    Test synchronizing English with deleted keys.
    """
    mod_en = LanguageFile(
        mod_id="testmod",
        lang_code="en_us",
        content={"key1": "value1"},
        content_hash="hash1",
    )
    rp_en = LanguageFile(
        mod_id="testmod",
        lang_code="en_us",
        content={"key1": "value1", "key2": "value2"},
        content_hash="hash2",
    )

    result_file, diff = synchronizer.synchronize_english(mod_en, rp_en)

    assert diff.deleted == {"key2"}
    assert "key2" not in result_file.content


def test_synchronize_chinese_no_existing(synchronizer, mod_en, mod_zh):
    """
    Test synchronizing Chinese when no resource pack file exists.
    """
    diff = DiffResult(added={"key1", "key2", "key3"})

    result_file = synchronizer.synchronize_chinese(mod_en, mod_zh, None, diff)

    assert result_file.mod_id == "testmod"
    assert result_file.lang_code == "zh_cn"
    assert result_file.content["key1"] == "值1"
    assert result_file.content["key2"] == "值2"
    assert result_file.content["key3"] == "值3"


def test_synchronize_chinese_no_mod_zh(synchronizer, mod_en):
    """
    Test synchronizing Chinese when mod has no Chinese file.
    """
    diff = DiffResult(added={"key1", "key2"})

    result_file = synchronizer.synchronize_chinese(mod_en, None, None, diff)

    assert result_file.content["key1"] == "value1"
    assert result_file.content["key2"] == "value2"


def test_synchronize_chinese_preserves_existing(synchronizer, mod_en, mod_zh):
    """
    Test that Chinese sync preserves existing translations.
    """
    rp_zh = LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={"key1": "已翻译1", "key2": "已翻译2"},
        content_hash="hash789",
    )
    diff = DiffResult(added={"key3"}, unchanged={"key1", "key2"})

    result_file = synchronizer.synchronize_chinese(mod_en, mod_zh, rp_zh, diff)

    assert result_file.content["key1"] == "已翻译1"
    assert result_file.content["key2"] == "已翻译2"
    assert result_file.content["key3"] == "值3"


def test_synchronize_chinese_updates_modified_keys(synchronizer, mod_en, mod_zh):
    """
    Test that Chinese sync updates modified keys.
    """
    rp_zh = LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={"key1": "旧翻译"},
        content_hash="hash789",
    )
    diff = DiffResult(modified={"key1"})

    result_file = synchronizer.synchronize_chinese(mod_en, mod_zh, rp_zh, diff)

    assert result_file.content["key1"] == "值1"


def test_synchronize_chinese_removes_deleted_keys(synchronizer, mod_en, mod_zh):
    """
    Test that Chinese sync removes deleted keys.
    """
    rp_zh = LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={"key1": "值1", "key2": "值2", "deleted_key": "删除的键"},
        content_hash="hash789",
    )
    diff = DiffResult(deleted={"deleted_key"}, unchanged={"key1", "key2"})

    result_file = synchronizer.synchronize_chinese(mod_en, mod_zh, rp_zh, diff)

    assert "key1" in result_file.content
    assert "key2" in result_file.content
    assert "deleted_key" not in result_file.content


def test_synchronize_chinese_uses_english_fallback(synchronizer, mod_en):
    """
    Test that Chinese sync uses English when Chinese key is missing.
    """
    mod_zh = LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={"key1": "值1"},
        content_hash="hash456",
    )
    diff = DiffResult(added={"key1", "key2"})

    result_file = synchronizer.synchronize_chinese(mod_en, mod_zh, None, diff)

    assert result_file.content["key1"] == "值1"
    assert result_file.content["key2"] == "value2"


def test_synchronize_chinese_mixed_changes(synchronizer, mod_en, mod_zh):
    """
    Test Chinese sync with mixed changes.
    """
    rp_zh = LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={"key1": "已翻译1", "key2": "已翻译2", "old_key": "旧键"},
        content_hash="hash789",
    )
    diff = DiffResult(
        added={"key3"}, modified={"key2"}, deleted={"old_key"}, unchanged={"key1"}
    )

    result_file = synchronizer.synchronize_chinese(mod_en, mod_zh, rp_zh, diff)

    assert result_file.content["key1"] == "已翻译1"
    assert result_file.content["key2"] == "值2"
    assert result_file.content["key3"] == "值3"
    assert "old_key" not in result_file.content


def test_synchronize_chinese_changed_key_missing_in_mod_zh(synchronizer):
    """
    Test that Chinese sync uses English fallback when changed key is missing in mod_zh.
    """
    mod_en = LanguageFile(
        mod_id="testmod",
        lang_code="en_us",
        content={"key1": "new_value1", "key2": "value2"},
        content_hash="hash1",
    )
    mod_zh = LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={"key2": "值2"},
        content_hash="hash2",
    )
    rp_zh = LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={"key1": "旧值1", "key2": "旧值2"},
        content_hash="hash3",
    )
    diff = DiffResult(modified={"key1", "key2"})

    result_file = synchronizer.synchronize_chinese(mod_en, mod_zh, rp_zh, diff)

    assert result_file.content["key1"] == "new_value1"
    assert result_file.content["key2"] == "值2"


def test_apply_changes_preserves_order(synchronizer):
    """
    Test that _apply_changes preserves key order.
    """
    base = CommentedMap([("z", "last"), ("a", "first"), ("m", "middle")])
    source = CommentedMap([("z", "new_last"), ("a", "first"), ("m", "middle")])
    diff = DiffResult(modified={"z"})

    result = synchronizer._apply_changes(base, source, diff)

    assert list(result.keys()) == ["z", "a", "m"]
    assert result["z"] == "new_last"


def test_apply_changes_adds_new_keys(synchronizer):
    """
    Test that _apply_changes adds new keys.
    """
    base = CommentedMap([("key1", "value1")])
    source = CommentedMap([("key1", "value1"), ("key2", "value2")])
    diff = DiffResult(added={"key2"})

    result = synchronizer._apply_changes(base, source, diff)

    assert "key2" in result
    assert result["key2"] == "value2"


def test_apply_changes_removes_deleted_keys(synchronizer):
    """
    Test that _apply_changes removes deleted keys.
    """
    base = CommentedMap([("key1", "value1"), ("key2", "value2")])
    source = CommentedMap([("key1", "value1")])
    diff = DiffResult(deleted={"key2"})

    result = synchronizer._apply_changes(base, source, diff)

    assert "key1" in result
    assert "key2" not in result


def test_synchronize_chinese_removes_orphaned_keys(synchronizer):
    """
    Test that Chinese sync removes keys that exist in zh_cn but not in en_us.
    This is the bug fix for keys that exist in Chinese files but not in English files.
    """
    mod_en = LanguageFile(
        mod_id="testmod",
        lang_code="en_us",
        content={"key1": "value1", "key2": "value2"},
        content_hash="hash1",
    )
    mod_zh = LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={"key1": "值1", "key2": "值2", "orphaned_key": "孤立键"},
        content_hash="hash2",
    )
    rp_zh = LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={"key1": "已翻译1", "key2": "已翻译2", "orphaned_key": "孤立键"},
        content_hash="hash3",
    )
    diff = DiffResult(unchanged={"key1", "key2"})

    result_file = synchronizer.synchronize_chinese(mod_en, mod_zh, rp_zh, diff)

    assert "key1" in result_file.content
    assert "key2" in result_file.content
    assert "orphaned_key" not in result_file.content
    assert len(result_file.content) == 2


def test_synchronize_chinese_adds_missing_keys(synchronizer):
    """
    Test that Chinese sync adds keys that exist in en_us but not in rp_zh.
    If mod_zh has the key, use it; otherwise use English fallback.
    """
    mod_en = LanguageFile(
        mod_id="testmod",
        lang_code="en_us",
        content={"key1": "value1", "key2": "value2", "key3": "value3"},
        content_hash="hash1",
    )
    mod_zh = LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={"key1": "值1", "key2": "值2"},
        content_hash="hash2",
    )
    rp_zh = LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={"key1": "已翻译1"},
        content_hash="hash3",
    )
    diff = DiffResult(unchanged={"key1", "key2", "key3"})

    result_file = synchronizer.synchronize_chinese(mod_en, mod_zh, rp_zh, diff)

    assert result_file.content["key1"] == "已翻译1"
    assert result_file.content["key2"] == "值2"
    assert result_file.content["key3"] == "value3"
    assert len(result_file.content) == 3
