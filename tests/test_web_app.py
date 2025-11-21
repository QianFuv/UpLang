"""
Tests for FastAPI application.
"""

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from uplang.web.app import create_app, start_server


@pytest.fixture
def mock_resourcepack(tmp_path):
    """
    Create a mock resource pack structure.
    """
    assets_dir = tmp_path / "assets"
    test_mod_lang = assets_dir / "testmod" / "lang"
    test_mod_lang.mkdir(parents=True)

    (test_mod_lang / "en_us.json").write_text(
        '{"item.sword": "Sword"}', encoding="utf-8"
    )

    return tmp_path


@pytest.fixture
def mock_static_dir(tmp_path):
    """
    Create a temporary static directory with test files.
    """
    static_dir = tmp_path / "static"
    static_dir.mkdir()

    (static_dir / "index.html").write_text(
        "<html><body>Test</body></html>", encoding="utf-8"
    )
    (static_dir / "test.css").write_text("body { color: red; }", encoding="utf-8")

    return static_dir


def test_create_app(mock_resourcepack):
    """
    Test FastAPI app creation.
    """
    app = create_app(mock_resourcepack)

    assert isinstance(app, FastAPI)
    assert app.title == "UpLang Translation Interface"
    assert app.version == "1.0.0"


def test_create_app_includes_api_router(mock_resourcepack, mock_static_dir):
    """
    Test that app includes API router.
    """
    app = create_app(mock_resourcepack, static_dir=mock_static_dir)

    api_routes = [
        route
        for route in app.routes
        if hasattr(route, "path") and route.path.startswith("/api")
    ]
    assert len(api_routes) > 0


def test_create_app_mounts_static(mock_resourcepack, mock_static_dir):
    """
    Test that app mounts static files.
    """
    app = create_app(mock_resourcepack, static_dir=mock_static_dir)

    static_routes = [
        route
        for route in app.routes
        if hasattr(route, "path") and route.path == "/static"
    ]
    assert len(static_routes) > 0


def test_root_endpoint(mock_resourcepack, mock_static_dir):
    """
    Test GET / endpoint serves index.html.
    """
    app = create_app(mock_resourcepack, static_dir=mock_static_dir)
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200


def test_favicon_endpoint(mock_resourcepack):
    """
    Test GET /favicon.ico endpoint returns 204.
    """
    app = create_app(mock_resourcepack)
    client = TestClient(app)

    response = client.get("/favicon.ico")

    assert response.status_code == 204


def test_favicon_endpoint_no_content(mock_resourcepack):
    """
    Test favicon endpoint returns empty response.
    """
    app = create_app(mock_resourcepack)
    client = TestClient(app)

    response = client.get("/favicon.ico")

    assert response.content == b""


def test_api_endpoints_accessible(mock_resourcepack, mock_static_dir):
    """
    Test that API endpoints are accessible through app.
    """
    app = create_app(mock_resourcepack, static_dir=mock_static_dir)
    client = TestClient(app)

    response = client.get("/api/mods")

    assert response.status_code == 200


def test_start_server(mock_resourcepack):
    """
    Test server start function.
    """
    with patch("uvicorn.run") as mock_run:
        start_server(mock_resourcepack, host="0.0.0.0", port=9000)

        mock_run.assert_called_once()

        call_args = mock_run.call_args
        assert call_args[1]["host"] == "0.0.0.0"
        assert call_args[1]["port"] == 9000

        app_arg = call_args[0][0]
        assert isinstance(app_arg, FastAPI)


def test_start_server_default_params(mock_resourcepack):
    """
    Test server start with default parameters.
    """
    with patch("uvicorn.run") as mock_run:
        start_server(mock_resourcepack)

        call_args = mock_run.call_args
        assert call_args[1]["host"] == "127.0.0.1"
        assert call_args[1]["port"] == 8000


def test_app_description(mock_resourcepack, mock_static_dir):
    """
    Test app has correct description.
    """
    app = create_app(mock_resourcepack, static_dir=mock_static_dir)

    assert "Minecraft modpack translations" in app.description


def test_static_file_serving(mock_resourcepack, mock_static_dir):
    """
    Test that static files can be served.
    """
    app = create_app(mock_resourcepack, static_dir=mock_static_dir)
    client = TestClient(app)

    response = client.get("/static/test.css")

    assert response.status_code == 200
