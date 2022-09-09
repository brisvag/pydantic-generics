from typing import Any, Type, no_type_check

import pydantic.main

from .monkeypatch import patched_pydantic_base_model, patched_pydantic_model_field, patched_dataclass_validator


_is_base_model_class_defined = False


class ModelMetaclass(pydantic.main.ModelMetaclass):
    @no_type_check
    def __new__(cls, name, bases, namespace, **kwargs):
        with patched_pydantic_model_field(), patched_dataclass_validator():
            new_cls = super().__new__(cls, name, bases, namespace, **kwargs)
            if _is_base_model_class_defined and not new_cls.__config__.arbitrary_types_allowed:
                raise ValueError('arbitrary_types_allowed must be True for extra_pydantic to work')
            return new_cls


class BaseModel(pydantic.main.BaseModel, metaclass=ModelMetaclass):
    pass


_is_base_model_class_defined = True


def create_model(__model_name: str, **kwargs: Any) -> Type["BaseModel"]:
    with patched_pydantic_base_model():
        return pydantic.main.create_model(__model_name, **kwargs)  # type: ignore
