"""
Tests for cache manager.
"""

import json

import pytest

from uplang.core.cache import CacheManager
from uplang.exceptions import CacheError


@pytest.fixture
def cache_path(tmp_path):
    """
    Create a temporary cache file path.
    """
    return tmp_path / ".uplang_cache.json"


@pytest.fixture
def cache_manager(cache_path):
    """
    Create a CacheManager instance.
    """
    return CacheManager(cache_path)


def test_cache_manager_creates_empty_cache(cache_manager, cache_path):
    """
    Test that CacheManager creates an empty cache if file doesn't exist.
    """
    assert cache_manager.cache_data["version"] == CacheManager.CACHE_VERSION
    assert "last_updated" in cache_manager.cache_data
    assert cache_manager.cache_data["mods"] == {}


def test_cache_manager_load_existing_cache(cache_path):
    """
    Test loading an existing cache file.
    """
    cache_data = {
        "version": CacheManager.CACHE_VERSION,
        "last_updated": "2025-01-01T00:00:00",
        "mods": {
            "testmod": {
                "jar_name": "testmod-1.0.0.jar",
                "en_us_hash": "hash123",
                "zh_cn_hash": "hash456",
                "last_sync": "2025-01-01T00:00:00",
            }
        },
    }

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache_data, f)

    cache_manager = CacheManager(cache_path)

    assert (
        cache_manager.cache_data["mods"]["testmod"]["jar_name"] == "testmod-1.0.0.jar"
    )
    assert cache_manager.cache_data["mods"]["testmod"]["en_us_hash"] == "hash123"


def test_cache_manager_load_invalid_version(cache_path):
    """
    Test that cache with wrong version is recreated.
    """
    cache_data = {
        "version": "0.0.0",
        "last_updated": "2025-01-01T00:00:00",
        "mods": {"testmod": {}},
    }

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache_data, f)

    cache_manager = CacheManager(cache_path)

    assert cache_manager.cache_data["version"] == CacheManager.CACHE_VERSION
    assert cache_manager.cache_data["mods"] == {}


def test_cache_manager_load_corrupted_cache(cache_path):
    """
    Test that corrupted cache file is recreated.
    """
    cache_path.write_text("invalid json{", encoding="utf-8")

    cache_manager = CacheManager(cache_path)

    assert cache_manager.cache_data["version"] == CacheManager.CACHE_VERSION
    assert cache_manager.cache_data["mods"] == {}


def test_save_cache(cache_manager, cache_path):
    """
    Test saving cache to file.
    """
    cache_manager.cache_data["mods"]["testmod"] = {
        "jar_name": "testmod-1.0.0.jar",
        "en_us_hash": "hash123",
        "zh_cn_hash": "hash456",
    }

    cache_manager.save()

    assert cache_path.exists()

    with open(cache_path, encoding="utf-8") as f:
        loaded_data = json.load(f)

    assert loaded_data["mods"]["testmod"]["jar_name"] == "testmod-1.0.0.jar"


def test_save_cache_updates_timestamp(cache_manager, cache_path):
    """
    Test that save updates the last_updated timestamp.
    """
    old_timestamp = cache_manager.cache_data["last_updated"]

    cache_manager.save()

    new_timestamp = cache_manager.cache_data["last_updated"]
    assert new_timestamp != old_timestamp


def test_save_cache_creates_directory(tmp_path):
    """
    Test that save creates parent directories.
    """
    cache_path = tmp_path / "subdir" / "nested" / "cache.json"
    cache_manager = CacheManager(cache_path)

    cache_manager.save()

    assert cache_path.exists()
    assert cache_path.parent.exists()


def test_is_changed_new_mod(cache_manager):
    """
    Test is_changed returns True for new mods.
    """
    assert cache_manager.is_changed("newmod", "hash1", "hash2")


def test_is_changed_no_change(cache_manager):
    """
    Test is_changed returns False when hashes match.
    """
    cache_manager.cache_data["mods"]["testmod"] = {
        "en_us_hash": "hash123",
        "zh_cn_hash": "hash456",
    }

    assert not cache_manager.is_changed("testmod", "hash123", "hash456")


def test_is_changed_en_us_changed(cache_manager):
    """
    Test is_changed detects English hash change.
    """
    cache_manager.cache_data["mods"]["testmod"] = {
        "en_us_hash": "old_hash",
        "zh_cn_hash": "hash456",
    }

    assert cache_manager.is_changed("testmod", "new_hash", "hash456")


def test_is_changed_zh_cn_changed(cache_manager):
    """
    Test is_changed detects Chinese hash change.
    """
    cache_manager.cache_data["mods"]["testmod"] = {
        "en_us_hash": "hash123",
        "zh_cn_hash": "old_hash",
    }

    assert cache_manager.is_changed("testmod", "hash123", "new_hash")


def test_is_changed_with_none_hashes(cache_manager):
    """
    Test is_changed with None hashes.
    """
    cache_manager.cache_data["mods"]["testmod"] = {
        "en_us_hash": "hash123",
        "zh_cn_hash": "hash456",
    }

    assert not cache_manager.is_changed("testmod", None, None)


def test_is_changed_partial_match(cache_manager):
    """
    Test is_changed with partial hash match.
    """
    cache_manager.cache_data["mods"]["testmod"] = {
        "en_us_hash": "hash123",
        "zh_cn_hash": None,
    }

    assert not cache_manager.is_changed("testmod", "hash123", None)


def test_update_mod(cache_manager):
    """
    Test updating a mod entry in cache.
    """
    cache_manager.update_mod("testmod", "testmod-1.0.0.jar", "hash123", "hash456")

    assert "testmod" in cache_manager.cache_data["mods"]
    assert (
        cache_manager.cache_data["mods"]["testmod"]["jar_name"] == "testmod-1.0.0.jar"
    )
    assert cache_manager.cache_data["mods"]["testmod"]["en_us_hash"] == "hash123"
    assert cache_manager.cache_data["mods"]["testmod"]["zh_cn_hash"] == "hash456"
    assert "last_sync" in cache_manager.cache_data["mods"]["testmod"]


def test_update_mod_overwrites_existing(cache_manager):
    """
    Test that update_mod overwrites existing entries.
    """
    cache_manager.cache_data["mods"]["testmod"] = {
        "jar_name": "old.jar",
        "en_us_hash": "old_hash",
    }

    cache_manager.update_mod("testmod", "new.jar", "new_hash", "zh_hash")

    assert cache_manager.cache_data["mods"]["testmod"]["jar_name"] == "new.jar"
    assert cache_manager.cache_data["mods"]["testmod"]["en_us_hash"] == "new_hash"


def test_update_mod_with_none_hashes(cache_manager):
    """
    Test updating mod with None hashes.
    """
    cache_manager.update_mod("testmod", "testmod.jar", None, None)

    assert cache_manager.cache_data["mods"]["testmod"]["en_us_hash"] is None
    assert cache_manager.cache_data["mods"]["testmod"]["zh_cn_hash"] is None


def test_remove_mod(cache_manager):
    """
    Test removing a mod from cache.
    """
    cache_manager.cache_data["mods"]["testmod"] = {"jar_name": "testmod.jar"}

    cache_manager.remove_mod("testmod")

    assert "testmod" not in cache_manager.cache_data["mods"]


def test_remove_mod_nonexistent(cache_manager):
    """
    Test removing a non-existent mod (should not raise error).
    """
    cache_manager.remove_mod("nonexistent")

    assert True


def test_get_cached_mod_ids(cache_manager):
    """
    Test getting all cached mod IDs.
    """
    cache_manager.cache_data["mods"] = {
        "mod1": {},
        "mod2": {},
        "mod3": {},
    }

    mod_ids = cache_manager.get_cached_mod_ids()

    assert mod_ids == {"mod1", "mod2", "mod3"}


def test_get_cached_mod_ids_empty(cache_manager):
    """
    Test getting cached mod IDs when cache is empty.
    """
    mod_ids = cache_manager.get_cached_mod_ids()

    assert mod_ids == set()


def test_clear_cache(cache_manager):
    """
    Test clearing all cache data.
    """
    cache_manager.cache_data["mods"] = {"mod1": {}, "mod2": {}}

    cache_manager.clear()

    assert cache_manager.cache_data["mods"] == {}
    assert cache_manager.cache_data["version"] == CacheManager.CACHE_VERSION


def test_clear_cache_preserves_version(cache_manager):
    """
    Test that clear preserves cache version.
    """
    cache_manager.cache_data["mods"] = {"mod1": {}}

    cache_manager.clear()

    assert cache_manager.cache_data["version"] == CacheManager.CACHE_VERSION
    assert "last_updated" in cache_manager.cache_data


def test_create_empty_cache_structure(cache_manager):
    """
    Test _create_empty_cache structure.
    """
    empty_cache = cache_manager._create_empty_cache()

    assert "version" in empty_cache
    assert "last_updated" in empty_cache
    assert "mods" in empty_cache
    assert empty_cache["mods"] == {}


def test_save_cache_failure(tmp_path, monkeypatch):
    """
    Test that save raises CacheError on write failure.
    """
    import json as json_module

    cache_path = tmp_path / "cache.json"
    cache_manager = CacheManager(cache_path)

    def mock_dump_failure(data, file, **kwargs):
        raise OSError("Permission denied")

    monkeypatch.setattr(json_module, "dump", mock_dump_failure)

    with pytest.raises(CacheError) as exc_info:
        cache_manager.save()

    assert "Failed to save cache" in str(exc_info.value)
