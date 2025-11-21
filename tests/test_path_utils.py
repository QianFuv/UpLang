"""
Tests for path utilities.
"""

from pathlib import Path

from uplang.utils.path_utils import extract_mod_id, sanitize_filename


def test_sanitize_filename_valid():
    """
    Test sanitizing a valid filename.
    """
    result = sanitize_filename("valid_filename")
    assert result == "valid_filename"


def test_sanitize_filename_invalid_chars():
    """
    Test sanitizing filename with invalid characters.
    """
    result = sanitize_filename("file<>name:with/invalid|chars?")
    assert "<" not in result
    assert ">" not in result
    assert ":" not in result
    assert "/" not in result
    assert "|" not in result
    assert "?" not in result


def test_sanitize_filename_spaces():
    """
    Test sanitizing filename with spaces.
    """
    result = sanitize_filename("file name with spaces")
    assert result == "file_name_with_spaces"


def test_sanitize_filename_empty():
    """
    Test sanitizing empty filename.
    """
    result = sanitize_filename("")
    assert result == "unnamed"


def test_extract_mod_id_simple():
    """
    Test extracting mod ID from simple JAR filename.
    """
    jar_path = Path("examplemod-1.0.0.jar")
    result = extract_mod_id(jar_path)
    assert result == "examplemod"


def test_extract_mod_id_complex_version():
    """
    Test extracting mod ID from JAR with complex version.
    """
    jar_path = Path("mymod-1.20.1-forge-1.0.0.jar")
    result = extract_mod_id(jar_path)
    assert result == "mymod"


def test_extract_mod_id_no_version():
    """
    Test extracting mod ID from JAR without version.
    """
    jar_path = Path("simplemod.jar")
    result = extract_mod_id(jar_path)
    assert result == "simplemod"


def test_extract_mod_id_special_chars():
    """
    Test extracting mod ID from JAR with special characters.
    """
    jar_path = Path("My-Cool-Mod-1.0.jar")
    result = extract_mod_id(jar_path)
    assert result == "my_cool_mod"
