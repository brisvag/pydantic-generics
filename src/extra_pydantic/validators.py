from itertools import zip_longest
from typing import Any, Callable, Type, TypeVar
import dataclasses

import pydantic.errors
from pydantic.dataclasses import _validate_dataclass as _pydantic_validate_dataclass

T = TypeVar("T")


class CannotCastError(pydantic.errors.PydanticTypeError):
    msg_template = "failed to cast value to instance of {type}:\n  {error}"


def simple_casting_validator(type_: Type[T]) -> Callable[[T], T]:
    def arbitrary_type_validator(v: Any) -> T:
        if isinstance(v, type_):
            return v

        # cast
        try:
            return type_(v)  # type: ignore
        except Exception as e:
            raise CannotCastError(
                type=getattr(type_, "__name__", type_), error=str(e)
            ) from e

    return arbitrary_type_validator


class Missing:
    pass


def tuple_element_casting_validator(field) -> Callable[[T], T]:
    def cast_elements(v: Any) -> T:
        if not field.sub_fields:
            return v

        result = []
        if len(field.sub_fields) == 2 and field.sub_fields[1].type_ is type(Ellipsis):
            f = field.sub_fields[0]
            for i, v_ in enumerate(v):
                r, e = f.validate(v_, {}, loc=i)
                if e:
                    raise CannotCastError(type=f.type_, error='')
                result.append(r)
            return result
        else:
            for i, (v_, f) in enumerate(zip_longest(v, field.sub_fields, fillvalue=Missing)):
                if v_ is Missing or f is Missing:
                    raise ValueError('args must be either a single one, or as many as there are elements')
                r, e = f.validate(v_, {}, loc=i)
                if e:
                    raise CannotCastError(type=f.type_, error='')
                result.append(r)
            return result

    return cast_elements


def element_casting_validator(field) -> Callable[[T], T]:
    def cast_elements(v: Any) -> T:
        if not field.sub_fields:
            return v

        result = []
        if len(field.sub_fields) == 1:
            f = field.sub_fields[0]
            for i, v_ in enumerate(v):
                r, e = f.validate(v_, {}, loc=i)
                if e:
                    raise CannotCastError(type=f.type_, error='')
                result.append(r)
            return result
        else:
            for i, (v_, f) in enumerate(zip_longest(v, field.sub_fields, fillvalue=Missing)):
                if v_ is Missing or f is Missing:
                    raise ValueError('args must be either a single one, or as many as there are elements')
                r, e = f.validate(v_, {}, loc=i)
                if e:
                    raise CannotCastError(type=f.type_, error='')
                result.append(r)
            return result

    return cast_elements


def mapping_casting_validator(field) -> Callable[[T], T]:
    def cast_elements(v: Any) -> T:
        if not field.sub_fields:
            return v

        if len(field.sub_fields) != 2:
            raise ValueError('must pass 2 fields to mapping')

        result = {}
        for i, (k_, v_) in enumerate(v.items()):
            f_key = field.sub_fields[0]
            k, e = f_key.validate(k_, {}, loc=i)
            if e:
                raise CannotCastError(type=f_key.type_, error='')
            f_val = field.sub_fields[1]
            v, e = f_val.validate(v_, {}, loc=i)
            if e:
                raise CannotCastError(type=f_val.type_, error='')
            result[k] = v
        return result

    return cast_elements


def _validate_dataclass(cls, v, field):
    if field.allow_none and v is None:
        return None
    return _pydantic_validate_dataclass(cls, v)


def coerce_dataclass_validator(cls):
    def coerce_dataclass(v):
        if v is None:
            return None
        return cls(**dataclasses.asdict(v))
    return coerce_dataclass
