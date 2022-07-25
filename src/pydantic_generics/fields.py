from contextlib import contextmanager
from typing import Generic, Iterator, Type

import pydantic.config
import pydantic.fields
import pydantic.validators

from .validators import simple_casting_validator

__all__ = ["ModelField"]


@contextmanager
def generic_types_allowed(field: pydantic.fields.ModelField) -> Iterator[None]:
    try:
        is_generic = issubclass(field.outer_type_, Generic)  # type: ignore
    except TypeError:
        is_generic = False

    config = field.model_config
    before, config.arbitrary_types_allowed = config.arbitrary_types_allowed, is_generic
    try:
        yield
    finally:
        config.arbitrary_types_allowed = before


@contextmanager
def generic_validator_inserted(type_: Type) -> Iterator[None]:
    v = (Generic, [simple_casting_validator(type_)])
    pydantic.validators._VALIDATORS.insert(0, v)
    try:
        yield
    finally:
        pydantic.validators._VALIDATORS.pop(0)


class ModelField(pydantic.fields.ModelField):
    def populate_validators(self) -> None:
        # XXX: not sure I like this, "generic_types_allowed"
        # the alternative would be to just say
        # "you have to use arbitrary_types_allowed if you want to use this"
        with generic_types_allowed(self), generic_validator_inserted(self.type_):
            super().populate_validators()
