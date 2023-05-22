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
        ValueError,
        match="Incompatible call",
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
    assert actual == (
        ("a_arg", "a_arg not default"),
        ("b_arg", "b_arg default"),
        ("c_kw", "c_kw default"),
        ("d_kw", "d_kw default"),
    )

    # check if parameter was not specified
    with pytest.raises(
        ValueError,
        match="Not specified parameter a_arg",
    ):
        create_call_key(
            inspect.signature(call_with_defaults),
            b_arg="b_arg not default",
        )
