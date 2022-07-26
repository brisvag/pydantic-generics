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
    Union,
    Literal,
    Optional,
)

import pytest

from pydantic_generics import BaseModel, create_model

T = TypeVar("T")
U = TypeVar("U")


class _ClassValidatorMixin:
    @classmethod
    def __get_validators__(cls):
        yield cls.v

    @classmethod
    def v(cls, v):
        # not a coercing validator!
        return v


class _ReprMixin:
    def __repr__(self):
        return f'{self.__class__.__name__}({repr(self.v)})'


class MyGeneric(_ReprMixin, Generic[T]):
    def __init__(self, value: T):
        self.v = value


class MyValidatingGeneric(_ClassValidatorMixin, MyGeneric[T]):
    pass


class MyGenericSequence(_ReprMixin, Sequence[T]):
    __len__ = None
    __getitem__ = None

    def __init__(self, data: Sequence[T]):
        self.v = list(data)


class MyValidatingGenericSequence(_ClassValidatorMixin, MyGenericSequence[T]):
    pass


class MyList(_ReprMixin, List[T]):
    def __init__(self, v):
        self.v = list(v)


class MyValidatingList(_ClassValidatorMixin, MyList[T]):
    pass


class MyMutableSequence(_ReprMixin, MutableSequence[T]):
    __delitem__ = None
    __getitem__ = None
    __len__ = None
    __setitem__ = None
    insert = None

    def __init__(self, v):
        self.v = list(v)


class MyValidatingMutableSequence(_ClassValidatorMixin, MyMutableSequence[T]):
    pass


class MyMutableSet(_ReprMixin, MutableSet[T]):
    __contains__ = None
    __len__ = None
    __iter__ = None
    add = None
    discard = None

    def __init__(self, v):
        self.v = set(v)


class MyValidatingMutableSet(_ClassValidatorMixin, MyMutableSet[T]):
    pass


class MyMutableMapping(_ReprMixin, MutableMapping[T, U]):
    __delitem__ = None
    __getitem__ = None
    __len__ = None
    __setitem__ = None
    __iter__ = None

    def __init__(self, v):
        self.v = dict(v)


class MyValidatingMutableMapping(_ClassValidatorMixin, MyMutableMapping[T]):
    pass


class MyString(str):
    pass


class MyValidatingString(_ClassValidatorMixin, MyString):
    pass


CASES = [
    (MyGeneric, 1),
    (MyGenericSequence, [1]),
    (MyGeneric, 1),
    (MyGenericSequence, [1]),
    (MyList, [1]),
    (MyMutableSequence, [1]),
    (MyMutableSet, {1}),
    (MyMutableMapping, {1: 2}),
    (MyValidatingGeneric, 1),
    (MyValidatingGenericSequence, [1]),
    (MyValidatingGeneric, 1),
    (MyValidatingGenericSequence, [1]),
    (MyValidatingList, [1]),
    (MyValidatingMutableSequence, [1]),
    (MyValidatingMutableSet, {1}),
    (MyValidatingMutableMapping, {1: 2}),
    # input of different type that can be coerced
    (MyGenericSequence, {1}),
    (MyList, {1}),
    (MyMutableSequence, {1}),
    (MyMutableSet, [1]),
    (MyValidatingGenericSequence, {1}),
    (MyValidatingList, {1}),
    (MyValidatingMutableSequence, {1}),
    (MyValidatingMutableSet, [1]),
]


@pytest.mark.parametrize("field, value", CASES)
def test_simple_generics(field: type, value: Any) -> None:
    Model = create_model("Model", x=(field, ...))
    assert issubclass(Model, BaseModel)
    instance = Model(x=value)
    attr = getattr(instance, "x")
    custom_type = get_origin(field) or field
    assert isinstance(attr, custom_type)


PARAMETRIZED_CASES = [
    (MyGeneric[int], 1, 1),
    (MyGenericSequence[int], [1], [1]),
    (MyGeneric[int], 1, 1),
    (MyGenericSequence[int], [1], [1]),
    (MyMutableSet[int], {1}, {1}),
    (MyValidatingGeneric[int], 1, 1),
    (MyValidatingGenericSequence[int], [1], [1]),
    (MyValidatingGeneric[int], 1, 1),
    (MyValidatingGenericSequence[int], [1], [1]),
    (MyValidatingMutableSet[int], {1}, {1}),
    # coerce element type
    (MyMutableSequence[str], [1], ['1']),
    (MyList[str], [1], ['1']),
    (MyMutableMapping[str, str], {1: 2}, {'1': '2'}),
    (MyMutableSet[str], {1}, {'1'}),
    (MyMutableSequence[str], {1}, ['1']),
    (MyValidatingMutableSequence[str], [1], ['1']),
    (MyValidatingList[str], [1], ['1']),
    (MyValidatingMutableMapping[str, str], {1: 2}, {'1': '2'}),
    (MyValidatingMutableSet[str], {1}, {'1'}),
    (MyValidatingMutableSequence[str], {1}, ['1']),
    # coerce container type as well
    (MyMutableSequence[str], {1}, ['1']),
    (MyList[str], {1}, ['1']),
    (MyMutableSet[str], [1], {'1'}),
    (MyValidatingMutableSequence[str], {1}, ['1']),
    (MyValidatingList[str], {1}, ['1']),
    (MyValidatingMutableSet[str], [1], {'1'}),
]


@pytest.mark.parametrize("field, value, expected", PARAMETRIZED_CASES)
def test_parametrized_generics(field: type, value: Any, expected: Any) -> None:
    Model = create_model("Model", x=(field, ...))
    assert issubclass(Model, BaseModel)
    instance = Model(x=value)
    attr = getattr(instance, "x")
    custom_type = get_origin(field) or field
    assert isinstance(attr, custom_type)
    assert attr.v == expected


OTHER_CASES = [
    # union tries to coerce in order and stops as soon as it succeeds
    (Union[str, float], 1.0, '1', str),
    (Union[float, str], '1', 1.0, float),
    # optional should not fail with None
    (Optional[int], None, None, type(None)),
    (Optional[int], 1, 1, int),
    # Literal is not a subclass of type, so it can cause issues when using `issubclass`
    (Literal[1], 1, 1, int),
    # subclass of builtin
    (MyString, '1', '1', MyString),
    (MyValidatingString, '1', '1', MyValidatingString),
]


@pytest.mark.parametrize("field, value, expected, expected_type", OTHER_CASES)
def test_other_types(field: type, value: Any, expected: Any, expected_type: type) -> None:
    Model = create_model("Model", x=(field, ...))
    assert issubclass(Model, BaseModel)
    instance = Model(x=value)
    attr = getattr(instance, "x")
    assert attr == expected
    assert type(attr) is expected_type
