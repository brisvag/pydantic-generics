from typing import Any, Callable, Type, TypeVar

import pydantic.errors
import pydantic.validators

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
