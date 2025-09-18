"""Tests for utils module."""

from pathlib import Path

import pytest

from uplang.utils import sanitize_filename, create_safe_mod_id


class TestSanitizeFilename:
    """Test cases for sanitize_filename function."""

    def test_sanitize_valid_filename(self):
        """Test sanitizing a valid filename."""
        result = sanitize_filename("valid_filename.jar")
        assert result == "valid_filename.jar"

    def test_sanitize_filename_with_invalid_chars(self):
        """Test sanitizing filename with invalid characters."""
        result = sanitize_filename("file<>name|with?invalid*chars")
        assert result == "file_name_with_invalid_chars"

    def test_sanitize_filename_with_multiple_underscores(self):
        """Test that multiple consecutive underscores are collapsed."""
        result = sanitize_filename("file___with___many___underscores")
        assert result == "file_with_many_underscores"

    def test_sanitize_filename_with_leading_trailing_dots(self):
        """Test removing leading and trailing dots and spaces."""
        result = sanitize_filename("  ..filename..  ")
        assert result == "filename"

    def test_sanitize_empty_filename(self):
        """Test sanitizing empty filename returns 'unknown'."""
        result = sanitize_filename("")
        assert result == "unknown"

    def test_sanitize_filename_with_only_invalid_chars(self):
        """Test sanitizing filename with only invalid characters."""
        result = sanitize_filename("<>|?*")
        # Invalid chars become underscores, then collapsed to single underscore
        assert result == "_"

    def test_sanitize_very_long_filename(self):
        """Test truncating very long filenames."""
        long_name = "a" * 250
        result = sanitize_filename(long_name)
        assert len(result) <= 200

    def test_sanitize_filename_preserves_unicode(self):
        """Test that Unicode characters are preserved."""
        result = sanitize_filename("文件名测试.jar")
        assert result == "文件名测试.jar"


class TestCreateSafeModId:
    """Test cases for create_safe_mod_id function."""

    def test_create_safe_mod_id_basic(self):
        """Test creating safe mod ID from basic JAR name."""
        result = create_safe_mod_id("test_mod.jar")
        assert result == "unrecognized_test_mod"

    def test_create_safe_mod_id_with_version(self):
        """Test creating safe mod ID from JAR with version."""
        result = create_safe_mod_id("awesome_mod-1.0.2.jar")
        assert result == "unrecognized_awesome_mod-1.0.2"

    def test_create_safe_mod_id_with_invalid_chars(self):
        """Test creating safe mod ID from JAR with invalid characters."""
        result = create_safe_mod_id("mod<name>with|invalid?chars.jar")
        assert result == "unrecognized_mod_name_with_invalid_chars"

    def test_create_safe_mod_id_without_extension(self):
        """Test creating safe mod ID from filename without .jar extension."""
        result = create_safe_mod_id("test_mod")
        assert result == "unrecognized_test_mod"

    def test_create_safe_mod_id_complex_name(self):
        """Test creating safe mod ID from complex JAR name."""
        result = create_safe_mod_id("My-Awesome-Mod_v2.1.3-forge.jar")
        assert result == "unrecognized_My-Awesome-Mod_v2.1.3-forge"

    def test_create_safe_mod_id_empty_name(self):
        """Test creating safe mod ID from empty name."""
        result = create_safe_mod_id("")
        assert result == "unrecognized_unknown"

    def test_create_safe_mod_id_only_extension(self):
        """Test creating safe mod ID from only .jar extension."""
        result = create_safe_mod_id(".jar")
        assert result == "unrecognized_jar"


class TestUtilityFunctionsIntegration:
    """Integration tests for utility functions."""

    def test_sanitize_and_create_mod_id_workflow(self):
        """Test the workflow of sanitizing and creating mod IDs."""
        problematic_jar = "Mod<>Name|With?Issues*-v1.0.jar"

        # This simulates the internal workflow
        sanitized = sanitize_filename(problematic_jar)
        mod_id = create_safe_mod_id(sanitized)

        assert "unrecognized_" in mod_id
        assert "<" not in mod_id
        assert ">" not in mod_id
        assert "|" not in mod_id
        assert "?" not in mod_id
        assert "*" not in mod_id

    def test_path_handling_with_sanitized_names(self, temp_dir: Path):
        """Test that sanitized names work with Path operations."""
        original_name = "problematic<>name.jar"
        sanitized = sanitize_filename(original_name)

        # Should be able to create a valid path
        test_path = temp_dir / sanitized
        test_path.write_text("test content")

        assert test_path.exists()
        assert test_path.read_text() == "test content"