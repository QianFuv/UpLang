"""
Tests for language file extractor.
"""

import json
from zipfile import ZipFile

import pytest

from uplang.core.extractor import LanguageExtractor
from uplang.exceptions import LanguageFileError
from uplang.models import Mod, ModType


@pytest.fixture
def extractor():
    """
    Create a LanguageExtractor instance.
    """
    return LanguageExtractor()


@pytest.fixture
def test_mod(tmp_path):
    """
    Create a test mod with language files.
    """
    jar_path = tmp_path / "testmod-1.0.0.jar"

    en_us_content = {"key1": "value1", "key2": "value2"}
    zh_cn_content = {"key1": "值1", "key2": "值2"}

    with ZipFile(jar_path, "w") as jar:
        jar.writestr(
            "assets/testmod/lang/en_us.json", json.dumps(en_us_content, indent=2)
        )
        jar.writestr(
            "assets/testmod/lang/zh_cn.json", json.dumps(zh_cn_content, indent=2)
        )

    return Mod(
        mod_id="testmod",
        name="Test Mod",
        version="1.0.0",
        jar_path=jar_path,
        mod_type=ModType.FORGE,
    )


@pytest.fixture
def mod_without_zh(tmp_path):
    """
    Create a test mod without Chinese language file.
    """
    jar_path = tmp_path / "mod-en-only-1.0.0.jar"

    en_us_content = {"key1": "value1"}

    with ZipFile(jar_path, "w") as jar:
        jar.writestr("assets/modenonly/lang/en_us.json", json.dumps(en_us_content))

    return Mod(
        mod_id="modenonly",
        name="Mod EN Only",
        version="1.0.0",
        jar_path=jar_path,
        mod_type=ModType.FORGE,
    )


@pytest.fixture
def mod_with_data_path(tmp_path):
    """
    Create a test mod with language files in data path.
    """
    jar_path = tmp_path / "datamod-1.0.0.jar"

    en_us_content = {"key1": "value1"}

    with ZipFile(jar_path, "w") as jar:
        jar.writestr("data/datamod/lang/en_us.json", json.dumps(en_us_content))

    return Mod(
        mod_id="datamod",
        name="Data Mod",
        version="1.0.0",
        jar_path=jar_path,
        mod_type=ModType.FORGE,
    )


def test_extract_language_files_both_languages(extractor, test_mod):
    """
    Test extracting both English and Chinese language files.
    """
    result = extractor.extract_language_files(test_mod)

    assert "en_us" in result
    assert "zh_cn" in result
    assert result["en_us"].mod_id == "testmod"
    assert result["zh_cn"].mod_id == "testmod"
    assert result["en_us"].content["key1"] == "value1"
    assert result["zh_cn"].content["key1"] == "值1"


def test_extract_language_files_english_only(extractor, mod_without_zh):
    """
    Test extracting when only English file exists.
    """
    result = extractor.extract_language_files(mod_without_zh)

    assert "en_us" in result
    assert "zh_cn" not in result


def test_extract_language_files_custom_lang_codes(extractor, test_mod):
    """
    Test extracting with custom language codes.
    """
    result = extractor.extract_language_files(test_mod, lang_codes=["en_us"])

    assert "en_us" in result
    assert "zh_cn" not in result


def test_extract_language_files_from_data_path(extractor, mod_with_data_path):
    """
    Test extracting language files from data path.
    """
    result = extractor.extract_language_files(mod_with_data_path)

    assert "en_us" in result
    assert result["en_us"].content["key1"] == "value1"


def test_extract_language_files_no_files(extractor, tmp_path):
    """
    Test extracting from a mod with no language files.
    """
    jar_path = tmp_path / "empty-1.0.0.jar"

    with ZipFile(jar_path, "w") as jar:
        jar.writestr("dummy.txt", "content")

    mod = Mod(
        mod_id="empty",
        name="Empty Mod",
        version="1.0.0",
        jar_path=jar_path,
        mod_type=ModType.FORGE,
    )

    result = extractor.extract_language_files(mod)

    assert len(result) == 0


def test_extract_single_language_assets_path(extractor, test_mod):
    """
    Test extracting a single language file from assets path.
    """
    with ZipFile(test_mod.jar_path, "r") as jar:
        lang_file = extractor._extract_single_language(jar, test_mod, "en_us")

    assert lang_file is not None
    assert lang_file.lang_code == "en_us"
    assert lang_file.content["key1"] == "value1"


def test_extract_single_language_not_found(extractor, test_mod):
    """
    Test extracting a non-existent language file.
    """
    with ZipFile(test_mod.jar_path, "r") as jar:
        lang_file = extractor._extract_single_language(jar, test_mod, "fr_fr")

    assert lang_file is None


def test_load_from_resource_pack(extractor, tmp_path):
    """
    Test loading a language file from resource pack.
    """
    resourcepack_dir = tmp_path / "resourcepack"
    lang_file_path = resourcepack_dir / "assets" / "testmod" / "lang" / "en_us.json"
    lang_file_path.parent.mkdir(parents=True, exist_ok=True)

    content = {"key1": "value1", "key2": "value2"}
    lang_file_path.write_text(json.dumps(content), encoding="utf-8")

    lang_file = extractor.load_from_resource_pack(resourcepack_dir, "testmod", "en_us")

    assert lang_file is not None
    assert lang_file.mod_id == "testmod"
    assert lang_file.lang_code == "en_us"
    assert lang_file.content == content


def test_load_from_resource_pack_not_found(extractor, tmp_path):
    """
    Test loading a non-existent language file from resource pack.
    """
    resourcepack_dir = tmp_path / "resourcepack"

    lang_file = extractor.load_from_resource_pack(resourcepack_dir, "testmod", "en_us")

    assert lang_file is None


def test_load_from_resource_pack_invalid_json(extractor, tmp_path):
    """
    Test loading an invalid JSON file from resource pack.
    """
    resourcepack_dir = tmp_path / "resourcepack"
    lang_file_path = resourcepack_dir / "assets" / "testmod" / "lang" / "en_us.json"
    lang_file_path.parent.mkdir(parents=True, exist_ok=True)
    lang_file_path.write_text("invalid json{", encoding="utf-8")

    with pytest.raises(LanguageFileError):
        extractor.load_from_resource_pack(resourcepack_dir, "testmod", "en_us")


def test_save_to_resource_pack(extractor, tmp_path):
    """
    Test saving a language file to resource pack.
    """
    from uplang.models import LanguageFile

    resourcepack_dir = tmp_path / "resourcepack"
    lang_file = LanguageFile(
        mod_id="testmod",
        lang_code="en_us",
        content={"key1": "value1", "key2": "value2"},
        content_hash="hash123",
    )

    extractor.save_to_resource_pack(resourcepack_dir, lang_file)

    expected_path = resourcepack_dir / "assets" / "testmod" / "lang" / "en_us.json"
    assert expected_path.exists()

    loaded = extractor.load_from_resource_pack(resourcepack_dir, "testmod", "en_us")
    assert loaded.content == lang_file.content


def test_save_to_resource_pack_creates_directories(extractor, tmp_path):
    """
    Test that save creates necessary directories.
    """
    from uplang.models import LanguageFile

    resourcepack_dir = tmp_path / "new_resourcepack"
    lang_file = LanguageFile(
        mod_id="newmod",
        lang_code="zh_cn",
        content={"key": "值"},
        content_hash="hash456",
    )

    extractor.save_to_resource_pack(resourcepack_dir, lang_file)

    expected_path = resourcepack_dir / "assets" / "newmod" / "lang" / "zh_cn.json"
    assert expected_path.exists()
    assert expected_path.parent.exists()


def test_extract_language_files_with_unicode(extractor, tmp_path):
    """
    Test extracting language files with unicode content.
    """
    jar_path = tmp_path / "unicode-1.0.0.jar"

    content = {
        "chinese": "中文测试",
        "japanese": "日本語テスト",
        "emoji": "😀🎮",
    }

    with ZipFile(jar_path, "w") as jar:
        jar.writestr(
            "assets/unicode/lang/en_us.json",
            json.dumps(content, indent=2, ensure_ascii=False),
        )

    mod = Mod(
        mod_id="unicode",
        name="Unicode Mod",
        version="1.0.0",
        jar_path=jar_path,
        mod_type=ModType.FORGE,
    )

    result = extractor.extract_language_files(mod, lang_codes=["en_us"])

    assert "en_us" in result
    assert result["en_us"].content["chinese"] == "中文测试"
    assert result["en_us"].content["japanese"] == "日本語テスト"
    assert result["en_us"].content["emoji"] == "😀🎮"


def test_extract_language_files_empty_json(extractor, tmp_path):
    """
    Test extracting empty language files.
    """
    jar_path = tmp_path / "empty-lang-1.0.0.jar"

    with ZipFile(jar_path, "w") as jar:
        jar.writestr("assets/emptylang/lang/en_us.json", "{}")

    mod = Mod(
        mod_id="emptylang",
        name="Empty Lang Mod",
        version="1.0.0",
        jar_path=jar_path,
        mod_type=ModType.FORGE,
    )

    result = extractor.extract_language_files(mod)

    assert "en_us" in result
    assert result["en_us"].content == {}


def test_save_to_resource_pack_unicode(extractor, tmp_path):
    """
    Test saving unicode content to resource pack.
    """
    from uplang.models import LanguageFile

    resourcepack_dir = tmp_path / "resourcepack"
    lang_file = LanguageFile(
        mod_id="testmod",
        lang_code="zh_cn",
        content={"test": "中文测试", "emoji": "😀"},
        content_hash="hash789",
    )

    extractor.save_to_resource_pack(resourcepack_dir, lang_file)

    loaded = extractor.load_from_resource_pack(resourcepack_dir, "testmod", "zh_cn")
    assert loaded.content["test"] == "中文测试"
    assert loaded.content["emoji"] == "😀"


def test_extract_language_files_corrupted_jar(extractor, tmp_path):
    """
    Test extracting from a corrupted JAR file.
    """
    jar_path = tmp_path / "corrupted.jar"
    jar_path.write_bytes(b"This is not a valid ZIP file")

    mod = Mod(
        mod_id="corrupted",
        name="Corrupted Mod",
        version="1.0.0",
        jar_path=jar_path,
        mod_type=ModType.FORGE,
    )

    with pytest.raises(LanguageFileError) as exc_info:
        extractor.extract_language_files(mod)

    assert "Failed to extract language files" in str(exc_info.value)


def test_extract_single_language_invalid_json_continues(extractor, tmp_path):
    """
    Test that _extract_single_language handles invalid JSON gracefully.
    """
    jar_path = tmp_path / "invalid_lang.jar"

    with ZipFile(jar_path, "w") as jar:
        jar.writestr("assets/testmod/lang/en_us.json", "invalid json {")

    mod = Mod(
        mod_id="testmod",
        name="Test Mod",
        version="1.0.0",
        jar_path=jar_path,
        mod_type=ModType.FORGE,
    )

    with ZipFile(jar_path, "r") as jar:
        result = extractor._extract_single_language(jar, mod, "en_us")

    assert result is None


def test_save_to_resource_pack_write_failure(extractor, tmp_path, monkeypatch):
    """
    Test that save_to_resource_pack raises LanguageFileError on write failure.
    """
    from uplang.models import LanguageFile
    from uplang.utils.json_handler import JSONHandler

    def mock_dump_failure(data, path):
        raise OSError("Permission denied")

    resourcepack_dir = tmp_path / "resourcepack"
    lang_file = LanguageFile(
        mod_id="testmod",
        lang_code="en_us",
        content={"key": "value"},
        content_hash="hash123",
    )

    monkeypatch.setattr(JSONHandler, "dump", mock_dump_failure)

    with pytest.raises(LanguageFileError) as exc_info:
        extractor.save_to_resource_pack(resourcepack_dir, lang_file)

    assert "Failed to save language file" in str(exc_info.value)
