# pytest-when

Plugin provides a `when` fixture, which enables the following way of mocking
the python objects:

```python
(
    when(some_object, "attribute")
    .called_with(1, 2, when.markers.any)
    .then_return("mocked")
)
```

It is readable and gives you a way to enable the mock only for a specific
argument's values. In this the attribute will be mocked, for specific
first two arguments and any third argument.

Inspired by <https://github.com/mockito/mockito-scala>

`.called_with` method arguments are compared with the
real callable signature and gives additional protection against
changing the real callable interface.

## Installation

```bash
pip install pytest-when
```


## Usage

After installing the package a new fixture `when` will be available.
See the following example how to use it:

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
        return "Not mocked"


def test_should_properly_patch_calls(when):
    when(Klass1, "some_method").called_with(
        "a",
        when.markers.any,
        kwarg1="b",
        kwarg2=when.markers.any,
    ).then_return("Mocked")

    assert (
        Klass1().some_method(
            "a",
            1,
            kwarg1="b",
            kwarg2="c",
        )
        == "Mocked"
    )
    assert (
        Klass1().some_method(
            "not mocked param",
            1,
            kwarg1="b",
            kwarg2="c",
        )
        == "Not mocked"
    )

# if you need to patch a function
def test_patch_a_function(when):
    when(example_module, "some_normal_function").called_with(
        "a",
        when.markers.any,
        kwarg1="b",
        kwarg2=when.markers.any,
    ).then_return("Mocked")

    assert (
            example_module.some_normal_function(
                "a",
                1,
                kwarg1="b",
                kwarg2="c",
            )
            == "Mocked"
    )
    assert (
            example_module.some_normal_function(
                "not mocked param",
                1,
                kwarg1="b",
                kwarg2="c",
            )
            == "Not mocked"
    )
```

It is possible to use 'when' with class methods and standalone functions
(in this case cls parameter will become a python module).

You can patch multiple times the same object with different "called_with"
parameters in a single test.

You can also patch multiple targets (cls, method)

See more examples at:
[test_integration](tests/test_integration.py)


## Setup for local developement

Requirements:
1. pdm <https://pdm.fming.dev/latest/#installation>
2. python3.8 (minimum supported by a tool)

```bash
pdm install
```

To run tests and linters use:
```bash
make test
make lint
```
