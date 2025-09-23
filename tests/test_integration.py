from tests.resources import example_module


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

    def some_method_with_defaults(
        self,
        arg1: str,
        arg2: int,
        *,
        kwarg1: str,
        kwarg2: str = "some default string",
    ) -> str:
        return "Not mocked"

    @classmethod
    def some_class_method(
        cls,
        arg1: str,
        arg2: int,
        *,
        kwarg1: str,
        kwarg2: str,
    ) -> str:
        return "Not mocked"


class Klass2:
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


def test_should_work_with_classmethods(when):
    when(Klass1, "some_class_method").called_with(
        "a",
        when.markers.any,
        kwarg1="b",
        kwarg2=when.markers.any,
    ).then_return("Mocked")

    assert (
        Klass1().some_class_method(
            "a",
            1,
            kwarg1="b",
            kwarg2="c",
        )
        == "Mocked"
    )
    assert (
        Klass1.some_class_method(
            "not mocked param",
            1,
            kwarg1="b",
            kwarg2="c",
        )
        == "Not mocked"
    )


def test_should_work_with_normal_functions(when):
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


def test_should_be_able_to_patch_multiple_calls(when):
    when(Klass1, "some_method").called_with(
        "a",
        when.markers.any,
        kwarg1="b",
        kwarg2=when.markers.any,
    ).then_return("Mocked first time")

    when(Klass1, "some_method").called_with(
        when.markers.any,
        1,
        kwarg1=when.markers.any,
        kwarg2="b",
    ).then_return("Mocked second time")

    assert (
        Klass1().some_method(
            "a",
            1,
            kwarg1="b",
            kwarg2="c",
        )
        == "Mocked first time"
    )
    assert (
        Klass1().some_method(
            "any",
            1,
            kwarg1="any too",
            kwarg2="b",
        )
        == "Mocked second time"
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


def test_should_properly_repatch(when):
    when(Klass1, "some_method").called_with(
        "a",
        when.markers.any,
        kwarg1="b",
        kwarg2=when.markers.any,
    ).then_return("Mocked first time")

    when(Klass1, "some_method").called_with(
        "a",
        when.markers.any,
        kwarg1="b",
        kwarg2=when.markers.any,
    ).then_return("Mocked second time")

    assert (
        Klass1().some_method(
            "a",
            1,
            kwarg1="b",
            kwarg2="c",
        )
        == "Mocked second time"
    )


def test_should_be_able_to_patch_multiple_objects(when):
    when(Klass1, "some_method").called_with(
        "a",
        when.markers.any,
        kwarg1="b",
        kwarg2=when.markers.any,
    ).then_return("Mocked Klass1")

    when(Klass2, "some_method").called_with(
        "b",
        when.markers.any,
        kwarg1="c",
        kwarg2=when.markers.any,
    ).then_return("Mocked Klass2")

    assert (
        Klass1().some_method(
            "a",
            1,
            kwarg1="b",
            kwarg2="c",
        )
        == "Mocked Klass1"
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

    assert (
        Klass2().some_method(
            "b",
            1,
            kwarg1="c",
            kwarg2="any",
        )
        == "Mocked Klass2"
    )
    assert (
        Klass2().some_method(
            "not mocked param",
            1,
            kwarg1="b",
            kwarg2="c",
        )
        == "Not mocked"
    )


def test_should_work_with_default_params_in_functions(when):
    patched_klass = (
        when(Klass1, "some_method_with_defaults")
        .called_with(
            when.markers.any,
            when.markers.any,
            kwarg1=when.markers.any,
            kwarg2="some default string",
        )
        .then_return("Mocked")
    )

    assert (
        Klass1().some_method_with_defaults(
            "a",
            1,
            kwarg1="b",
            kwarg2="some default string",
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
    patched_klass.assert_called()


def test_should_work_with_variadic_args_kwargs(when):
    patched_foo = (
        when(example_module, "some_foo_with_variadic_args_kwargs")
        .called_with(1, a=2)
        .then_return("Mocked")
    )
    assert (
        example_module.some_foo_with_variadic_args_kwargs(1, a=2) == "Mocked"
    )
    assert (
        example_module.some_foo_with_variadic_args_kwargs(1, a=3)
        == "Not mocked"
    )
    patched_foo.assert_called()
    patched_foo = (
        when(example_module, "some_foo_with_variadic_args_kwargs")
        .called_with(2, 3, 4, a=1)
        .then_return("Mocked1")
    )
    assert (
        example_module.some_foo_with_variadic_args_kwargs(2, 3, 4, a=1)
        == "Mocked1"
    )

    assert (
        example_module.some_foo_with_variadic_args_kwargs(3, 2, 4, a=1)
        == "Not mocked"
    )


def test_should_work_with_foo_without_args(when):
    patched_foo = (
        when(example_module, "some_foo_without_args")
        .called_with()
        .then_return("Mocked")
    )
    assert example_module.some_foo_without_args() == "Mocked"
    patched_foo.assert_called()


def test_should_work_with_star_kwargs(when, mocker):
    class _:  # noqa: N801
        @staticmethod
        def foo(a, **kwargs):  # noqa: ARG004
            return "Not mocked"

    patched_foo = (
        when(_, "foo")
        .called_with(
            1,
            kwarg_a=when.markers.any,
            kwarg_b="bbb",
        )
        .then_return("Mocked")
    )
    assert _.foo(1, kwarg_b="bbb", kwarg_a="aaa") == "Mocked"
    assert _.foo(1, kwarg_a="aaa", kwarg_b="bbb") == "Mocked"
    assert _.foo(2, kwarg_a="aaa", kwarg_b="bbb") == "Not mocked"
    patched_foo.assert_called()


# Use a simple object to store call state for test assertions

from typing import Any

class CallState:
    def __init__(self):
        self.called: bool = False
        self.last_args: tuple[Any, ...] = ()
        self.last_kwargs: dict[str, Any] = {}

call_state = CallState()

def call_tracker(*args, **kwargs):
    call_state.called = True
    call_state.last_args = args
    call_state.last_kwargs = kwargs
    return "called!"


def test_then_call_invokes_callback(when):
    from pytest_when.when import MockedCalls
    MockedCalls.__dict__["mocked_calls_registry"].clear()
    call_state.called = False
    when(Klass1, "some_method").called_with(
        "a",
        1,
        kwarg1="b",
        kwarg2="c",
    ).then_call(call_tracker)

    result = Klass1().some_method("a", 1, kwarg1="b", kwarg2="c")
    assert result == "called!"
    assert call_state.called is True
    # Check type and values, not instance equality
    assert isinstance(call_state.last_args[0], Klass1)
    assert call_state.last_args[1:] == ("a", 1)
    assert call_state.last_kwargs == {"kwarg1": "b", "kwarg2": "c"}


def test_then_call_with_different_args(when):
    from pytest_when.when import MockedCalls
    MockedCalls.__dict__["mocked_calls_registry"].clear()
    call_state.called = False
    when(Klass1, "some_method").called_with(
        "x",
        2,
        kwarg1="y",
        kwarg2="z",
    ).then_call(call_tracker)

    # Should not call tracker for unmatched args
    result = Klass1().some_method("not matched", 2, kwarg1="y", kwarg2="z")
    assert result == "Not mocked"
    assert call_state.called is False

    # Should call tracker for matched args
    result = Klass1().some_method("x", 2, kwarg1="y", kwarg2="z")
    assert result == "called!"
    assert call_state.called is True
    assert isinstance(call_state.last_args[0], Klass1)
    assert call_state.last_args[1:] == ("x", 2)
    assert call_state.last_kwargs == {"kwarg1": "y", "kwarg2": "z"}
