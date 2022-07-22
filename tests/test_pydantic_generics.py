from typing import Any, Generic, Sequence, TypeVar, get_origin

import pytest

from pydantic_generics import BaseModel, create_model

T = TypeVar("T")


class MyGeneric(Generic[T]):
    def __init__(self, value: T):
        self.value = value


class MyGenericSequence(Sequence[T]):
    def __init__(self, data: Sequence[T]):
        self._data = list(data)

    def __getitem__(self, index: int) -> T:  # type: ignore
        return self._data[index]

    def __len__(self) -> int:
        return len(self._data)


CASES = [
    (MyGeneric, 1),
    # (MyGeneric[int], 1),
    (MyGenericSequence, [1]),
    # (MyGenericSequence[int], [1]),
]


@pytest.mark.parametrize("field, value", CASES)
def test_something(field: type, value: Any) -> None:
    Model = create_model("Model", x=(field, ...))
    assert issubclass(Model, BaseModel)
    instance = Model(x=value)
    assert isinstance(getattr(instance, "x"), get_origin(field) or field)
