"""
Tests for custom exceptions.
"""

import pytest

from uplang.exceptions import (
    CacheError,
    JSONParseError,
    LanguageFileError,
    ModMetadataError,
    ModNotFoundError,
    SyncError,
    UpLangError,
    ValidationError,
)


def test_uplang_error_basic():
    """
    Test basic UpLangError creation.
    """
    error = UpLangError("Test error message")
    assert str(error) == "Test error message"
    assert error.message == "Test error message"
    assert error.context == {}


def test_uplang_error_with_context():
    """
    Test UpLangError with context.
    """
    error = UpLangError("Test error", context={"key": "value", "number": 42})
    error_str = str(error)
    assert "Test error" in error_str
    assert "key=value" in error_str
    assert "number=42" in error_str


def test_uplang_error_empty_context():
    """
    Test UpLangError with empty context dict.
    """
    error = UpLangError("Test error", context={})
    assert str(error) == "Test error"
    assert error.context == {}


def test_mod_not_found_error():
    """
    Test ModNotFoundError exception.
    """
    error = ModNotFoundError("Mod not found", context={"path": "/path/to/mod"})
    assert isinstance(error, UpLangError)
    assert "Mod not found" in str(error)
    assert "path=/path/to/mod" in str(error)


def test_mod_metadata_error():
    """
    Test ModMetadataError exception.
    """
    error = ModMetadataError("Invalid metadata", context={"mod_id": "testmod"})
    assert isinstance(error, UpLangError)
    assert "Invalid metadata" in str(error)


def test_language_file_error():
    """
    Test LanguageFileError exception.
    """
    error = LanguageFileError("File error", context={"file": "lang.json"})
    assert isinstance(error, UpLangError)
    assert "File error" in str(error)


def test_json_parse_error():
    """
    Test JSONParseError exception.
    """
    error = JSONParseError("Parse failed", context={"line": 10})
    assert isinstance(error, LanguageFileError)
    assert isinstance(error, UpLangError)
    assert "Parse failed" in str(error)


def test_sync_error():
    """
    Test SyncError exception.
    """
    error = SyncError("Sync failed", context={"mod_id": "testmod"})
    assert isinstance(error, UpLangError)
    assert "Sync failed" in str(error)


def test_cache_error():
    """
    Test CacheError exception.
    """
    error = CacheError("Cache error", context={"path": "/cache/path"})
    assert isinstance(error, UpLangError)
    assert "Cache error" in str(error)


def test_validation_error():
    """
    Test ValidationError exception.
    """
    error = ValidationError("Validation failed", context={"field": "email"})
    assert isinstance(error, UpLangError)
    assert "Validation failed" in str(error)


def test_error_inheritance():
    """
    Test that all custom errors inherit from UpLangError.
    """
    errors = [
        ModNotFoundError("test"),
        ModMetadataError("test"),
        LanguageFileError("test"),
        JSONParseError("test"),
        SyncError("test"),
        CacheError("test"),
        ValidationError("test"),
    ]

    for error in errors:
        assert isinstance(error, UpLangError)
        assert isinstance(error, Exception)


def test_error_can_be_raised():
    """
    Test that errors can be raised and caught.
    """
    with pytest.raises(UpLangError):
        raise UpLangError("Test error")

    with pytest.raises(ModNotFoundError):
        raise ModNotFoundError("Mod not found")


def test_error_context_multiple_items():
    """
    Test error with multiple context items.
    """
    error = UpLangError(
        "Complex error",
        context={"item1": "value1", "item2": "value2", "item3": "value3"},
    )

    error_str = str(error)
    assert "Complex error" in error_str
    assert "item1=value1" in error_str
    assert "item2=value2" in error_str
    assert "item3=value3" in error_str


def test_error_message_attribute():
    """
    Test that error message is accessible via attribute.
    """
    error = UpLangError("Test message", context={"key": "value"})
    assert error.message == "Test message"


def test_error_context_attribute():
    """
    Test that error context is accessible via attribute.
    """
    context = {"key1": "value1", "key2": "value2"}
    error = UpLangError("Test message", context=context)
    assert error.context == context


def test_json_parse_error_is_language_file_error():
    """
    Test that JSONParseError is a subclass of LanguageFileError.
    """
    error = JSONParseError("Parse error")
    assert isinstance(error, JSONParseError)
    assert isinstance(error, LanguageFileError)
    assert isinstance(error, UpLangError)


def test_error_with_none_context():
    """
    Test error creation with None context.
    """
    error = UpLangError("Test error", context=None)
    assert error.context == {}
    assert str(error) == "Test error"


def test_error_str_representation():
    """
    Test string representation of errors.
    """
    error1 = UpLangError("Simple error")
    assert str(error1) == "Simple error"

    error2 = UpLangError("Error with context", context={"key": "value"})
    assert "Error with context" in str(error2)
    assert "key=value" in str(error2)
