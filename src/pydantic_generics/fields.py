from contextlib import contextmanager
from typing import Generic, Iterator, get_origin, get_args, Iterable, Mapping

import pydantic.config
import pydantic.fields
import pydantic.validators

from .validators import simple_casting_validator, element_casting_validator, mapping_casting_validator

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
def generic_validator_inserted(field: pydantic.fields.ModelField) -> Iterator[None]:
    v = [
        (Mapping, [mapping_casting_validator(field), simple_casting_validator(field.type_)]),
        (Iterable, [element_casting_validator(field), simple_casting_validator(field.type_)]),
        (Generic, [simple_casting_validator(field.type_)]),
    ]
    before, pydantic.validators._VALIDATORS = pydantic.validators._VALIDATORS, v + pydantic.validators._VALIDATORS
    try:
        yield
    finally:
        pydantic.validators._VALIDATORS = before


class ModelField(pydantic.fields.ModelField):
    def populate_validators(self) -> None:
        # XXX: not sure I like this, "generic_types_allowed"
        # the alternative would be to just say
        # "you have to use arbitrary_types_allowed if you want to use this"
        with generic_types_allowed(self), generic_validator_inserted(self):
            super().populate_validators()
            # override self.validators generation, cause we need *both* class validators
            # and generic validators
            # TODO: not sure about this. Without this change, if we create validators, no "smart"
            # validation happens (so we have to manually validate fields for lists, for example).
            # However, with it we force type coercion no matter what, even in cases where maybe we don't want it
            class_validators_ = self.class_validators.values()
            if not self.sub_fields or self.shape == pydantic.fields.SHAPE_GENERIC:
                get_validators = getattr(self.type_, '__get_validators__', list)
                v_funcs = (
                    *[v.func for v in class_validators_ if v.each_item and v.pre],
                    *get_validators(),
                    *list(pydantic.fields.find_validators(self.type_, self.model_config)),
                    *[v.func for v in class_validators_ if v.each_item and not v.pre],
                )
                self.validators = pydantic.class_validators.prep_validators(v_funcs)

    def _type_analysis(self):
        origin = get_origin(self.outer_type_)
        if origin is None or not isinstance(origin, type) or not issubclass(origin, Generic):
            super()._type_analysis()
        else:
            self.shape = pydantic.fields.SHAPE_GENERIC
            # ellipsis breaks everything down the line, and is otherwise useless other than for static typing
            self.sub_fields = [
                self._create_sub_type(t, f'{self.name}_{i}')
                for i, t in enumerate(get_args(self.type_))
                if t is not Ellipsis
            ]
            self.type_ = origin
