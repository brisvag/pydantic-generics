# extra-pydantic

[![License](https://img.shields.io/pypi/l/extra-pydantic.svg?color=green)](https://github.com/tlambert03/extra-pydantic/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/extra-pydantic.svg?color=green)](https://pypi.org/project/extra-pydantic)
[![Python Version](https://img.shields.io/pypi/pyversions/extra-pydantic.svg?color=green)](https://python.org)
[![CI](https://github.com/tlambert03/extra-pydantic/actions/workflows/ci.yml/badge.svg)](https://github.com/tlambert03/extra-pydantic/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/tlambert03/extra-pydantic/branch/main/graph/badge.svg)](https://codecov.io/gh/tlambert03/extra-pydantic)

Better and more consistent [pydantic](https://github.com/pydantic/pydantic) support for (parametrized) generics, custom builtin-like classes, protocols, dataclasses.

## Why

Objects that happen to *also* be mappings/lists/tuple get validated as such, rather than obeying the type hints provided. This even results in unexpected errors with lists not being recognized as such. Additionally, Generics are treated very differently when parametrized compared to when they aren't.

Consider this simple list-like `MyList` object: it has some dummy methods to mimic a list and a simple validator that just returns a `MyList` object. It also inherits from generic `Sequence` so we can parametrize it.

```py
from typing import T, Sequence

class MyList(Sequence[T]):
    def __init__(self, data):
        self.v = list(data)
    def __iter__(self):
        yield from self.v
    def __getitem__(self, key):
        return self.v[key]
    def __len__(self):
        return len(self.v)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_list_like

    @classmethod
    def validate_list_like(v):
        return cls(v)
```

We then create a model using the above as our field type hint:

```py
from pydantic import BaseModel

class MyModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    a: MyList
    b: MyList[float]
```

When instantiating `MyModel`, one would expect to always get two `MyList` fields, one of which coerces its contents to `float`. Instead, we get:

```py
MyModel(a=[1, 2, 3], b=[1, 2, 3])
# MyModel(a=MyList([1, 2, 3]), b=[1.0, 2.0, 3.0])
```

And even worse:
```py
MyModel(a=MyList([1, 2, 3]), b=MyList([1, 2, 3]))
```
```py
ValidationError: 1 validation error for MyModel
b
  value is not a valid sequence (type=type_error.sequence)
```

## How

To fix the above issue, we have to monkeypatch several places across the pydantic codebase. Due pydantic's function-oriented design, simply subclassing and overloading methods is out of the question. This library is however careful to always undo any patch after it served its purpose (hence the many context managers). This ensures that one can use normal `pydantic.BaseModel`s right next to `extra_pydantic.BaseModel` without issue.

The main changes to `pydantic` are the following:
- `ModelField` ensures *both* default validators and custom class validators are always run. This is a substantial change from `pydantic`, where only one of the two is exectuted.
- validators for sequence-like and mapping-like
    - return the correct types (and coerce if necessary and possible, instead of always failing)
    - validate and coerce parametrized field as expected, without losing information about the outer type
- everything is coerced, if possible, without having to write a class validator as in the example above
    - note that if a class cannot be auto-coerced by simply passing the input value to its init as a single argument, you can still dolve this by writing a custom class validator!
