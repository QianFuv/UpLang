"""
UpLang - Minecraft Modpack Language File Synchronizer

A command-line tool to streamline the process of updating language files
for Minecraft Java Edition modpacks.
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("uplang")
except PackageNotFoundError:
    __version__ = "0.0.0.dev"

__author__ = "QianFuv"
__email__ = "qianfuv@qq.com"
__license__ = "MIT"

__all__ = ["__version__", "__author__", "__email__", "__license__"]
