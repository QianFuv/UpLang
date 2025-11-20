"""
Tests for package initialization.
"""

import sys
import pytest
from importlib.metadata import PackageNotFoundError


def test_version_when_package_installed():
    """
    Test that __version__ is set correctly when package is installed.
    """
    import uplang

    assert hasattr(uplang, "__version__")
    assert isinstance(uplang.__version__, str)


def test_version_when_package_not_found(monkeypatch):
    """
    Test that __version__ defaults to 0.0.0.dev when package is not found.
    """
    def mock_version(package_name):
        raise PackageNotFoundError(f"Package {package_name} not found")

    import importlib.metadata
    monkeypatch.setattr(importlib.metadata, "version", mock_version)

    if "uplang" in sys.modules:
        del sys.modules["uplang"]

    import uplang

    assert uplang.__version__ == "0.0.0.dev"


def test_module_attributes():
    """
    Test that all expected module attributes are present.
    """
    import uplang

    assert hasattr(uplang, "__author__")
    assert uplang.__author__ == "QianFuv"

    assert hasattr(uplang, "__email__")
    assert uplang.__email__ == "qianfuv@qq.com"

    assert hasattr(uplang, "__license__")
    assert uplang.__license__ == "MIT"


def test_all_exports():
    """
    Test that __all__ contains expected exports.
    """
    import uplang

    expected_exports = ["__version__", "__author__", "__email__", "__license__"]
    assert uplang.__all__ == expected_exports
