[![PyPI](https://img.shields.io/pypi/v/pytest-when.svg)](https://pypi.python.org/pypi/pytest-when)
[![Build](https://github.com/Tinche/tightwrap/workflows/CI/badge.svg)](https://github.com/zhukovgreen/pytest-when/actions/workflows/test-lint.yml?query=workflow:%22Test+Action%22)
[![Supported Python Versions](https://img.shields.io/python/required-version-toml?tomlFilePath=https://raw.githubusercontent.com/zhukovgreen/pytest-when/main/pyproject.toml)](https://raw.githubusercontent.com/zhukovgreen/pytest-when/main/pyproject.toml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

# pytest-when

<img src="./logo.png" width="250"/>

Inspired
by [mokito-scala](https://github.com/mockito/mockito-scala), `pytest-when`
provides a fixture for `pytest` to simplify the mocking of python objects:

## Purpose

More readable than the full `Given...When...Then` pattern, `pytest-when` is
meant for developers who want to test for behaviour, without any extra
overhead.
Enable the mock only for a specific argument's values to make code more
readable.

## Benefits

In this example, when you specify the first two arguments and *any* third
argument, the attribute will be mocked,

```python
(
    when(some_object, "attribute")
    .called_with(1, 2, when.markers.any)
    .then_return("attribute mocked")
)
```

Note that the `.called_with` method arguments are compared with the real
callable signature.
This gives additional protection against changing the real callable interface.

With `when` fixture, the following expression:

```python
when(example_module, "some_normal_function").called_with(
    "a",
    1,
    kwarg1="b",
    kwarg2=2,
).then_return("Mocked")

```

is roughly equal to:

```python

mock_only_for_calls = (
    call("a", 1, kwarg1="b", kwarg2=2),
    "Mocked",
)

def matches(
        call: Call,
        mocked_calls_registry: tuple[tuple[call, ReturnType], ...],
) -> bool:
    ...

def create_call(*args, **kwargs) -> Call:
    ...

def side_effect_callback(*args, **kwargs):
    if matches(create_call(*args, **kwargs), mock_only_for_calls):
        return mock_only_for_calls[1]
    return unittest.mock.DEFAULT


mocker.patch.object(
    example_module,
    "some_normal_function",
    autospec=True,
    side_effect=side_effect_callback,
)
```

where logic of `matches` and `create_call` is not trivial

## Installation

Install the package into your development environment, from
[pypi](https://pypi.org/project/pytest-when/), using `pip`, for example:

```bash
pip install pytest-when
```

## Implementation

Onced installed, the `when` fixture will be available just like the rest of
the `pytest` plugins.
See the following example of how to use it:

```python
# class which we're going to mock in the test
class Klass1:
    def some_method(
            self,
            arg1: str,
            arg2: int,
            *,
            kwarg1: str,
            kwarg2: str,
    ) -> str:
        return "some_method not mocked"


def test_should_properly_patch_calls(when):
    when(Klass1, "some_method").called_with(
        "a",
        when.markers.any,
        kwarg1="b",
        kwarg2=when.markers.any,
    ).then_return("some method mocked")

    assert (
            Klass1().some_method(
                "a",
                1,
                kwarg1="b",
                kwarg2="c",
            )
            == "some method mocked"
    )
    assert (
            Klass1().some_method(
                "not mocked param",
                1,
                kwarg1="b",
                kwarg2="c",
            )
            == "some method not mocked"
    )


# if you need to patch a function
def test_patch_a_function(when):
    when(example_module, "some_normal_function").called_with(
        "a",
        when.markers.any,
        kwarg1="b",
        kwarg2=when.markers.any,
    ).then_return("some_normal_function mocked")

    assert (
            example_module.some_normal_function(
                "a",
                1,
                kwarg1="b",
                kwarg2="c",
            )
            == "some_normal_function mocked"
    )
    assert (
            example_module.some_normal_function(
                "not mocked param",
                1,
                kwarg1="b",
                kwarg2="c",
            )
            == "some_normal_function not mocked"
    )
```

It is possible to use `when` with class methods and standalone functions
(in this case cls parameter will become a python module).

You can patch the same object multiple times using different `called_with`
parameters in a single test.

You can also patch multiple targets (cls, method)

See more examples at:
[test_integration](tests/test_integration.py)

## Setup for local developement

The project can be extended by cloning the repo and
installing [the `PDM` build tool](https://pdm-project.org/latest/#recommended-installation-method)
So, the development environment requires:

1. pdm <https://pdm.fming.dev/latest/#installation>
2. python3.8 or greater

```bash
pdm install
```

To run tests and linters use:

```bash
make test
make lint
```
