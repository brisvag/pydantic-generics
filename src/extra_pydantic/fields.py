from contextlib import contextmanager
from dataclasses import is_dataclass
from typing import (
    Generic,
    Iterable,
    Iterator,
    Mapping,
    Tuple,
    Type,
    get_args,
    get_origin,
)

import pydantic.config
import pydantic.fields
import pydantic.validators

from .validators import (
    coerce_dataclass_validator,
    element_casting_validator,
    mapping_casting_validator,
    simple_casting_validator,
    tuple_element_casting_validator,
)

__all__ = ["ModelField"]


@contextmanager
def extended_bultin_validators(field: pydantic.fields.ModelField) -> Iterator[None]:
    """
    Prepend a few custom validators to pydantic.validators._VALIDATORS.
    This ensures that our validators are called first if the field type
    matches one of the generics below.
    """
    v = [
        (type(Ellipsis), []),  # so the ellipsis type does not mess up things
        (
            Mapping,
            [mapping_casting_validator(field), simple_casting_validator(field.type_)],
        ),
        (
            Tuple,
            [
                tuple_element_casting_validator(field),
                simple_casting_validator(field.type_),
            ],
        ),
        (
            Iterable,
            [element_casting_validator(field), simple_casting_validator(field.type_)],
        ),
        (Generic, [simple_casting_validator(field.type_)]),
    ]
    before, pydantic.validators._VALIDATORS = (
        pydantic.validators._VALIDATORS,
        v + pydantic.validators._VALIDATORS,
    )
    try:
        yield
    finally:
        pydantic.validators._VALIDATORS = before


# patched ModelField that:
# - always uses both class validators and bultin validators
# - ensures the final field value is always coerced to the right type, if possible

# NOTE: root validators with `pre=False` *still* run after the type coercion


class ModelField(pydantic.fields.ModelField):
    def populate_validators(self) -> None:
        with extended_bultin_validators(self):
            super().populate_validators()
            # override self.validators generation, cause we need *both* class
            # validators and generic validators
            # TODO: not sure about this. Without this change, if we create validators,
            # no "smart" validation happens (so we have to manually validate fields
            # for lists, for example). However, with it we force type coercion no
            # matter what, even in cases where maybe we don't want it.
            class_validators_ = self.class_validators.values()
            if not self.sub_fields or self.shape == pydantic.fields.SHAPE_GENERIC:
                get_validators = getattr(self.type_, "__get_validators__", list)
                v_funcs = (
                    *[v.func for v in class_validators_ if v.each_item and v.pre],
                    *get_validators(),
                    *list(
                        pydantic.fields.find_validators(self.type_, self.model_config)
                    ),
                    *[v.func for v in class_validators_ if v.each_item and not v.pre],
                )
                self.validators = pydantic.class_validators.prep_validators(v_funcs)

            if is_dataclass(self.type_):
                self.validators.extend(
                    pydantic.class_validators.prep_validators(
                        [coerce_dataclass_validator(self.type_)]
                    )
                )

    def _type_analysis(self) -> None:
        origin = get_origin(self.outer_type_)
        if (
            origin is None
            or not isinstance(origin, type)
            or not issubclass(origin, Generic)  # type: ignore
        ):
            super()._type_analysis()
        else:
            self.shape = pydantic.fields.SHAPE_GENERIC
            # ellipsis breaks everything down the line, it needs to be a type
            args = [
                t if t is not Ellipsis else type(Ellipsis) for t in get_args(self.type_)
            ]
            self.sub_fields = [
                self._create_sub_type(t, f"{self.name}_{i}") for i, t in enumerate(args)
            ]
            self.type_: Type = origin
