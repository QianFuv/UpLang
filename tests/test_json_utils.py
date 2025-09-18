"""Tests for json_utils module."""

import json
import tempfile
from pathlib import Path
from collections import OrderedDict
from typing import Any

import pytest

from uplang.json_utils import read_json_robust, write_json_safe


class TestReadJsonRobust:
    """Test cases for read_json_robust function."""

    def test_read_valid_json(self, temp_dir: Path):
        """Test reading a valid JSON file."""
        test_file = temp_dir / "valid.json"
        test_data = {"key": "value", "number": 42}
        test_file.write_text(json.dumps(test_data))

        result = read_json_robust(test_file)
        assert isinstance(result, OrderedDict)
        assert dict(result) == test_data

    def test_read_json_with_utf8_bom(self, temp_dir: Path):
        """Test reading JSON with UTF-8 BOM."""
        test_file = temp_dir / "bom.json"
        test_data = {"key": "value"}
        content = '\ufeff' + json.dumps(test_data)
        test_file.write_text(content, encoding='utf-8')

        result = read_json_robust(test_file)
        assert isinstance(result, OrderedDict)
        assert dict(result) == test_data

    def test_read_json_with_trailing_comma(self, temp_dir: Path):
        """Test reading JSON with trailing comma (malformed)."""
        test_file = temp_dir / "trailing_comma.json"
        content = '{"key": "value",}'
        test_file.write_text(content)

        result = read_json_robust(test_file)
        assert isinstance(result, OrderedDict)
        assert dict(result) == {"key": "value"}

    def test_read_nonexistent_file(self, temp_dir: Path):
        """Test reading a nonexistent file returns empty OrderedDict."""
        nonexistent = temp_dir / "does_not_exist.json"
        result = read_json_robust(nonexistent)
        assert isinstance(result, OrderedDict)
        assert len(result) == 0

    def test_read_empty_file(self, temp_dir: Path):
        """Test reading an empty file returns empty OrderedDict."""
        empty_file = temp_dir / "empty.json"
        empty_file.write_text("")

        result = read_json_robust(empty_file)
        assert isinstance(result, OrderedDict)
        assert len(result) == 0


class TestWriteJsonSafe:
    """Test cases for write_json_safe function."""

    def test_write_valid_data(self, temp_dir: Path):
        """Test writing valid data to JSON file."""
        test_file = temp_dir / "output.json"
        test_data = {"key": "value", "number": 42}

        write_json_safe(test_file, test_data)

        assert test_file.exists()
        written_data = json.loads(test_file.read_text())
        assert written_data == test_data

    def test_write_ordered_data(self, temp_dir: Path):
        """Test writing ordered data preserves order."""
        test_file = temp_dir / "ordered.json"
        test_data: OrderedDict[str, str] = OrderedDict([
            ("first", "value1"),
            ("second", "value2"),
            ("third", "value3")
        ])

        write_json_safe(test_file, test_data)

        content = test_file.read_text()
        lines = [line.strip() for line in content.split('\n') if line.strip() and not line.strip() in ['{', '}']]

        # Check that the order is preserved
        assert '"first"' in lines[0]
        assert '"second"' in lines[1]
        assert '"third"' in lines[2]

    def test_write_unicode_data(self, temp_dir: Path):
        """Test writing Unicode data."""
        test_file = temp_dir / "unicode.json"
        test_data = {"chinese": "测试", "japanese": "テスト"}

        write_json_safe(test_file, test_data)

        written_data = json.loads(test_file.read_text(encoding='utf-8'))
        assert written_data == test_data

    def test_write_creates_directory(self, temp_dir: Path):
        """Test writing creates parent directories."""
        nested_file = temp_dir / "nested" / "dir" / "file.json"
        test_data = {"nested": True}

        write_json_safe(nested_file, test_data)

        assert nested_file.exists()
        written_data = json.loads(nested_file.read_text())
        assert written_data == test_data


class TestOrderedJsonHandling:
    """Test cases for ordered JSON handling."""

    def test_read_preserves_order(self, temp_dir: Path):
        """Test that reading JSON preserves key order."""
        test_file = temp_dir / "ordered.json"

        # Write JSON with specific order
        ordered_data: OrderedDict[str, str] = OrderedDict([
            ("z_last", "last"),
            ("a_first", "first"),
            ("m_middle", "middle")
        ])
        test_file.write_text(json.dumps(ordered_data, indent=2))

        result = read_json_robust(test_file)

        # Verify it's an OrderedDict (function should return OrderedDict)
        assert isinstance(result, OrderedDict)

        # Verify order is preserved
        keys = list(result.keys())
        assert keys == ["z_last", "a_first", "m_middle"]

    def test_write_preserves_order(self, temp_dir: Path):
        """Test that writing ordered data preserves order."""
        test_file = temp_dir / "ordered_output.json"
        ordered_data: OrderedDict[str, str] = OrderedDict([
            ("first", "value1"),
            ("second", "value2"),
            ("third", "value3")
        ])

        write_json_safe(test_file, ordered_data)

        # Read back and verify order
        content = test_file.read_text()
        lines = [line.strip() for line in content.split('\n') if line.strip() and not line.strip() in ['{', '}']]

        # Check that the order is preserved in the file
        assert '"first"' in lines[0]
        assert '"second"' in lines[1]
        assert '"third"' in lines[2]