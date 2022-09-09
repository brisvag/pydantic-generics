import sys
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    List,
    Literal,
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Optional,
    Protocol,
    Sequence,
    SupportsInt,
    Tuple,
    TypeVar,
    Union,
    get_origin,
    runtime_checkable,
)

import pytest
from pydantic.color import Color
from pydantic.dataclasses import dataclass
from pydantic.error_wrappers import ValidationError

from extra_pydantic import BaseModel, create_model

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")


class Config:
    arbitrary_types_allowed = True


class _ClassValidatorMixin:
    @classmethod
    def __get_validators__(cls):
        yield cls.v

    @classmethod
    def v(cls, v):
        # not a coercing validator!
        return v


class _DunderMixin:
    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.v)})"

    def __eq__(self, o):
        return self.v == o


class MyGeneric(_DunderMixin, Generic[T]):
    def __init__(self, value: T):
        self.v = value


class MyValidatingGeneric(_ClassValidatorMixin, MyGeneric[T]):
    pass


class MyGenericSequence(_DunderMixin, Sequence[T]):
    __len__ = None
    __getitem__ = None

    def __init__(self, data: Sequence[T]):
        self.v = list(data)


class MyValidatingGenericSequence(_ClassValidatorMixin, MyGenericSequence[T]):
    pass


class MyList(_DunderMixin, List[T]):
    def __init__(self, v):
        self.v = list(v)


class MyValidatingList(_ClassValidatorMixin, MyList[T]):
    pass


class MyTuple(_DunderMixin, Tuple[T]):
    def __init__(self, v):
        self.v = tuple(v)


class MyValidatingTuple(_ClassValidatorMixin, MyTuple[T]):
    pass


class MyMutableSequence(_DunderMixin, MutableSequence[T]):
    __delitem__ = None
    __getitem__ = None
    __len__ = None
    __setitem__ = None
    insert = None

    def __init__(self, v):
        self.v = list(v)


class MyValidatingMutableSequence(_ClassValidatorMixin, MyMutableSequence[T]):
    pass


class MyMutableSet(_DunderMixin, MutableSet[T]):
    __contains__ = None
    __len__ = None
    __iter__ = None
    add = None
    discard = None

    def __init__(self, v):
        self.v = set(v)


class MyValidatingMutableSet(_ClassValidatorMixin, MyMutableSet[T]):
    pass


class MyMutableMapping(_DunderMixin, MutableMapping[T, U]):
    __delitem__ = None
    __getitem__ = None
    __len__ = None
    __setitem__ = None

    def __init__(self, v):
        self.v = dict(v)

    def __iter__(self):
        yield from self.v

    def __getitem__(self, k):
        return self.v[k]


class MyValidatingMutableMapping(_ClassValidatorMixin, MyMutableMapping[T, U]):
    pass


class MyString(str):
    pass


class MyValidatingString(_ClassValidatorMixin, MyString):
    pass


class MyTripleParameterIterable(Generic[T, U, V]):
    """Not a subclass of iterable, but technically iterable"""

    def __init__(self, v):
        self.v = list(v)

    def __iter__(self):
        yield from self.v


class MyGenericWithCustomValidator(Generic[T, U]):
    def __init__(self, v):
        self.v = v

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, field):
        if isinstance(v, field.sub_fields[0].type_):
            return "first"
        elif isinstance(v, field.sub_fields[1].type_):
            return "second"


class MyTripleTuple(_DunderMixin, Tuple[T, U, V]):
    def __init__(self, v):
        self.v = tuple(v)


@runtime_checkable
class MyProtocol(Protocol):
    x: int


class MyConcreteProtocol(MyProtocol):
    def __init__(self, x):
        self.x = x

    def __eq__(self, other):
        return self.x == self.x


class FollowsProtocol:
    def __init__(self, x):
        self.x = x

    def __eq__(self, other):
        return self.x == self.x


class DoesNotFollowProtocol:
    def __init__(self, y):
        self.y = y


@dataclass
class MyDataClass:
    a: int


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
    (MyValidatingTuple, (1,)),
    (MyValidatingMutableSequence, [1]),
    (MyValidatingMutableSet, {1}),
    (MyValidatingMutableMapping, {1: 2}),
    # input of different type that can be coerced
    (MyGenericSequence, {1}),
    (MyList, {1}),
    (MyTuple, [1]),
    (MyMutableSequence, {1}),
    (MyMutableSet, [1]),
    (MyValidatingGenericSequence, {1}),
    (MyValidatingList, {1}),
    (MyValidatingTuple, {1}),
    (MyValidatingMutableSequence, {1}),
    (MyValidatingMutableSet, [1]),
]


@pytest.mark.parametrize("field, value", CASES)
def test_simple_generics(field: type, value: Any) -> None:
    Model = create_model("Model", x=(field, ...), __config__=Config)
    assert issubclass(Model, BaseModel)
    instance = Model(x=value)
    attr = getattr(instance, "x")
    custom_type = get_origin(field) or field
    assert type(attr) is custom_type


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
    (MyMutableSequence[str], [1], ["1"]),
    (MyList[str], [1], ["1"]),
    (MyTuple[str], (1,), ("1",)),
    (MyMutableMapping[str, str], {1: 2}, {"1": "2"}),
    (MyMutableSet[str], {1}, {"1"}),
    (MyMutableSequence[str], {1}, ["1"]),
    (MyValidatingMutableSequence[str], [1], ["1"]),
    (MyValidatingList[str], [1], ["1"]),
    (MyValidatingTuple[str], (1,), ("1",)),
    (MyValidatingMutableMapping[str, str], {1: 2}, {"1": "2"}),
    (MyValidatingMutableSet[str], {1}, {"1"}),
    (MyValidatingMutableSequence[str], {1}, ["1"]),
    # coerce container type as well
    (MyMutableSequence[str], {1}, ["1"]),
    (MyList[str], {1}, ["1"]),
    (MyTuple[str], {1}, ("1",)),
    (MyMutableSet[str], [1], {"1"}),
    (MyValidatingMutableSequence[str], {1}, ["1"]),
    (MyValidatingList[str], {1}, ["1"]),
    (MyValidatingTuple[str], {1}, ("1",)),
    (MyValidatingMutableSet[str], [1], {"1"}),
    (MyList[int], "123", [1, 2, 3]),
    # multiple parameters for iterable will validate one by one
    (MyTripleTuple[int, float, str], [1, 2, 3], (1, 2.0, "3")),
    # custom validation coerce to the right
    (MyGenericWithCustomValidator[str, int], "a", "first"),
    (MyGenericWithCustomValidator[str, int], 1, "second"),
    (
        MyList[MyList[Union[int, str]]],
        [[1, "a", 1.0], [False]],
        [MyList([1, "a", 1]), MyList([0])],
    ),
    (
        MyMutableMapping[MyString, MyMutableSet[float]],
        {1: {1, False}},
        {MyString("1"): MyMutableSet({1.0, 0.0})},
    ),
]


@pytest.mark.parametrize("field, value, expected", PARAMETRIZED_CASES)
def test_parametrized_generics(field: type, value: Any, expected: Any) -> None:
    Model = create_model("Model", x=(field, ...), __config__=Config)
    assert issubclass(Model, BaseModel)
    instance = Model(x=value)
    attr = getattr(instance, "x")
    custom_type = get_origin(field) or field
    assert isinstance(attr, custom_type)
    if issubclass(custom_type, Iterable):
        assert all(v == e for v, e in zip(attr.v, expected))
        assert all(type(v) is type(e) for v, e in zip(attr.v, expected))
    if issubclass(custom_type, Mapping):
        assert all(v == e for v, e in zip(attr.v.values(), expected.values()))
        assert all(
            type(v) is type(e) for v, e in zip(attr.v.values(), expected.values())
        )
    assert attr.v == expected


def noop():
    pass


OTHER_CASES = [
    # union tries to coerce in order and stops as soon as it succeeds
    (Union[str, float], 1.0, "1.0", str),
    (Union[float, str], "1", 1.0, float),
    # optional should not fail with None
    (Optional[int], None, None, type(None)),
    (Optional[int], 1, 1, int),
    # Literal is not a subclass of type, so it can cause issues when using `issubclass`
    (Literal[1], 1, 1, int),
    # subclass of builtin
    (MyString, "1", "1", MyString),
    (MyValidatingString, "1", "1", MyValidatingString),
    (Callable, noop, noop, type(noop)),
    # abstract classes and protocols should not be coerced
    (SupportsInt, 1, 1, int),
    (MyProtocol, FollowsProtocol(1), FollowsProtocol(1), FollowsProtocol),
    # but "concrete" protocols should
    (MyConcreteProtocol, FollowsProtocol(1), MyConcreteProtocol(1), MyConcreteProtocol),
    (MyDataClass, MyDataClass(a=1), MyDataClass(a=1), MyDataClass),
    # optional dataclass must accept None
    (Optional[MyDataClass], MyDataClass(a=1), MyDataClass(a=1), MyDataClass),
    (Optional[MyDataClass], None, None, type(None)),
]


@pytest.mark.parametrize("field, value, expected, expected_type", OTHER_CASES)
def test_other_types(
    field: type, value: Any, expected: Any, expected_type: type
) -> None:
    Model = create_model("Model", x=(field, ...), __config__=Config)
    assert issubclass(Model, BaseModel)
    instance = Model(x=value)
    attr = getattr(instance, "x")
    assert attr == expected
    assert type(attr) is expected_type


FAILING_CASES = [
    (MyGenericSequence, 1),
    (MyMutableSequence, None),
    (MyMutableMapping, [1]),
    (MyGenericSequence[int], "asd"),
    (MyMutableMapping[int, int], {"a": "b"}),
    # TODO: this should not fail like this
    (MyTripleParameterIterable[int, float, str], [1]),
    (MyTuple[int], (1, 1)),
    (SupportsInt, "asd"),
    (MyProtocol, DoesNotFollowProtocol(1)),
]


@pytest.mark.parametrize("field, value", FAILING_CASES)
def test_incompatible_types(field: type, value: Any) -> None:
    Model = create_model("Model", x=(field, ...), __config__=Config)
    assert issubclass(Model, BaseModel)
    with pytest.raises(ValidationError):
        Model(x=value)


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python3.9 or higher")
def test_python39() -> None:
    field = MyTripleTuple[str, ...]
    value = (1, 2)
    expected = ("1", "2")
    Model = create_model("Model", x=(field, ...), __config__=Config)
    assert issubclass(Model, BaseModel)
    instance = Model(x=value)
    attr = getattr(instance, "x")
    custom_type = get_origin(field) or field
    assert isinstance(attr, custom_type)
    assert all(v == e for v, e in zip(attr.v, expected))
    assert all(type(v) is type(e) for v, e in zip(attr.v, expected))
    assert attr.v == expected

    # different length of parameters and value
    field = MyTripleTuple[int, float, str]
    value = [1, 2]
    Model = create_model("Model", x=(field, ...), __config__=Config)
    assert issubclass(Model, BaseModel)
    with pytest.raises(ValidationError):
        instance = Model(x=value)


def test_color():
    """test separately because == does not work on Color"""

    class M(BaseModel):
        Config = Config
        c: Color

    m = M(c="red")
    assert isinstance(m.c, Color)
    assert m.c.as_named() == "red"
