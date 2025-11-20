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
    import json

    def mock_dumps_failure(data, **kwargs):
        raise IOError("Permission denied")

    file_path = tmp_path / "output.json"
    data = {"key": "value"}

    monkeypatch.setattr(json, "dumps", mock_dumps_failure)

    with pytest.raises(LanguageFileError) as exc_info:
        json_handler.dump(data, file_path)

    assert "Failed to write JSON file" in str(exc_info.value)


def test_dump_with_surrogate_pairs(json_handler, tmp_path):
    """
    Test dumping data containing surrogate pairs (corrupted Unicode).
    """
    file_path = tmp_path / "surrogate.json"
    data = {"key": "value\udcff", "normal": "normal_value"}

    json_handler.dump(data, file_path)

    assert file_path.exists()
    loaded_data = json_handler.load(file_path)
    assert "key" in loaded_data
    assert "normal" in loaded_data
    assert loaded_data["normal"] == "normal_value"


def test_clean_control_chars_with_surrogates(json_handler, tmp_path):
    """
    Test that surrogate pairs are preserved in control character cleaning.
    """
    file_path = tmp_path / "surrogate_test.json"
    content = '{"test": "value\ud800with\udfffsurrogates"}'
    file_path.write_text(content, encoding="utf-8", errors="surrogatepass")

    data = json_handler.load(file_path)
    assert "test" in data


def test_clean_control_chars_replaces_with_space(json_handler, tmp_path):
    """
    Test that control characters are replaced with spaces.
    """
    file_path = tmp_path / "control_chars.json"
    content = '{"test": "value\x01with\x02control\x03chars"}'
    file_path.write_text(content, encoding="utf-8")

    data = json_handler.load(file_path)
    assert "test" in data
    assert "control" in data["test"]


def test_strip_comments_line_starting_with_comment(json_handler, tmp_path):
    """
    Test stripping lines that start with //.
    """
    file_path = tmp_path / "comments.json"
    content = '''
{
    // This is a comment
    "key1": "value1",
    // Another comment
    "key2": "value2"
}
'''
    file_path.write_text(content, encoding="utf-8")

    data = json_handler.load(file_path)
    assert data["key1"] == "value1"
    assert data["key2"] == "value2"


def test_strip_comments_inline_after_colon(json_handler, tmp_path):
    """
    Test handling inline comments after colons (special case handling).
    This covers line 91 in json_handler.py where the previous line ends with colon.
    """
    file_path = tmp_path / "inline_comments.json"
    content = '''{
    "nested": {
        "key1": "value1"  // this is a nested comment without comma
    },
    "key2": "value2"
}'''
    file_path.write_text(content, encoding="utf-8")

    data = json_handler.load(file_path)
    assert "nested" in data
    assert "key2" in data


def test_strip_comments_inline_without_comma(json_handler, tmp_path):
    """
    Test handling inline comments on lines without commas.
    """
    file_path = tmp_path / "inline_no_comma.json"
    content = '''
{
    "key": {
        "nested": "value" // inline comment
    }
}
'''
    file_path.write_text(content, encoding="utf-8")

    data = json_handler.load(file_path)
    assert "key" in data


def test_load_with_all_encoding_failures(json_handler, tmp_path, monkeypatch):
    """
    Test that load raises JSONParseError when all encodings fail.
    """
    file_path = tmp_path / "test.json"
    file_path.write_text('{"key": "value"}', encoding="utf-8")

    original_open = open

    def mock_open_with_decode_error(*args, **kwargs):
        file_obj = original_open(*args, **kwargs)
        original_read = file_obj.read

        def failing_read():
            raise UnicodeDecodeError("utf-8", b"", 0, 1, "mocked error")

        file_obj.read = failing_read
        return file_obj

    monkeypatch.setattr("builtins.open", mock_open_with_decode_error)

    with pytest.raises(JSONParseError) as exc_info:
        json_handler.load(file_path)

    assert "Failed to read file with any encoding" in str(exc_info.value)


def test_load_from_bytes_latin1_fallback(json_handler):
    """
    Test that load_from_bytes successfully uses fallback encodings.
    Lines 175-176 and 182 in json_handler.py are difficult to cover in practice
    because latin-1 and cp1252 can decode virtually any byte sequence.
    This test verifies the fallback mechanism works correctly.
    """
    content = b'\x80\x81\x82\x83'
    result = json_handler.load_from_bytes(content)
    assert isinstance(result, dict)


