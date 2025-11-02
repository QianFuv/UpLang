"""
Tests for JAR file scanner.
"""

import pytest
from pathlib import Path
from zipfile import ZipFile
import json
import tomllib

from uplang.core.scanner import ModScanner
from uplang.models import ModType
from uplang.exceptions import ModNotFoundError, ModMetadataError


@pytest.fixture
def scanner():
    """
    Create a ModScanner instance.
    """
    return ModScanner()


@pytest.fixture
def forge_jar(tmp_path):
    """
    Create a mock Forge JAR file.
    """
    jar_path = tmp_path / "testmod-forge-1.0.0.jar"

    mods_toml = """
[[mods]]
modId = "testmod"
displayName = "Test Mod"
version = "1.0.0"
"""

    with ZipFile(jar_path, "w") as jar:
        jar.writestr("META-INF/mods.toml", mods_toml)

    return jar_path


@pytest.fixture
def fabric_jar(tmp_path):
    """
    Create a mock Fabric JAR file.
    """
    jar_path = tmp_path / "testmod-fabric-1.0.0.jar"

    fabric_json = {
        "id": "testmod",
        "name": "Test Mod",
        "version": "1.0.0"
    }

    with ZipFile(jar_path, "w") as jar:
        jar.writestr("fabric.mod.json", json.dumps(fabric_json))

    return jar_path


@pytest.fixture
def neoforge_jar(tmp_path):
    """
    Create a mock NeoForge JAR file.
    """
    jar_path = tmp_path / "testmod-neoforge-1.0.0.jar"

    mods_toml = """
[[mods]]
modId = "testmod"
displayName = "Test Mod"
version = "1.0.0"
"""

    with ZipFile(jar_path, "w") as jar:
        jar.writestr("META-INF/neoforge.mods.toml", mods_toml)

    return jar_path


@pytest.fixture
def unknown_jar(tmp_path):
    """
    Create a JAR file with no metadata.
    """
    jar_path = tmp_path / "unknown-mod-1.0.0.jar"

    with ZipFile(jar_path, "w") as jar:
        jar.writestr("dummy.txt", "content")

    return jar_path


def test_scan_directory_with_jars(scanner, tmp_path, forge_jar, fabric_jar):
    """
    Test scanning a directory with JAR files.
    """
    mods = scanner.scan_directory(tmp_path)

    assert len(mods) == 2
    assert all(mod.mod_id == "testmod" for mod in mods)


def test_scan_directory_empty(scanner, tmp_path):
    """
    Test scanning an empty directory.
    """
    mods = scanner.scan_directory(tmp_path)

    assert len(mods) == 0


def test_scan_directory_nonexistent(scanner, tmp_path):
    """
    Test scanning a non-existent directory.
    """
    nonexistent_dir = tmp_path / "nonexistent"

    with pytest.raises(ModNotFoundError) as exc_info:
        scanner.scan_directory(nonexistent_dir)

    assert "not found" in str(exc_info.value)


def test_scan_jar_forge(scanner, forge_jar):
    """
    Test scanning a Forge JAR file.
    """
    mod = scanner.scan_jar(forge_jar)

    assert mod.mod_id == "testmod"
    assert mod.name == "Test Mod"
    assert mod.version == "1.0.0"
    assert mod.mod_type == ModType.FORGE
    assert mod.jar_path == forge_jar


def test_scan_jar_fabric(scanner, fabric_jar):
    """
    Test scanning a Fabric JAR file.
    """
    mod = scanner.scan_jar(fabric_jar)

    assert mod.mod_id == "testmod"
    assert mod.name == "Test Mod"
    assert mod.version == "1.0.0"
    assert mod.mod_type == ModType.FABRIC


def test_scan_jar_neoforge(scanner, neoforge_jar):
    """
    Test scanning a NeoForge JAR file.
    """
    mod = scanner.scan_jar(neoforge_jar)

    assert mod.mod_id == "testmod"
    assert mod.name == "Test Mod"
    assert mod.version == "1.0.0"
    assert mod.mod_type == ModType.NEOFORGE


def test_scan_jar_unknown(scanner, unknown_jar):
    """
    Test scanning a JAR with no recognized metadata.
    """
    mod = scanner.scan_jar(unknown_jar)

    assert mod.mod_id == "unknown_mod"
    assert mod.name == "unknown-mod-1.0.0"
    assert mod.version == "unknown"
    assert mod.mod_type == ModType.UNKNOWN


def test_scan_jar_nonexistent(scanner, tmp_path):
    """
    Test scanning a non-existent JAR file.
    """
    nonexistent_jar = tmp_path / "nonexistent.jar"

    with pytest.raises(ModNotFoundError):
        scanner.scan_jar(nonexistent_jar)


def test_scan_jar_forge_minimal(scanner, tmp_path):
    """
    Test scanning a Forge JAR with minimal metadata.
    """
    jar_path = tmp_path / "minimal.jar"
    mods_toml = """
[[mods]]
modId = "minimalmod"
"""

    with ZipFile(jar_path, "w") as jar:
        jar.writestr("META-INF/mods.toml", mods_toml)

    mod = scanner.scan_jar(jar_path)

    assert mod.mod_id == "minimalmod"
    assert mod.mod_type == ModType.FORGE


def test_scan_jar_fabric_minimal(scanner, tmp_path):
    """
    Test scanning a Fabric JAR with minimal metadata.
    """
    jar_path = tmp_path / "minimal.jar"
    fabric_json = {"id": "minimalmod"}

    with ZipFile(jar_path, "w") as jar:
        jar.writestr("fabric.mod.json", json.dumps(fabric_json))

    mod = scanner.scan_jar(jar_path)

    assert mod.mod_id == "minimalmod"
    assert mod.mod_type == ModType.FABRIC


def test_scan_jar_forge_invalid_toml(scanner, tmp_path):
    """
    Test scanning a Forge JAR with invalid TOML.
    """
    jar_path = tmp_path / "invalid.jar"

    with ZipFile(jar_path, "w") as jar:
        jar.writestr("META-INF/mods.toml", "invalid toml [[")

    mod = scanner.scan_jar(jar_path)

    assert mod.mod_type == ModType.UNKNOWN


def test_scan_jar_fabric_invalid_json(scanner, tmp_path):
    """
    Test scanning a Fabric JAR with invalid JSON.
    """
    jar_path = tmp_path / "invalid.jar"

    with ZipFile(jar_path, "w") as jar:
        jar.writestr("fabric.mod.json", "invalid json {")

    mod = scanner.scan_jar(jar_path)

    assert mod.mod_type == ModType.UNKNOWN


def test_scan_jar_forge_empty_mods_list(scanner, tmp_path):
    """
    Test scanning a Forge JAR with empty mods list.
    """
    jar_path = tmp_path / "empty.jar"
    mods_toml = "mods = []"

    with ZipFile(jar_path, "w") as jar:
        jar.writestr("META-INF/mods.toml", mods_toml)

    mod = scanner.scan_jar(jar_path)

    assert mod.mod_type == ModType.UNKNOWN


def test_scan_directory_with_invalid_jars(scanner, tmp_path):
    """
    Test scanning directory with some invalid JAR files.
    """
    valid_jar = tmp_path / "valid.jar"
    invalid_jar = tmp_path / "invalid.jar"

    mods_toml = """
[[mods]]
modId = "validmod"
"""
    with ZipFile(valid_jar, "w") as jar:
        jar.writestr("META-INF/mods.toml", mods_toml)

    with ZipFile(invalid_jar, "w") as jar:
        jar.writestr("dummy.txt", "content")

    mods = scanner.scan_directory(tmp_path)

    assert len(mods) == 2


def test_scan_jar_forge_multiple_mods(scanner, tmp_path):
    """
    Test scanning a Forge JAR with multiple mods (uses first one).
    """
    jar_path = tmp_path / "multi.jar"
    mods_toml = """
[[mods]]
modId = "firstmod"
displayName = "First Mod"

[[mods]]
modId = "secondmod"
displayName = "Second Mod"
"""

    with ZipFile(jar_path, "w") as jar:
        jar.writestr("META-INF/mods.toml", mods_toml)

    mod = scanner.scan_jar(jar_path)

    assert mod.mod_id == "firstmod"
    assert mod.name == "First Mod"


def test_scan_directory_handles_scan_jar_exception(scanner, tmp_path):
    """
    Test that scan_directory handles exceptions from scan_jar gracefully.
    """
    valid_jar = tmp_path / "valid.jar"
    corrupt_jar = tmp_path / "corrupt.jar"

    mods_toml = """
[[mods]]
modId = "validmod"
"""
    with ZipFile(valid_jar, "w") as jar:
        jar.writestr("META-INF/mods.toml", mods_toml)

    corrupt_jar.write_bytes(b"This is not a valid ZIP file")

    mods = scanner.scan_directory(tmp_path)

    assert len(mods) == 1
    assert mods[0].mod_id == "validmod"


def test_scan_jar_corrupted_zip(scanner, tmp_path):
    """
    Test scanning a corrupted JAR file raises ModMetadataError.
    """
    jar_path = tmp_path / "corrupted.jar"
    jar_path.write_bytes(b"This is not a valid ZIP file")

    with pytest.raises(ModMetadataError) as exc_info:
        scanner.scan_jar(jar_path)

    assert "Failed to read JAR file" in str(exc_info.value)


def test_scan_jar_neoforge_empty_mods_list(scanner, tmp_path):
    """
    Test scanning a NeoForge JAR with empty mods list.
    """
    jar_path = tmp_path / "empty_neoforge.jar"
    mods_toml = "mods = []"

    with ZipFile(jar_path, "w") as jar:
        jar.writestr("META-INF/neoforge.mods.toml", mods_toml)

    mod = scanner.scan_jar(jar_path)

    assert mod.mod_type == ModType.UNKNOWN


def test_scan_jar_neoforge_invalid_toml(scanner, tmp_path):
    """
    Test scanning a NeoForge JAR with invalid TOML.
    """
    jar_path = tmp_path / "invalid_neoforge.jar"

    with ZipFile(jar_path, "w") as jar:
        jar.writestr("META-INF/neoforge.mods.toml", "invalid toml [[")

    mod = scanner.scan_jar(jar_path)

    assert mod.mod_type == ModType.UNKNOWN
