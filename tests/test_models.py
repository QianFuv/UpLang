"""Tests for models module."""

from pathlib import Path

import pytest

from uplang.models import Mod, ModComparisonResult, SyncStats, ModType, ModStatus


class TestMod:
    """Test cases for Mod dataclass."""

    def test_mod_creation(self):
        """Test creating a Mod instance."""
        mod = Mod(
            mod_id="test_mod",
            version="1.0.0",
            file_path=Path("/test/test_mod.jar"),
            mod_type=ModType.FORGE,
            file_hash="abcd1234"
        )

        assert mod.mod_id == "test_mod"
        assert mod.version == "1.0.0"
        assert mod.file_path == Path("/test/test_mod.jar")
        assert mod.mod_type == ModType.FORGE
        assert mod.file_hash == "abcd1234"

    def test_mod_equality(self):
        """Test Mod equality comparison."""
        mod1 = Mod("test_mod", "1.0.0", Path("/test/test_mod.jar"))
        mod2 = Mod("test_mod", "1.0.0", Path("/test/test_mod.jar"))
        mod3 = Mod("other_mod", "1.0.0", Path("/test/other_mod.jar"))

        assert mod1 == mod2
        assert mod1 != mod3

    def test_mod_hash(self):
        """Test Mod hash functionality."""
        mod1 = Mod("test_mod", "1.0.0", Path("/test/test_mod.jar"))
        mod2 = Mod("test_mod", "1.0.0", Path("/test/test_mod.jar"))

        # Same mods should have same hash
        assert hash(mod1) == hash(mod2)

        # Can be used in sets
        mod_set = {mod1, mod2}
        assert len(mod_set) == 1

    def test_mod_is_recognized(self):
        """Test mod recognition detection."""
        recognized_mod = Mod("test_mod", "1.0.0", Path("/test/test_mod.jar"))
        unrecognized_mod = Mod("unrecognized_test", "1.0.0", Path("/test/test.jar"))

        assert recognized_mod.is_recognized
        assert not unrecognized_mod.is_recognized

    def test_mod_display_name(self):
        """Test mod display name generation."""
        recognized_mod = Mod("test_mod", "1.0.0", Path("/test/test_mod.jar"))
        unrecognized_mod = Mod("unrecognized_test", "1.0.0", Path("/test/test.jar"))

        assert recognized_mod.display_name == "test_mod"
        assert unrecognized_mod.display_name == "test"


class TestModComparisonResult:
    """Test cases for ModComparisonResult dataclass."""

    def test_comparison_result_creation(self):
        """Test creating a ModComparisonResult instance."""
        mod1 = Mod("mod1", "1.0.0", Path("/test/mod1.jar"))
        mod2 = Mod("mod2", "1.0.0", Path("/test/mod2.jar"))

        result = ModComparisonResult(
            new_mods={mod1},
            updated_mods={mod2}
        )

        assert mod1 in result.new_mods
        assert mod2 in result.updated_mods
        assert len(result.deleted_mods) == 0
        assert len(result.unchanged_mods) == 0

    def test_comparison_result_has_changes(self):
        """Test has_changes property."""
        mod1 = Mod("mod1", "1.0.0", Path("/test/mod1.jar"))

        # No changes
        result_empty = ModComparisonResult()
        assert not result_empty.has_changes

        # With changes
        result_with_changes = ModComparisonResult(new_mods={mod1})
        assert result_with_changes.has_changes

    def test_comparison_result_total_changes(self):
        """Test total_changes property."""
        mod1 = Mod("mod1", "1.0.0", Path("/test/mod1.jar"))
        mod2 = Mod("mod2", "1.0.0", Path("/test/mod2.jar"))
        mod3 = Mod("mod3", "1.0.0", Path("/test/mod3.jar"))

        result = ModComparisonResult(
            new_mods={mod1},
            updated_mods={mod2},
            deleted_mods={mod3}
        )

        assert result.total_changes == 3


class TestSyncStats:
    """Test cases for SyncStats dataclass."""

    def test_sync_stats_creation(self):
        """Test creating a SyncStats instance."""
        stats = SyncStats(
            keys_added=5,
            keys_removed=2,
            files_processed=3,
            files_skipped=1,
            errors=0
        )

        assert stats.keys_added == 5
        assert stats.keys_removed == 2
        assert stats.files_processed == 3
        assert stats.files_skipped == 1
        assert stats.errors == 0

    def test_sync_stats_total_changes(self):
        """Test total_changes property."""
        stats = SyncStats(keys_added=5, keys_removed=2)
        assert stats.total_changes == 7

    def test_sync_stats_has_changes(self):
        """Test has_changes property."""
        stats_no_changes = SyncStats()
        stats_with_changes = SyncStats(keys_added=1)

        assert not stats_no_changes.has_changes
        assert stats_with_changes.has_changes