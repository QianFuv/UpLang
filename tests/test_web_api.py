"""
Tests for web API endpoints.
"""


import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient

from uplang.web.api import TranslationUpdate, create_router


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
        '{"item.sword": "Sword", "item.shield": "Shield"}', encoding="utf-8"
    )

    (test_mod_lang / "zh_cn.json").write_text('{"item.sword": "剑"}', encoding="utf-8")

    another_mod_dir = assets_dir / "anothermod"
    another_mod_lang = another_mod_dir / "lang"
    another_mod_lang.mkdir(parents=True)

    (another_mod_lang / "en_us.json").write_text(
        '{"block.stone": "Stone"}', encoding="utf-8"
    )

    return tmp_path


@pytest.fixture
def router(mock_resourcepack):
    """
    Create API router with test client.
    """
    return create_router(mock_resourcepack)


@pytest.fixture
def client(router):
    """
    Create test client with router.
    """
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)

    return TestClient(app)


def test_create_router(mock_resourcepack):
    """
    Test router creation.
    """
    router = create_router(mock_resourcepack)

    assert isinstance(router, APIRouter)
    assert router.prefix == "/api"


def test_translation_update_model():
    """
    Test TranslationUpdate model.
    """
    data = {"translations": {"key1": "value1", "key2": "value2"}}
    update = TranslationUpdate(**data)

    assert update.translations == {"key1": "value1", "key2": "value2"}


def test_get_mods(client):
    """
    Test GET /api/mods endpoint.
    """
    response = client.get("/api/mods")

    assert response.status_code == 200

    mods = response.json()
    assert isinstance(mods, list)
    assert len(mods) == 2

    testmod = next(m for m in mods if m["mod_id"] == "anothermod")
    assert testmod["total_keys"] == 1
    assert "untranslated_count" in testmod
    assert "translated_count" in testmod


def test_get_mod_items_all(client):
    """
    Test GET /api/mods/{mod_id} with filter=all.
    """
    response = client.get("/api/mods/testmod?filter=all")

    assert response.status_code == 200

    data = response.json()
    assert data["mod_id"] == "testmod"
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_get_mod_items_untranslated(client):
    """
    Test GET /api/mods/{mod_id} with filter=untranslated.
    """
    response = client.get("/api/mods/testmod?filter=untranslated")

    assert response.status_code == 200

    data = response.json()
    assert data["mod_id"] == "testmod"
    assert len(data["items"]) == 1
    assert data["items"][0]["key"] == "item.shield"


def test_get_mod_items_translated(client):
    """
    Test GET /api/mods/{mod_id} with filter=translated.
    """
    response = client.get("/api/mods/testmod?filter=translated")

    assert response.status_code == 200

    data = response.json()
    assert data["mod_id"] == "testmod"

    translated_items = [item for item in data["items"] if item.get("is_translated")]
    assert len(translated_items) == 1
    assert translated_items[0]["key"] == "item.sword"


def test_get_mod_items_default_filter(client):
    """
    Test GET /api/mods/{mod_id} without filter parameter.
    """
    response = client.get("/api/mods/testmod")

    assert response.status_code == 200

    data = response.json()
    assert data["mod_id"] == "testmod"
    assert len(data["items"]) == 2


def test_update_translations_success(client, mock_resourcepack):
    """
    Test PUT /api/mods/{mod_id}/translations with valid data.
    """
    translations_data = {"translations": {"item.shield": "盾牌"}}

    response = client.put("/api/mods/testmod/translations", json=translations_data)

    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "message" in data

    zh_file_path = mock_resourcepack / "assets" / "testmod" / "lang" / "zh_cn.json"
    assert zh_file_path.exists()


def test_update_translations_failure(client, monkeypatch):
    """
    Test PUT /api/mods/{mod_id}/translations with save failure.
    """

    from uplang.web import service

    original_save = service.TranslationService.save_translations

    def mock_save_failure(self, mod_id, translations):
        return False

    monkeypatch.setattr(
        service.TranslationService, "save_translations", mock_save_failure
    )

    translations_data = {"translations": {"item.shield": "盾牌"}}

    response = client.put("/api/mods/testmod/translations", json=translations_data)

    assert response.status_code == 500
    assert "Failed to save translations" in response.json()["detail"]

    monkeypatch.setattr(service.TranslationService, "save_translations", original_save)


def test_get_stats(client):
    """
    Test GET /api/stats endpoint.
    """
    response = client.get("/api/stats")

    assert response.status_code == 200

    data = response.json()
    assert "total_mods" in data
    assert "total_keys" in data
    assert "total_translated" in data
    assert "total_untranslated" in data
    assert "progress_percentage" in data

    assert data["total_mods"] == 2
    assert data["total_keys"] == 3
    assert isinstance(data["progress_percentage"], float)


def test_get_stats_with_zero_keys(tmp_path):
    """
    Test GET /api/stats with no keys.
    """
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()

    router = create_router(tmp_path)

    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)

    client = TestClient(app)

    response = client.get("/api/stats")

    assert response.status_code == 200

    data = response.json()
    assert data["total_keys"] == 0
    assert data["progress_percentage"] == 0


def test_get_mod_items_nonexistent_mod(client):
    """
    Test GET /api/mods/{mod_id} with non-existent mod.
    """
    response = client.get("/api/mods/nonexistent?filter=all")

    assert response.status_code == 200

    data = response.json()
    assert data["mod_id"] == "nonexistent"
    assert data["total"] == 0
    assert len(data["items"]) == 0


def test_update_translations_empty_dict(client, mock_resourcepack):
    """
    Test PUT /api/mods/{mod_id}/translations with empty translations.
    """
    translations_data = {"translations": {}}

    response = client.put("/api/mods/testmod/translations", json=translations_data)

    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
