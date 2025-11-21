"""
Tests for web translation service.
"""

from pathlib import Path

import pytest

from uplang.web.service import TranslationService


@pytest.fixture
def mock_resourcepack(tmp_path):
    """
    Create a mock resource pack structure.
    """
    assets_dir = tmp_path / "assets"

    test_mod_dir = assets_dir / "testmod"
    test_mod_lang = test_mod_dir / "lang"
    test_mod_lang.mkdir(parents=True)

    (test_mod_lang / "en_us.json").write_text(
        (
            '{"item.testmod.sword": "Sword", "item.testmod.shield": "Shield", '
            '"block.testmod.stone": "Stone"}'
        ),
        encoding="utf-8",
    )

    (test_mod_lang / "zh_cn.json").write_text(
        '{"item.testmod.sword": "剑", "item.testmod.shield": "Shield"}',
        encoding="utf-8",
    )

    empty_mod_dir = assets_dir / "emptymod"
    empty_mod_lang = empty_mod_dir / "lang"
    empty_mod_lang.mkdir(parents=True)

    (empty_mod_lang / "en_us.json").write_text("{}", encoding="utf-8")

    no_zh_mod_dir = assets_dir / "nozhmod"
    no_zh_mod_lang = no_zh_mod_dir / "lang"
    no_zh_mod_lang.mkdir(parents=True)

    (no_zh_mod_lang / "en_us.json").write_text('{"key1": "value1"}', encoding="utf-8")

    return tmp_path


@pytest.fixture
def service(mock_resourcepack):
    """
    Create TranslationService with mock resource pack.
    """
    return TranslationService(mock_resourcepack)


def test_init(mock_resourcepack):
    """
    Test service initialization.
    """
    service = TranslationService(mock_resourcepack)

    assert service.resourcepack_dir == Path(mock_resourcepack)
    assert service.extractor is not None
    assert service.json_handler is not None


def test_get_all_mods(service):
    """
    Test getting all mods with statistics.
    """
    mods = service.get_all_mods()

    assert len(mods) == 3

    testmod = next(m for m in mods if m["mod_id"] == "testmod")
    assert testmod["total_keys"] == 3
    assert testmod["untranslated_count"] == 2
    assert testmod["translated_count"] == 1


def test_get_all_mods_no_assets(tmp_path):
    """
    Test get_all_mods with no assets directory.
    """
    service = TranslationService(tmp_path)
    mods = service.get_all_mods()

    assert mods == []


def test_get_all_mods_with_files_in_assets(tmp_path):
    """
    Test get_all_mods ignores files in assets directory.
    """
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()

    (assets_dir / "some_file.txt").write_text("not a mod")

    service = TranslationService(tmp_path)
    mods = service.get_all_mods()

    assert mods == []


def test_get_all_mods_no_lang_dir(tmp_path):
    """
    Test get_all_mods skips mods without lang directory.
    """
    assets_dir = tmp_path / "assets"
    mod_dir = assets_dir / "testmod"
    mod_dir.mkdir(parents=True)

    service = TranslationService(tmp_path)
    mods = service.get_all_mods()

    assert mods == []


def test_get_all_mods_no_en_file(tmp_path):
    """
    Test get_all_mods skips mods without en_us.json.
    """
    assets_dir = tmp_path / "assets"
    mod_dir = assets_dir / "testmod" / "lang"
    mod_dir.mkdir(parents=True)

    (mod_dir / "zh_cn.json").write_text('{"key": "value"}', encoding="utf-8")

    service = TranslationService(tmp_path)
    mods = service.get_all_mods()

    assert mods == []


def test_get_all_mods_invalid_json(tmp_path):
    """
    Test get_all_mods handles invalid JSON gracefully.
    """
    assets_dir = tmp_path / "assets"
    mod_dir = assets_dir / "testmod" / "lang"
    mod_dir.mkdir(parents=True)

    (mod_dir / "en_us.json").write_text("invalid json{", encoding="utf-8")

    service = TranslationService(tmp_path)
    mods = service.get_all_mods()

    assert len(mods) == 1
    assert mods[0]["total_keys"] == 0


def test_get_untranslated_items(service):
    """
    Test getting untranslated items for a mod.
    """
    items = service.get_untranslated_items("testmod")

    assert len(items) == 2

    shield_item = next(i for i in items if i["key"] == "item.testmod.shield")
    assert shield_item["english"] == "Shield"
    assert shield_item["chinese"] == "Shield"

    stone_item = next(i for i in items if i["key"] == "block.testmod.stone")
    assert stone_item["english"] == "Stone"
    assert stone_item["chinese"] == ""


def test_get_untranslated_items_no_zh_file(service):
    """
    Test getting untranslated items when zh_cn.json doesn't exist.
    """
    items = service.get_untranslated_items("nozhmod")

    assert len(items) == 1
    assert items[0]["key"] == "key1"
    assert items[0]["english"] == "value1"
    assert items[0]["chinese"] == ""


def test_get_untranslated_items_invalid_mod(service):
    """
    Test getting untranslated items for non-existent mod.
    """
    items = service.get_untranslated_items("nonexistent")

    assert items == []


def test_get_untranslated_items_no_en_file(service, tmp_path):
    """
    Test getting untranslated items when load fails.
    """
    items = service.get_untranslated_items("nonexistent_mod")

    assert items == []


def test_get_all_items(service):
    """
    Test getting all items for a mod.
    """
    items = service.get_all_items("testmod")

    assert len(items) == 3

    sword_item = next(i for i in items if i["key"] == "item.testmod.sword")
    assert sword_item["english"] == "Sword"
    assert sword_item["chinese"] == "剑"
    assert sword_item["is_translated"] is True

    shield_item = next(i for i in items if i["key"] == "item.testmod.shield")
    assert not shield_item["is_translated"]

    stone_item = next(i for i in items if i["key"] == "block.testmod.stone")
    assert not stone_item["is_translated"]
    assert stone_item["chinese"] == ""


def test_get_all_items_no_zh_file(service):
    """
    Test getting all items when zh_cn.json doesn't exist.
    """
    items = service.get_all_items("nozhmod")

    assert len(items) == 1
    assert not items[0]["is_translated"]


def test_get_all_items_invalid_mod(service):
    """
    Test getting all items for non-existent mod.
    """
    items = service.get_all_items("nonexistent")

    assert items == []


def test_save_translations(service):
    """
    Test saving translations.
    """
    translations = {"item.testmod.shield": "盾牌", "block.testmod.stone": "石头"}

    result = service.save_translations("testmod", translations)

    assert result is True

    zh_file_path = (
        service.resourcepack_dir / "assets" / "testmod" / "lang" / "zh_cn.json"
    )
    assert zh_file_path.exists()

    saved_content = service.json_handler.load(zh_file_path)
    assert saved_content["item.testmod.shield"] == "盾牌"
    assert saved_content["block.testmod.stone"] == "石头"
    assert saved_content["item.testmod.sword"] == "剑"


def test_save_translations_new_zh_file(service):
    """
    Test saving translations when zh_cn.json doesn't exist.
    """
    translations = {"key1": "翻译1"}

    result = service.save_translations("nozhmod", translations)

    assert result is True

    zh_file_path = (
        service.resourcepack_dir / "assets" / "nozhmod" / "lang" / "zh_cn.json"
    )
    assert zh_file_path.exists()


def test_save_translations_invalid_mod(service):
    """
    Test saving translations for non-existent mod.
    """
    translations = {"key": "value"}

    result = service.save_translations("nonexistent", translations)

    assert result is False


def test_save_translations_exception(service, monkeypatch):
    """
    Test save_translations handles exceptions.
    """

    def mock_save_failure(*args, **kwargs):
        raise OSError("Permission denied")

    monkeypatch.setattr(service.extractor, "save_to_resource_pack", mock_save_failure)

    translations = {"key": "value"}
    result = service.save_translations("testmod", translations)

    assert result is False


def test_count_untranslated(service):
    """
    Test counting untranslated items.
    """
    count = service._count_untranslated("testmod")

    assert count == 2


def test_count_untranslated_no_zh_file(service):
    """
    Test counting untranslated when zh_cn.json doesn't exist.
    """
    count = service._count_untranslated("nozhmod")

    assert count == 1


def test_count_untranslated_invalid_mod(service):
    """
    Test counting untranslated for non-existent mod.
    """
    count = service._count_untranslated("nonexistent")

    assert count == 0


def test_reorder_by_reference(service):
    """
    Test reordering target dict by reference dict.
    """
    reference = {"key1": "ref1", "key2": "ref2", "key3": "ref3"}
    target = {"key3": "val3", "key1": "val1", "key4": "val4", "key2": "val2"}

    result = service._reorder_by_reference(target, reference)

    assert list(result.keys()) == ["key1", "key2", "key3", "key4"]
    assert result["key1"] == "val1"
    assert result["key2"] == "val2"
    assert result["key3"] == "val3"
    assert result["key4"] == "val4"


def test_reorder_by_reference_partial_match(service):
    """
    Test reordering when target has keys not in reference.
    """
    reference = {"key1": "ref1", "key2": "ref2"}
    target = {"key3": "val3", "key1": "val1"}

    result = service._reorder_by_reference(target, reference)

    assert list(result.keys()) == ["key1", "key3"]


def test_reorder_by_reference_empty_target(service):
    """
    Test reordering with empty target dict.
    """
    reference = {"key1": "ref1", "key2": "ref2"}
    target = {}

    result = service._reorder_by_reference(target, reference)

    assert result == {}
