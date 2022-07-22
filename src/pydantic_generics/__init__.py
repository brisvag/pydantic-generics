"""Parametrized Generic support for pydantic."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pydantic-generics")
except PackageNotFoundError:
    __version__ = "uninstalled"
__author__ = "Talley Lambert"
__email__ = "talley.lambert@gmail.com"

from .main import BaseModel, create_model
from .monkeypatch import patched_pydantic_base_model

__all__ = ["BaseModel", "create_model", "patched_pydantic_base_model"]
