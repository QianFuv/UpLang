"""
Tests for web module initialization.
"""



def test_import_create_app():
    """
    Test that create_app can be imported from web module.
    """
    from uplang.web import create_app

    assert create_app is not None
    assert callable(create_app)


def test_web_module_exports():
    """
    Test web module __all__ exports.
    """
    from uplang import web

    assert hasattr(web, "__all__")
    assert "create_app" in web.__all__


def test_create_app_functionality():
    """
    Test that imported create_app actually works.
    """
    from pathlib import Path

    from fastapi import FastAPI

    from uplang.web import create_app

    temp_dir = Path(__file__).parent
    app = create_app(temp_dir)

    assert isinstance(app, FastAPI)
