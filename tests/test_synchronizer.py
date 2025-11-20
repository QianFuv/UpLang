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

    result_file = synchronizer.synchronize_chinese(mod_en, mod_zh, mod_en, None, diff)

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

    result_file = synchronizer.synchronize_chinese(mod_en, None, mod_en, None, diff)

    assert result_file.content["key1"] == "value1"
    assert result_file.content["key2"] == "value2"


def test_synchronize_chinese_preserves_existing(synchronizer, mod_en, mod_zh):
    """
    Test that Chinese sync preserves existing translations.
    """
    rp_en = LanguageFile(
        mod_id="testmod",
        lang_code="en_us",
        content={"key1": "value1", "key2": "value2"},
        content_hash="hash_en",
    )
    rp_zh = LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={"key1": "已翻译1", "key2": "已翻译2"},
        content_hash="hash789",
    )
    diff = DiffResult(added={"key3"}, unchanged={"key1", "key2"})

    result_file = synchronizer.synchronize_chinese(mod_en, mod_zh, rp_en, rp_zh, diff)

    assert result_file.content["key1"] == "已翻译1"
    assert result_file.content["key2"] == "已翻译2"
    assert result_file.content["key3"] == "值3"


def test_synchronize_chinese_updates_modified_keys(synchronizer, mod_en, mod_zh):
    """
    Test that Chinese sync updates modified keys.
    """
    rp_en = LanguageFile(
        mod_id="testmod",
        lang_code="en_us",
        content={"key1": "old_value"},
        content_hash="hash_en",
    )
    rp_zh = LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={"key1": "旧翻译"},
        content_hash="hash789",
    )
    diff = DiffResult(modified={"key1"})

    result_file = synchronizer.synchronize_chinese(mod_en, mod_zh, rp_en, rp_zh, diff)

    assert result_file.content["key1"] == "值1"


def test_synchronize_chinese_removes_deleted_keys(synchronizer, mod_en, mod_zh):
    """
    Test that Chinese sync removes deleted keys.
    """
    rp_en = LanguageFile(
        mod_id="testmod",
        lang_code="en_us",
        content={"key1": "value1", "key2": "value2", "deleted_key": "deleted"},
        content_hash="hash_en",
    )
    rp_zh = LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={"key1": "值1", "key2": "值2", "deleted_key": "删除的键"},
        content_hash="hash789",
    )
    diff = DiffResult(deleted={"deleted_key"}, unchanged={"key1", "key2"})

    result_file = synchronizer.synchronize_chinese(mod_en, mod_zh, rp_en, rp_zh, diff)

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

    result_file = synchronizer.synchronize_chinese(mod_en, mod_zh, mod_en, None, diff)

    assert result_file.content["key1"] == "值1"
    assert result_file.content["key2"] == "value2"


def test_synchronize_chinese_mixed_changes(synchronizer, mod_en, mod_zh):
    """
    Test Chinese sync with mixed changes.
    """
    rp_en = LanguageFile(
        mod_id="testmod",
        lang_code="en_us",
        content={"key1": "value1", "key2": "old_value2", "old_key": "old"},
        content_hash="hash_en",
    )
    rp_zh = LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={"key1": "已翻译1", "key2": "已翻译2", "old_key": "旧键"},
        content_hash="hash789",
    )
    diff = DiffResult(
        added={"key3"}, modified={"key2"}, deleted={"old_key"}, unchanged={"key1"}
    )

    result_file = synchronizer.synchronize_chinese(mod_en, mod_zh, rp_en, rp_zh, diff)

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
    rp_en = LanguageFile(
        mod_id="testmod",
        lang_code="en_us",
        content={"key1": "old_value1", "key2": "old_value2"},
        content_hash="hash_en",
    )
    rp_zh = LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={"key1": "旧值1", "key2": "旧值2"},
        content_hash="hash3",
    )
    diff = DiffResult(modified={"key1", "key2"})

    result_file = synchronizer.synchronize_chinese(mod_en, mod_zh, rp_en, rp_zh, diff)

    assert result_file.content["key1"] == "new_value1"
    assert result_file.content["key2"] == "值2"


def test_apply_changes_preserves_order(synchronizer):
    """
    Test that _apply_changes uses source key order.
    """
    source = CommentedMap([("z", "new_last"), ("a", "first"), ("m", "middle")])

    result = synchronizer._apply_changes(source)

    assert list(result.keys()) == ["z", "a", "m"]
    assert result["z"] == "new_last"


def test_apply_changes_adds_new_keys(synchronizer):
    """
    Test that _apply_changes includes all source keys.
    """
    source = CommentedMap([("key1", "value1"), ("key2", "value2")])

    result = synchronizer._apply_changes(source)

    assert "key1" in result
    assert "key2" in result
    assert result["key2"] == "value2"


def test_apply_changes_removes_deleted_keys(synchronizer):
    """
    Test that _apply_changes only includes source keys.
    """
    source = CommentedMap([("key1", "value1")])

    result = synchronizer._apply_changes(source)

    assert "key1" in result
    assert "key2" not in result
    assert len(result) == 1


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
    rp_en = LanguageFile(
        mod_id="testmod",
        lang_code="en_us",
        content={"key1": "value1", "key2": "value2", "orphaned_key": "orphaned"},
        content_hash="hash_en",
    )
    rp_zh = LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={"key1": "已翻译1", "key2": "已翻译2", "orphaned_key": "孤立键"},
        content_hash="hash3",
    )
    diff = DiffResult(unchanged={"key1", "key2"})

    result_file = synchronizer.synchronize_chinese(mod_en, mod_zh, rp_en, rp_zh, diff)

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
    rp_en = LanguageFile(
        mod_id="testmod",
        lang_code="en_us",
        content={"key1": "value1", "key2": "value2", "key3": "value3"},
        content_hash="hash_en",
    )
    rp_zh = LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={"key1": "已翻译1"},
        content_hash="hash3",
    )
    diff = DiffResult(unchanged={"key1", "key2", "key3"})

    result_file = synchronizer.synchronize_chinese(mod_en, mod_zh, rp_en, rp_zh, diff)

    assert result_file.content["key1"] == "已翻译1"
    assert result_file.content["key2"] == "值2"
    assert result_file.content["key3"] == "value3"
    assert len(result_file.content) == 3


def test_synchronize_chinese_preserves_when_no_rp_en(synchronizer, mod_en):
    """
    Test that Chinese sync preserves existing translations when resource pack has no en_us.
    This is the bug fix for when resource pack only has zh_cn.
    """
    mod_zh = LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={"key1": "模组值1", "key2": "模组值2"},
        content_hash="hash2",
    )
    rp_zh = LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={"key1": "资源包翻译1", "key2": "资源包翻译2"},
        content_hash="hash3",
    )
    diff = DiffResult(added={"key1", "key2", "key3"})

    result_file = synchronizer.synchronize_chinese(mod_en, mod_zh, None, rp_zh, diff)

    assert result_file.content["key1"] == "资源包翻译1"
    assert result_file.content["key2"] == "资源包翻译2"
    assert result_file.content["key3"] == "value3"


def test_synchronize_chinese_as_primary_no_existing(synchronizer):
    """
    Test synchronizing Chinese as primary language when no resource pack file exists.
    """
    mod_zh = LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={"key1": "值1", "key2": "值2", "key3": "值3"},
        content_hash="hash123",
    )

    result_file, diff = synchronizer.synchronize_chinese_as_primary(mod_zh, None)

    assert result_file.mod_id == "testmod"
    assert result_file.lang_code == "zh_cn"
    assert result_file.content == mod_zh.content
    assert diff.added == {"key1", "key2", "key3"}
    assert len(diff.modified) == 0
    assert len(diff.deleted) == 0


def test_synchronize_chinese_as_primary_no_changes(synchronizer):
    """
    Test synchronizing Chinese as primary language with no changes.
    """
    mod_zh = LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={"key1": "值1", "key2": "值2"},
        content_hash="hash1",
    )
    rp_zh = LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={"key1": "值1", "key2": "值2"},
        content_hash="hash2",
    )

    result_file, diff = synchronizer.synchronize_chinese_as_primary(mod_zh, rp_zh)

    assert result_file.content == mod_zh.content
    assert len(diff.added) == 0
    assert len(diff.modified) == 0
    assert len(diff.deleted) == 0
    assert not diff.has_changes


def test_synchronize_chinese_as_primary_with_changes(synchronizer):
    """
    Test synchronizing Chinese as primary language with changes.
    """
    mod_zh = LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={"key1": "新值1", "key2": "值2", "key3": "值3"},
        content_hash="hash1",
    )
    rp_zh = LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={"key1": "旧值1", "key4": "值4"},
        content_hash="hash2",
    )

    result_file, diff = synchronizer.synchronize_chinese_as_primary(mod_zh, rp_zh)

    assert diff.added == {"key2", "key3"}
    assert diff.modified == {"key1"}
    assert diff.deleted == {"key4"}
    assert result_file.content["key1"] == "新值1"
    assert result_file.content["key2"] == "值2"
    assert result_file.content["key3"] == "值3"
    assert "key4" not in result_file.content


def test_reorder_by_reference_basic(synchronizer):
    """
    Test basic key reordering to match reference dictionary.
    """
    target = CommentedMap([("z", "last"), ("a", "first"), ("m", "middle")])
    reference = CommentedMap([("a", "ref1"), ("m", "ref2"), ("z", "ref3")])

    result = synchronizer.reorder_by_reference(target, reference)

    assert list(result.keys()) == ["a", "m", "z"]
    assert result["a"] == "first"
    assert result["m"] == "middle"
    assert result["z"] == "last"


def test_reorder_by_reference_extra_keys_in_target(synchronizer):
    """
    Test reordering when target has extra keys not in reference.
    """
    target = CommentedMap([("key1", "值1"), ("key2", "值2"), ("key3", "值3")])
    reference = CommentedMap([("key1", "value1"), ("key3", "value3")])

    result = synchronizer.reorder_by_reference(target, reference)

    assert list(result.keys()) == ["key1", "key3", "key2"]
    assert result["key1"] == "值1"
    assert result["key2"] == "值2"
    assert result["key3"] == "值3"


def test_reorder_by_reference_extra_keys_in_reference(synchronizer):
    """
    Test reordering when reference has keys not in target.
    """
    target = CommentedMap([("key1", "值1"), ("key2", "值2")])
    reference = CommentedMap(
        [("key1", "value1"), ("key2", "value2"), ("key3", "value3")]
    )

    result = synchronizer.reorder_by_reference(target, reference)

    assert list(result.keys()) == ["key1", "key2"]
    assert result["key1"] == "值1"
    assert result["key2"] == "值2"
    assert "key3" not in result


def test_reorder_by_reference_empty_reference(synchronizer):
    """
    Test reordering with empty reference dictionary.
    """
    target = CommentedMap([("key1", "值1"), ("key2", "值2")])
    reference = CommentedMap()

    result = synchronizer.reorder_by_reference(target, reference)

    assert list(result.keys()) == ["key1", "key2"]
    assert result["key1"] == "值1"
    assert result["key2"] == "值2"


def test_reorder_by_reference_empty_target(synchronizer):
    """
    Test reordering with empty target dictionary.
    """
    target = CommentedMap()
    reference = CommentedMap([("key1", "value1"), ("key2", "value2")])

    result = synchronizer.reorder_by_reference(target, reference)

    assert len(result) == 0


def test_reorder_by_reference_preserves_values(synchronizer):
    """
    Test that reordering preserves all values from target.
    """
    target = CommentedMap(
        [("z", "最后"), ("a", "第一"), ("m", "中间"), ("extra", "额外")]
    )
    reference = CommentedMap([("a", "first"), ("m", "middle"), ("z", "last")])

    result = synchronizer.reorder_by_reference(target, reference)

    assert result["z"] == "最后"
    assert result["a"] == "第一"
    assert result["m"] == "中间"
    assert result["extra"] == "额外"


def test_synchronize_chinese_no_rp_en_with_missing_keys(synchronizer):
    """
    Test Chinese sync when rp_en is None and keys missing from rp_zh but present in mod_zh.
    This covers line 74 in synchronizer.py.
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
        content={"key1": "模组值1", "key2": "模组值2", "key3": "模组值3"},
        content_hash="hash2",
    )
    rp_zh = LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={"key1": "资源包翻译1"},
        content_hash="hash3",
    )
    diff = DiffResult(added={"key1", "key2", "key3"})

    result_file = synchronizer.synchronize_chinese(mod_en, mod_zh, None, rp_zh, diff)

    assert result_file.content["key1"] == "资源包翻译1"
    assert result_file.content["key2"] == "模组值2"
    assert result_file.content["key3"] == "模组值3"
