"""Parametrized Generic support for pydantic"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pydantic-generics")
except PackageNotFoundError:
    __version__ = "uninstalled"
__author__ = "Talley Lambert"
__email__ = "talley.lambert@gmail.com"
