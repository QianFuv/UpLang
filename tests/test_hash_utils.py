"""
Tests for hash utilities.
"""

from uplang.utils.hash_utils import calculate_dict_hash, calculate_hash


def test_calculate_dict_hash_empty():
    """
    Test hash calculation for empty dictionary.
    """
    hash1 = calculate_dict_hash({})
    hash2 = calculate_dict_hash({})

    assert hash1 == hash2
    assert isinstance(hash1, str)
    assert len(hash1) == 64


def test_calculate_dict_hash_deterministic():
    """
    Test that hash calculation is deterministic.
    """
    data = {"key1": "value1", "key2": "value2", "key3": "value3"}

    hash1 = calculate_dict_hash(data)
    hash2 = calculate_dict_hash(data)

    assert hash1 == hash2


def test_calculate_dict_hash_order_independent():
    """
    Test that hash is independent of key order.
    """
    data1 = {"key1": "value1", "key2": "value2"}
    data2 = {"key2": "value2", "key1": "value1"}

    hash1 = calculate_dict_hash(data1)
    hash2 = calculate_dict_hash(data2)

    assert hash1 == hash2


def test_calculate_dict_hash_different_values():
    """
    Test that different values produce different hashes.
    """
    data1 = {"key1": "value1"}
    data2 = {"key1": "value2"}

    hash1 = calculate_dict_hash(data1)
    hash2 = calculate_dict_hash(data2)

    assert hash1 != hash2


def test_calculate_dict_hash_unicode():
    """
    Test hash calculation with unicode characters.
    """
    data = {"key1": "中文", "key2": "日本語", "key3": "한국어"}

    hash1 = calculate_dict_hash(data)
    hash2 = calculate_dict_hash(data)

    assert hash1 == hash2
    assert isinstance(hash1, str)
    assert len(hash1) == 64


def test_calculate_hash_file(tmp_path):
    """
    Test calculating hash of a file.
    """
    file_path = tmp_path / "test_file.txt"
    file_path.write_text("Hello, World!", encoding="utf-8")

    hash1 = calculate_hash(file_path)
    hash2 = calculate_hash(file_path)

    assert hash1 == hash2
    assert isinstance(hash1, str)
    assert len(hash1) == 64


def test_calculate_hash_different_files(tmp_path):
    """
    Test that different files produce different hashes.
    """
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"

    file1.write_text("Content 1", encoding="utf-8")
    file2.write_text("Content 2", encoding="utf-8")

    hash1 = calculate_hash(file1)
    hash2 = calculate_hash(file2)

    assert hash1 != hash2


def test_calculate_hash_large_file(tmp_path):
    """
    Test calculating hash of a large file (tests chunking).
    """
    file_path = tmp_path / "large_file.txt"
    content = "x" * 10000
    file_path.write_text(content, encoding="utf-8")

    hash1 = calculate_hash(file_path)
    hash2 = calculate_hash(file_path)

    assert hash1 == hash2


def test_calculate_hash_binary_file(tmp_path):
    """
    Test calculating hash of a binary file.
    """
    file_path = tmp_path / "binary_file.bin"
    file_path.write_bytes(b"\x00\x01\x02\x03\xff\xfe\xfd")

    hash_value = calculate_hash(file_path)

    assert isinstance(hash_value, str)
    assert len(hash_value) == 64


def test_calculate_hash_empty_file(tmp_path):
    """
    Test calculating hash of an empty file.
    """
    file_path = tmp_path / "empty.txt"
    file_path.write_text("", encoding="utf-8")

    hash_value = calculate_hash(file_path)

    assert isinstance(hash_value, str)
    assert len(hash_value) == 64
