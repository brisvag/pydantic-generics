from contextlib import contextmanager
from typing import Any, Type, no_type_check

import pydantic.main

from .monkeypatch import patched_pydantic_base_model, patched_pydantic_model_field, patched_dataclass_validator


is_basemodel = False


@contextmanager
def is_basemodel():
    # allows us to declare BaseModel without triggering the arbitrary_types_allowed error
    global is_basemodel
    is_basemodel = True
    yield
    is_basemodel = False


class ModelMetaclass(pydantic.main.ModelMetaclass):
    @no_type_check
    def __new__(cls, name, bases, namespace, **kwargs):
        with patched_pydantic_model_field(), patched_dataclass_validator():
            new_cls = super().__new__(cls, name, bases, namespace, **kwargs)
            if not is_basemodel and not new_cls.__config__.arbitrary_types_allowed:
                raise ValueError('arbitrary_types_allowed must be True for pydantic_generics to work')
            return new_cls


with is_basemodel():
    class BaseModel(pydantic.main.BaseModel, metaclass=ModelMetaclass):
        pass


def create_model(__model_name: str, **kwargs: Any) -> Type["BaseModel"]:
    with patched_pydantic_base_model():
        return pydantic.main.create_model(__model_name, **kwargs)  # type: ignore
