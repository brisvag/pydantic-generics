from typing import List, MutableSequence, Any, get_origin, MutableSet, MutableMapping, TypeVar

import pytest

from pydantic_generics import BaseModel, create_model

T = TypeVar("T")
U = TypeVar("U")


class Wrap:
    def __init__(self, v):
        self.v = v

    def __getattr__(self, name):
        return getattr(self.v, name)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.v})'

    @classmethod
    def __get_validators__(cls):
        yield cls.v

    @classmethod
    def v(cls, v):
        return v


class MyList(List[T], Wrap):
    pass


class MySeq(MutableSequence[T], Wrap):
    __delitem__ = None
    __getitem__ = None
    __len__ = None
    __setitem__ = None
    insert = None
    pass


class MySet(MutableSet[T], Wrap):
    __contains__ = None
    __iter__ = None
    __len__ = None
    add = None
    discard = None
    pass


class MyDict(MutableMapping[T, U], Wrap):
    __delitem__ = None
    __getitem__ = None
    __len__ = None
    __iter__ = None
    __setitem__ = None
    pass


CASES = [
    (MyList, [1]),
    # (MyList[str], [1]),
    (MySeq, [1]),
    # (MySeq[str], [1]),
    (MySet, {1}),
    # (MySeq[str], {1}),
    (MyDict, {1: 2}),
    # (MyDict[str, str], {1: 2}),
]


@pytest.mark.parametrize("field, value", CASES)
def test_something(field: type, value: Any) -> None:
    Model = create_model("Model", x=(field, ...))
    assert issubclass(Model, BaseModel)
    instance = Model(x=value)
    assert isinstance(getattr(instance, "x"), get_origin(field) or field)
