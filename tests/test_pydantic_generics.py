from typing import (
    Any,
    Generic,
    List,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Sequence,
    TypeVar,
    get_origin,
)

import pytest

from pydantic_generics import BaseModel, create_model

T = TypeVar("T")
U = TypeVar("U")


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


class _CastMixin:
    @classmethod
    def __get_validators__(cls):
        yield cls.v

    @classmethod
    def v(cls, v):
        return cls(v)


class MyList(List[T]):
    def __init__(self, v):
        self.v = v


class MyMutableSequence(MutableSequence[T]):
    __delitem__ = None
    __getitem__ = None
    __len__ = None
    __setitem__ = None
    insert = None

    def __init__(self, v):
        self.v = v


class MyMutableSet(MutableSet[T]):
    __contains__ = None
    __iter__ = None
    __len__ = None
    add = None
    discard = None

    def __init__(self, v):
        self.v = v


class MyMutableMapping(MutableMapping[T, U]):
    __delitem__ = None
    __getitem__ = None
    __len__ = None
    __iter__ = None
    __setitem__ = None

    def __init__(self, v):
        self.v = v


CASES = [
    (MyGeneric, 1),
    (MyGenericSequence, [1]),
    (MyGeneric, 1),
    (MyGenericSequence, [1]),
    (MyList, [1]),
    (MyMutableSequence, [1]),
    (MyMutableSet, {1}),
    (MyMutableMapping, {1: 2}),
]


PARAMETRIZED_CASES = [
    (MyGeneric[int], 1),
    (MyGenericSequence[int], [1]),
    (MyGeneric[int], 1),
    (MyGenericSequence[int], [1]),
    (MyMutableSequence[str], [1]),
    (MyList[str], [1]),
    (MyMutableMapping[str, str], {1: 2}),
    (MyMutableSequence[str], {1}),
]


@pytest.mark.parametrize("field, value", CASES)
def test_something(field: type, value: Any) -> None:
    Model = create_model("Model", x=(field, ...))
    assert issubclass(Model, BaseModel)
    instance = Model(x=value)
    attr = getattr(instance, "x")
    custom_type = get_origin(field) or field
    assert isinstance(attr, custom_type)
