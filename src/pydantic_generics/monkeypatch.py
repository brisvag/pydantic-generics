from contextlib import contextmanager
from types import ModuleType
from typing import Iterator

import pydantic.fields
import pydantic.main
import pydantic.validators


@contextmanager
def patched_pydantic_base_model() -> Iterator[None]:
    """Monkeypatch pydantic.main.BaseModel to use our own BaseModel."""
    from .main import BaseModel

    orig, pydantic.main.BaseModel = pydantic.main.BaseModel, BaseModel
    try:
        yield
    finally:
        pydantic.main.BaseModel = orig


@contextmanager
def patched_pydantic_model_field(mod: ModuleType = pydantic.main) -> Iterator[None]:
    """Monkeypatch pydantic.fields.ModelField to use our own ModelField."""
    from .fields import ModelField

    orig = getattr(mod, "ModelField")
    setattr(mod, "ModelField", ModelField)
    try:
        yield
    finally:
        setattr(mod, "ModelField", orig)


@contextmanager
def patched_make_arbitrary_type_validator() -> Iterator[None]:
    """Monkeypatch pydantic make_arbitrary_type_validator."""
    from .validators import simple_casting_validator

    orig = pydantic.validators.make_arbitrary_type_validator
    pydantic.validators.make_arbitrary_type_validator = simple_casting_validator
    try:
        yield
    finally:
        pydantic.validators.make_arbitrary_type_validator = orig


@contextmanager
def patched_dataclass_validator():
    from .validators import _validate_dataclass

    orig, pydantic.dataclasses._validate_dataclass = pydantic.dataclasses._validate_dataclass, _validate_dataclass
    try:
        yield
    finally:
        pydantic.dataclasses._validate_dataclass = orig
