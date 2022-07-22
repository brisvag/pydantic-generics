from typing import Any, Type, no_type_check

import pydantic.main

from .monkeypatch import patched_pydantic_base_model, patched_pydantic_model_field


class ModelMetaclass(pydantic.main.ModelMetaclass):
    @no_type_check
    def __new__(cls, name, bases, namespace, **kwargs):
        with patched_pydantic_model_field():
            return super().__new__(cls, name, bases, namespace, **kwargs)


class BaseModel(pydantic.main.BaseModel, metaclass=ModelMetaclass):
    pass


def create_model(__model_name: str, **kwargs: Any) -> Type["BaseModel"]:
    with patched_pydantic_base_model():
        return pydantic.main.create_model(__model_name, **kwargs)  # type: ignore
