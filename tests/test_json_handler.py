"""
Tests for JSON handler.
"""

import pytest
from pathlib import Path
from uplang.utils.json_handler import JSONHandler
from uplang.exceptions import JSONParseError, LanguageFileError


@pytest.fixture
def json_handler():
    """
    Create a JSONHandler instance.
    """
    return JSONHandler()


@pytest.fixture
def temp_json_file(tmp_path):
    """
    Create a temporary JSON file.
    """
    file_path = tmp_path / "test.json"
    content = '{"key1": "value1", "key2": "value2"}'
    file_path.write_text(content, encoding="utf-8")
    return file_path


def test_load_valid_json(json_handler, temp_json_file):
    """
    Test loading a valid JSON file.
    """
    data = json_handler.load(temp_json_file)

    assert isinstance(data, dict)
    assert data["key1"] == "value1"
    assert data["key2"] == "value2"


def test_load_nonexistent_file(json_handler, tmp_path):
    """
    Test loading a non-existent file.
    """
    file_path = tmp_path / "nonexistent.json"

    with pytest.raises(LanguageFileError) as exc_info:
        json_handler.load(file_path)

    assert "File not found" in str(exc_info.value)


def test_load_empty_json(json_handler, tmp_path):
    """
    Test loading an empty JSON file.
    """
    file_path = tmp_path / "empty.json"
    file_path.write_text("{}", encoding="utf-8")

    data = json_handler.load(file_path)
    assert data == {}


def test_load_json_with_bom(json_handler, tmp_path):
    """
    Test loading JSON file with UTF-8 BOM.
    """
    file_path = tmp_path / "with_bom.json"
    content = '{"key": "value"}'
    file_path.write_bytes(b'\xef\xbb\xbf' + content.encode("utf-8"))

    data = json_handler.load(file_path)
    assert data["key"] == "value"


def test_load_json_with_unicode(json_handler, tmp_path):
    """
    Test loading JSON with unicode characters.
    """
    file_path = tmp_path / "unicode.json"
    content = '{"chinese": "中文", "japanese": "日本語"}'
    file_path.write_text(content, encoding="utf-8")

    data = json_handler.load(file_path)
    assert data["chinese"] == "中文"
    assert data["japanese"] == "日本語"


def test_load_invalid_json(json_handler, tmp_path):
    """
    Test loading invalid JSON.
    """
    file_path = tmp_path / "invalid.json"
    file_path.write_text("not valid json{", encoding="utf-8")

    with pytest.raises(JSONParseError):
        json_handler.load(file_path)


def test_load_non_dict_json(json_handler, tmp_path):
    """
    Test loading JSON that is not a dictionary.
    """
    file_path = tmp_path / "array.json"
    file_path.write_text('["item1", "item2"]', encoding="utf-8")

    with pytest.raises(JSONParseError) as exc_info:
        json_handler.load(file_path)

    assert "Expected dict" in str(exc_info.value)


def test_load_from_bytes_valid(json_handler):
    """
    Test loading JSON from valid bytes.
    """
    content = b'{"key": "value"}'
    data = json_handler.load_from_bytes(content)

    assert data["key"] == "value"


def test_load_from_bytes_with_bom(json_handler):
    """
    Test loading JSON from bytes with BOM.
    """
    content = b'\xef\xbb\xbf{"key": "value"}'
    data = json_handler.load_from_bytes(content)

    assert data["key"] == "value"


def test_load_from_bytes_unicode(json_handler):
    """
    Test loading JSON from bytes with unicode.
    """
    content = '{"key": "中文"}'.encode("utf-8")
    data = json_handler.load_from_bytes(content)

    assert data["key"] == "中文"


def test_load_from_bytes_empty(json_handler):
    """
    Test loading empty JSON from bytes.
    """
    content = b'{}'
    data = json_handler.load_from_bytes(content)

    assert data == {}


def test_load_from_bytes_invalid(json_handler):
    """
    Test loading invalid JSON from bytes.
    """
    content = b'invalid json{'

    with pytest.raises(JSONParseError):
        json_handler.load_from_bytes(content)


def test_load_from_bytes_non_dict(json_handler):
    """
    Test loading non-dict JSON from bytes.
    """
    content = b'["array"]'

    with pytest.raises(JSONParseError) as exc_info:
        json_handler.load_from_bytes(content)

    assert "Expected dict" in str(exc_info.value)


def test_dump_valid_data(json_handler, tmp_path):
    """
    Test dumping valid data to JSON file.
    """
    file_path = tmp_path / "output.json"
    data = {"key1": "value1", "key2": "value2"}

    json_handler.dump(data, file_path)

    assert file_path.exists()
    loaded_data = json_handler.load(file_path)
    assert loaded_data == data


def test_dump_creates_directory(json_handler, tmp_path):
    """
    Test that dump creates parent directories.
    """
    file_path = tmp_path / "subdir" / "nested" / "output.json"
    data = {"key": "value"}

    json_handler.dump(data, file_path)

    assert file_path.exists()
    assert file_path.parent.exists()


def test_dump_unicode_data(json_handler, tmp_path):
    """
    Test dumping unicode data.
    """
    file_path = tmp_path / "unicode.json"
    data = {"chinese": "中文", "emoji": "😀"}

    json_handler.dump(data, file_path)

    loaded_data = json_handler.load(file_path)
    assert loaded_data == data


def test_dump_empty_dict(json_handler, tmp_path):
    """
    Test dumping empty dictionary.
    """
    file_path = tmp_path / "empty.json"
    data = {}

    json_handler.dump(data, file_path)

    loaded_data = json_handler.load(file_path)
    assert loaded_data == {}


def test_dump_preserves_order(json_handler, tmp_path):
    """
    Test that dump preserves key order.
    """
    file_path = tmp_path / "ordered.json"
    data = {"z": "last", "a": "first", "m": "middle"}

    json_handler.dump(data, file_path)

    loaded_data = json_handler.load(file_path)
    assert list(loaded_data.keys()) == ["z", "a", "m"]


def test_load_null_json(json_handler, tmp_path):
    """
    Test loading JSON file with null content.
    """
    file_path = tmp_path / "null.json"
    file_path.write_text("null", encoding="utf-8")

    data = json_handler.load(file_path)
    assert data == {}


def test_load_from_bytes_null(json_handler):
    """
    Test loading null JSON from bytes.
    """
    content = b'null'
    data = json_handler.load_from_bytes(content)

    assert data == {}


def test_dump_write_failure(json_handler, tmp_path, monkeypatch):
    """
    Test that dump raises LanguageFileError on write failure.
    """
    from ruamel.yaml import YAML

    def mock_dump_failure(data, stream):
        raise IOError("Permission denied")

    file_path = tmp_path / "output.json"
    data = {"key": "value"}

    monkeypatch.setattr(YAML, "dump", mock_dump_failure)

    with pytest.raises(LanguageFileError) as exc_info:
        json_handler.dump(data, file_path)

    assert "Failed to write JSON file" in str(exc_info.value)


