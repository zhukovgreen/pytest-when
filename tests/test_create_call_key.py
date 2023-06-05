import inspect

import pytest

from pytest_when.when import Markers, create_call_key


def foo(a_arg, b_arg, *, c_kw, d_kw):
    ...


def test_should_build_a_key_from_non_empty_call():
    actual = create_call_key(
        inspect.signature(foo),
        Markers.any,
        2,
        c_kw=3,
        d_kw=4,
    )
    assert actual == (
        ("a_arg", Markers.any),
        ("b_arg", 2),
        ("c_kw", 3),
        ("d_kw", 4),
    )


def test_result_should_be_hashable():
    {}[
        create_call_key(
            inspect.signature(foo),
            Markers.any,
            2,
            c_kw=3,
            d_kw=4,
        )
    ] = 1
    {}[
        create_call_key(
            inspect.signature(foo),
            {"some_inner": "container"},
            ["some", "list"],
            c_kw=3,
            d_kw=4,
        )
    ] = 2


def test_should_work_for_class_methods_as_well():
    class Some:
        def call(self, a_arg, b_arg, *, c_kw, d_kw):
            ...

    actual = create_call_key(
        inspect.signature(Some.call),
        Markers.any,
        Markers.any,
        2,
        c_kw=3,
        d_kw=4,
    )
    assert actual == (
        ("self", Markers.any),
        ("a_arg", Markers.any),
        ("b_arg", 2),
        ("c_kw", 3),
        ("d_kw", 4),
    )


def test_should_raise_exception_on_incompatible_calls():
    with pytest.raises(
        TypeError,
        match="missing a required argument: 'd_kw'",
    ):
        create_call_key(
            inspect.signature(foo),
            Markers.any,
            2,
            c_kw=3,
        )


def test_should_generate_a_key_based_on_the_params_order_of_the_signature():
    actual = create_call_key(
        inspect.signature(foo),
        b_arg=2,
        a_arg=Markers.any,
        d_kw=4,
        c_kw=3,
    )
    assert actual == (
        ("a_arg", Markers.any),
        ("b_arg", 2),
        ("c_kw", 3),
        ("d_kw", 4),
    )


def test_should_properly_work_with_default_values_in_the_signature():
    def call_with_defaults(
        a_arg,
        b_arg="b_arg default",
        *,
        c_kw="c_kw default",
        d_kw="d_kw default",
    ):
        ...

    actual = create_call_key(
        inspect.signature(call_with_defaults),
        "a_arg not default",
    )
    assert actual == (("a_arg", "a_arg not default"),)

    # check if parameter was not specified
    with pytest.raises(
        TypeError,
        match="missing a required argument: 'a_arg'",
    ):
        create_call_key(
            inspect.signature(call_with_defaults),
            b_arg="b_arg not default",
        )


def test_should_work_with_variadic_args_and_kwargs():
    def foo_with_variadic_args_kwargs(*args, **kwargs) -> str:
        ...

    actual = create_call_key(
        inspect.signature(foo_with_variadic_args_kwargs),
        1,
        2,
        a=3,
        b=4,
        c=Markers.any,
    )
    assert actual == (
        ("args", (1, 2)),
        (
            "kwargs",
            (
                ("a", 3),
                ("b", 4),
                ("c", Markers.any),
            ),
        ),
    )

    def foo_with_variadic_kwargs(
        just_a_arg,
        *just_var_arg,
        just_b_kwarg=1,
        **kwargs,
    ):
        ...

    actual = create_call_key(
        inspect.signature(foo_with_variadic_kwargs),
        1,
        2,
        3,
        c=4,
        d=5,
    )
    assert actual == (
        ("just_a_arg", 1),
        ("just_var_arg", (2, 3)),
        (
            "kwargs",
            (
                ("c", 4),
                ("d", 5),
            ),
        ),
    )
