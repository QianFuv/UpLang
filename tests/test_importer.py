"""
Tests for translation importer.
"""

import tempfile
from pathlib import Path
from zipfile import ZipFile

import pytest

from uplang.core.importer import ImportResult, TranslationImporter
from uplang.exceptions import UpLangError


@pytest.fixture
def temp_rp_dir():
    """
    Create a temporary resource pack directory.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        rp_path = Path(tmpdir)
        (rp_path / "assets").mkdir()
        yield rp_path


@pytest.fixture
def temp_zip_file():
    """
    Create a temporary zip file with test data.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "test.zip"

        with ZipFile(zip_path, "w") as zf:
            zf.writestr(
                "assets/testmod/lang/en_us.json",
                '{"key1": "value1", "key2": "value2", "key3": "value3"}',
            )
            zf.writestr(
                "assets/testmod/lang/zh_cn.json",
                '{"key1": "值1", "key2": "值2", "key3": "值3"}',
            )
            zf.writestr(
                "assets/anothermod/lang/zh_cn.json", '{"key1": "另一个值"}'
            )

        yield zip_path


@pytest.fixture
def importer():
    """
    Create a TranslationImporter instance.
    """
    return TranslationImporter()


def test_import_from_zip_basic(importer, temp_zip_file, temp_rp_dir):
    """
    Test basic import from zip file.
    """
    (temp_rp_dir / "assets" / "testmod" / "lang").mkdir(parents=True)
    en_file = temp_rp_dir / "assets" / "testmod" / "lang" / "en_us.json"
    en_file.write_text(
        '{"key1": "value1", "key2": "value2", "key3": "value3"}', encoding="utf-8"
    )

    zh_file = temp_rp_dir / "assets" / "testmod" / "lang" / "zh_cn.json"
    zh_file.write_text(
        '{"key1": "value1", "key2": "value2", "key3": "value3"}', encoding="utf-8"
    )

    result = importer.import_from_zip(temp_zip_file, temp_rp_dir)

    assert result.total_mods == 1
    assert result.keys_imported == 3
    assert len(result.errors) == 0

    import json

    zh_content = json.loads(zh_file.read_text(encoding="utf-8"))
    assert zh_content["key1"] == "值1"
    assert zh_content["key2"] == "值2"
    assert zh_content["key3"] == "值3"


def test_import_from_zip_only_untranslated(importer, temp_rp_dir):
    """
    Test import only fills untranslated keys.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "test.zip"

        with ZipFile(zip_path, "w") as zf:
            zf.writestr(
                "assets/testmod/lang/en_us.json",
                '{"key1": "value1", "key2": "value2", "key3": "value3"}',
            )
            zf.writestr(
                "assets/testmod/lang/zh_cn.json",
                '{"key1": "值1", "key2": "值2", "key3": "值3"}',
            )

        (temp_rp_dir / "assets" / "testmod" / "lang").mkdir(parents=True)
        en_file = temp_rp_dir / "assets" / "testmod" / "lang" / "en_us.json"
        en_file.write_text(
            '{"key1": "value1", "key2": "value2", "key3": "value3"}',
            encoding="utf-8",
        )

        zh_file = temp_rp_dir / "assets" / "testmod" / "lang" / "zh_cn.json"
        zh_file.write_text(
            '{"key1": "已翻译", "key2": "value2", "key3": "value3"}', encoding="utf-8"
        )

        result = importer.import_from_zip(zip_path, temp_rp_dir, overwrite=False)

        assert result.keys_imported == 2

        import json

        zh_content = json.loads(zh_file.read_text(encoding="utf-8"))
        assert zh_content["key1"] == "已翻译"
        assert zh_content["key2"] == "值2"
        assert zh_content["key3"] == "值3"


def test_import_from_zip_with_overwrite(importer, temp_rp_dir):
    """
    Test import with overwrite flag.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "test.zip"

        with ZipFile(zip_path, "w") as zf:
            zf.writestr(
                "assets/testmod/lang/en_us.json",
                '{"key1": "value1", "key2": "value2", "key3": "value3"}',
            )
            zf.writestr(
                "assets/testmod/lang/zh_cn.json",
                '{"key1": "值1", "key2": "值2", "key3": "值3"}',
            )

        (temp_rp_dir / "assets" / "testmod" / "lang").mkdir(parents=True)
        en_file = temp_rp_dir / "assets" / "testmod" / "lang" / "en_us.json"
        en_file.write_text(
            '{"key1": "value1", "key2": "value2", "key3": "value3"}',
            encoding="utf-8",
        )

        zh_file = temp_rp_dir / "assets" / "testmod" / "lang" / "zh_cn.json"
        zh_file.write_text('{"key1": "已翻译", "key2": "value2"}', encoding="utf-8")

        result = importer.import_from_zip(zip_path, temp_rp_dir, overwrite=True)

        assert result.keys_imported == 3

        import json

        zh_content = json.loads(zh_file.read_text(encoding="utf-8"))
        assert zh_content["key1"] == "值1"
        assert zh_content["key2"] == "值2"
        assert zh_content["key3"] == "值3"


def test_import_from_zip_dry_run(importer, temp_rp_dir):
    """
    Test dry run mode doesn't modify files.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "test.zip"

        with ZipFile(zip_path, "w") as zf:
            zf.writestr(
                "assets/testmod/lang/en_us.json",
                '{"key1": "value1", "key2": "value2", "key3": "value3"}',
            )
            zf.writestr(
                "assets/testmod/lang/zh_cn.json",
                '{"key1": "值1", "key2": "值2", "key3": "值3"}',
            )

        (temp_rp_dir / "assets" / "testmod" / "lang").mkdir(parents=True)
        en_file = temp_rp_dir / "assets" / "testmod" / "lang" / "en_us.json"
        en_file.write_text(
            '{"key1": "value1", "key2": "value2", "key3": "value3"}',
            encoding="utf-8",
        )

        zh_file_path = temp_rp_dir / "assets" / "testmod" / "lang" / "zh_cn.json"
        zh_file_path.write_text(
            '{"key1": "value1", "key2": "value2", "key3": "value3"}', encoding="utf-8"
        )

        result = importer.import_from_zip(zip_path, temp_rp_dir, dry_run=True)

        assert result.keys_imported == 3

        zh_content_after = zh_file_path.read_text(encoding="utf-8")
        assert zh_content_after == '{"key1": "value1", "key2": "value2", "key3": "value3"}'


def test_import_from_zip_no_english_file(importer, temp_rp_dir):
    """
    Test import when mod has no English file in resource pack.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "test.zip"

        with ZipFile(zip_path, "w") as zf:
            zf.writestr("assets/testmod/lang/zh_cn.json", '{"key1": "值1"}')

        result = importer.import_from_zip(zip_path, temp_rp_dir)

        assert result.total_mods == 0
        assert result.keys_imported == 0


def test_import_from_zip_invalid_file_path(importer, temp_rp_dir):
    """
    Test import with invalid file path format.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "test.zip"

        with ZipFile(zip_path, "w") as zf:
            zf.writestr("invalid/path/zh_cn.json", '{"key1": "值1"}')

        result = importer.import_from_zip(zip_path, temp_rp_dir)

        assert result.total_mods == 0


def test_import_from_zip_invalid_json(importer, temp_rp_dir):
    """
    Test import with invalid JSON in zip file.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "test.zip"

        with ZipFile(zip_path, "w") as zf:
            zf.writestr("assets/testmod/lang/zh_cn.json", "invalid json{")

        (temp_rp_dir / "assets" / "testmod" / "lang").mkdir(parents=True)
        en_file = temp_rp_dir / "assets" / "testmod" / "lang" / "en_us.json"
        en_file.write_text('{"key1": "value1"}', encoding="utf-8")

        result = importer.import_from_zip(zip_path, temp_rp_dir)

        assert result.total_mods == 1
        assert len(result.errors) == 1


def test_import_from_zip_missing_file(importer, temp_rp_dir):
    """
    Test import from non-existent zip file.
    """
    with pytest.raises(UpLangError):
        importer.import_from_zip(Path("nonexistent.zip"), temp_rp_dir)


def test_extract_mod_id_valid(importer):
    """
    Test extracting mod ID from valid file path.
    """
    mod_id = importer._extract_mod_id("assets/testmod/lang/zh_cn.json")
    assert mod_id == "testmod"


def test_extract_mod_id_invalid(importer):
    """
    Test extracting mod ID from invalid file path.
    """
    with pytest.raises(ValueError):
        importer._extract_mod_id("invalid/path/file.json")


def test_identify_keys_to_import_no_existing(importer):
    """
    Test identifying keys when no existing resource pack file.
    """
    zip_zh = {"key1": "值1", "key2": "值2"}

    keys = importer._identify_keys_to_import(zip_zh, None, None, False)

    assert keys == set()


def test_identify_keys_to_import_untranslated_only(importer):
    """
    Test identifying only untranslated keys.
    """
    from uplang.models import LanguageFile

    zip_zh = {"key1": "值1", "key2": "值2", "key3": "值3"}
    rp_en = LanguageFile(
        mod_id="test",
        lang_code="en_us",
        content={"key1": "value1", "key2": "value2", "key3": "value3"},
    )
    rp_zh = LanguageFile(
        mod_id="test",
        lang_code="zh_cn",
        content={"key1": "已翻译", "key2": "value2", "key3": "value3"},
    )

    keys = importer._identify_keys_to_import(zip_zh, rp_en, rp_zh, False)

    assert "key1" not in keys
    assert "key2" in keys
    assert "key3" in keys


def test_identify_keys_to_import_with_overwrite(importer):
    """
    Test identifying keys with overwrite flag.
    """
    zip_zh = {"key1": "值1", "key2": "值2"}

    keys = importer._identify_keys_to_import(zip_zh, None, None, True)

    assert keys == {"key1", "key2"}


def test_import_result_default():
    """
    Test ImportResult default values.
    """
    result = ImportResult()

    assert result.total_mods == 0
    assert result.keys_imported == 0
    assert result.keys_skipped == 0
    assert result.errors == []


def test_import_from_zip_no_keys_to_import(importer, temp_rp_dir):
    """
    Test import when all keys are already translated.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "test.zip"

        with ZipFile(zip_path, "w") as zf:
            zf.writestr("assets/testmod/lang/zh_cn.json", '{"key1": "值1"}')

        (temp_rp_dir / "assets" / "testmod" / "lang").mkdir(parents=True)
        en_file = temp_rp_dir / "assets" / "testmod" / "lang" / "en_us.json"
        en_file.write_text('{"key1": "value1"}', encoding="utf-8")

        zh_file = temp_rp_dir / "assets" / "testmod" / "lang" / "zh_cn.json"
        zh_file.write_text('{"key1": "已翻译"}', encoding="utf-8")

        result = importer.import_from_zip(zip_path, temp_rp_dir, overwrite=False)

        assert result.keys_imported == 0


def test_identify_keys_no_english_reference(importer):
    """
    Test identifying keys when no English reference exists.
    """
    from uplang.models import LanguageFile

    zip_zh = {"key1": "值1", "key2": "值2"}
    rp_zh = LanguageFile(
        mod_id="test", lang_code="zh_cn", content={"key1": "key1", "key2": "key2"}
    )

    keys = importer._identify_keys_to_import(zip_zh, None, rp_zh, False)

    assert keys == set()
