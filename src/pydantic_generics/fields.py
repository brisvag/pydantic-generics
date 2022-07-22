from contextlib import contextmanager
from typing import Generic, Iterator

import pydantic.config
import pydantic.fields
import pydantic.validators

from .monkeypatch import patched_make_arbitrary_type_validator

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


class ModelField(pydantic.fields.ModelField):
    def populate_validators(self) -> None:
        with patched_make_arbitrary_type_validator():
            # XXX: not sure I like this, the alternative would be to just say
            # "you have to use arbitrary_types_allowed if you want to use this"
            with generic_types_allowed(self):
                super().populate_validators()
