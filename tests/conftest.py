"""Pytest configuration and shared fixtures for UpLang tests.

This module provides common test fixtures and configuration for the UpLang test suite.
Fixtures include temporary directories, sample data, and mock JAR files for testing
the language file extraction and synchronization functionality.
"""

import json
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, Any, Generator

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_path:
        yield Path(temp_path)


@pytest.fixture
def sample_lang_data() -> Dict[str, Any]:
    """Sample language data for testing."""
    return {
        "item.test_mod.test_item": "Test Item",
        "block.test_mod.test_block": "Test Block",
        "itemGroup.test_mod": "Test Mod Items"
    }


@pytest.fixture
def sample_jar_file(temp_dir: Path, sample_lang_data: Dict[str, Any]) -> Path:
    """Create a sample JAR file with language data."""
    jar_path = temp_dir / "test_mod.jar"

    with zipfile.ZipFile(jar_path, 'w') as jar:
        # Add en_us.json
        en_content = json.dumps(sample_lang_data, indent=2)
        jar.writestr("assets/test_mod/lang/en_us.json", en_content)

        # Add zh_cn.json with some translations
        zh_data = sample_lang_data.copy()
        zh_data["item.test_mod.test_item"] = "测试物品"
        zh_content = json.dumps(zh_data, indent=2, ensure_ascii=False)
        jar.writestr("assets/test_mod/lang/zh_cn.json", zh_content)

        # Add mod metadata
        metadata = {
            "modid": "test_mod",
            "name": "Test Mod",
            "version": "1.0.0"
        }
        jar.writestr("mcmod.info", json.dumps([metadata], indent=2))

    return jar_path


@pytest.fixture
def mods_directory(temp_dir: Path, sample_jar_file: Path) -> Path:
    """Create a mods directory with sample JAR files."""
    mods_dir = temp_dir / "mods"
    mods_dir.mkdir()

    # Copy sample jar to mods directory
    import shutil
    shutil.copy2(sample_jar_file, mods_dir / "test_mod.jar")

    return mods_dir


@pytest.fixture
def resource_pack_directory(temp_dir: Path) -> Path:
    """Create an empty resource pack directory."""
    rp_dir = temp_dir / "resource_pack"
    rp_dir.mkdir()
    return rp_dir


@pytest.fixture
def mock_project_state() -> Dict[str, Any]:
    """Mock project state data for testing."""
    return {
        "mods_directory": "/test/mods",
        "resource_pack_directory": "/test/resource_pack",
        "mods": {
            "test_mod.jar": {
                "mod_id": "test_mod",
                "file_size": 1024,
                "last_modified": 1234567890.0,
                "hash": "abcd1234"
            }
        },
        "last_scan": 1234567890.0
    }