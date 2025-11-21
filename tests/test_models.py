"""
Tests for data models.
"""

from pathlib import Path

from uplang.models import DiffResult, LanguageFile, Mod, ModType, SyncResult


def test_mod_creation():
    """
    Test creating a Mod instance.
    """
    mod = Mod(
        mod_id="examplemod",
        name="Example Mod",
        version="1.0.0",
        jar_path=Path("examplemod-1.0.0.jar"),
        mod_type=ModType.FORGE,
    )

    assert mod.mod_id == "examplemod"
    assert mod.name == "Example Mod"
    assert mod.version == "1.0.0"
    assert mod.mod_type == ModType.FORGE
    assert "Example Mod" in str(mod)


def test_diff_result_has_changes():
    """
    Test DiffResult.has_changes property.
    """
    diff_empty = DiffResult()
    assert not diff_empty.has_changes

    diff_with_added = DiffResult(added={"key1"})
    assert diff_with_added.has_changes

    diff_with_modified = DiffResult(modified={"key1"})
    assert diff_with_modified.has_changes

    diff_with_deleted = DiffResult(deleted={"key1"})
    assert diff_with_deleted.has_changes


def test_diff_result_total_changes():
    """
    Test DiffResult.total_changes property.
    """
    diff = DiffResult(added={"k1", "k2"}, modified={"k3"}, deleted={"k4", "k5", "k6"})

    assert diff.total_changes == 6
    assert len(diff.added) == 2
    assert len(diff.modified) == 1
    assert len(diff.deleted) == 3


def test_sync_result_success():
    """
    Test SyncResult for successful sync.
    """
    result = SyncResult(
        mod_id="examplemod",
        success=True,
        added_keys=5,
        modified_keys=3,
        deleted_keys=2,
    )

    assert result.success
    assert not result.skipped
    assert result.total_changes == 10
    assert "examplemod" in str(result)


def test_sync_result_skipped():
    """
    Test SyncResult for skipped sync.
    """
    result = SyncResult(mod_id="examplemod", skipped=True)

    assert result.success
    assert result.skipped
    assert result.total_changes == 0
    assert "skipped" in str(result)


def test_sync_result_failed():
    """
    Test SyncResult for failed sync.
    """
    result = SyncResult(mod_id="examplemod", success=False, error="Test error")

    assert not result.success
    assert result.error == "Test error"
    assert "failed" in str(result)


def test_diff_result_str():
    """
    Test DiffResult string representation.
    """
    diff = DiffResult(added={"k1", "k2"}, modified={"k3"}, deleted={"k4"})
    result_str = str(diff)

    assert "+2" in result_str
    assert "~1" in result_str
    assert "-1" in result_str


def test_language_file_creation():
    """
    Test creating a LanguageFile instance.
    """
    lang_file = LanguageFile(
        mod_id="testmod",
        lang_code="en_us",
        content={"key1": "value1", "key2": "value2"},
        content_hash="abc123",
    )

    assert lang_file.mod_id == "testmod"
    assert lang_file.lang_code == "en_us"
    assert len(lang_file.content) == 2
    assert lang_file.content_hash == "abc123"


def test_language_file_str_with_content():
    """
    Test LanguageFile string representation with content.
    """
    lang_file = LanguageFile(
        mod_id="testmod",
        lang_code="en_us",
        content={"key1": "value1", "key2": "value2", "key3": "value3"},
        content_hash="abc123",
    )

    result_str = str(lang_file)

    assert "testmod" in result_str
    assert "en_us" in result_str
    assert "3 keys" in result_str


def test_language_file_str_with_empty_content():
    """
    Test LanguageFile string representation with empty content.
    """
    lang_file = LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={},
        content_hash=None,
    )

    result_str = str(lang_file)

    assert "testmod" in result_str
    assert "zh_cn" in result_str
    assert "0 keys" in result_str
