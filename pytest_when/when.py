# ruff: noqa: SLF001

from __future__ import annotations

import enum
import functools
import inspect

from collections.abc import Callable, Hashable, Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    NewType,
    Protocol,
    TypeAlias,
    TypeVar,
)

import pytest

from friendly_sequences import Seq
from pytest_mock.plugin import MockCacheItem
from typing_extensions import ParamSpec


if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from pytest_mock import MockerFixture


class HasNameDunder(Protocol):
    __name__: str


_TargetCls = TypeVar("_TargetCls", bound=HasNameDunder)
_TargetMethodReturn = TypeVar("_TargetMethodReturn")

_TargetClsName = NewType("_TargetClsName", str)
_TargetMethodName = NewType("_TargetMethodName", str)
_TargetMethodParams = ParamSpec("_TargetMethodParams")
_TargetClsMethodKey = tuple[_TargetClsName, _TargetMethodName]

_TargetMethodArgs = tuple[Any, ...]
_TargetMethodKwargs = dict[str, Any]

_CallKeyParamDef = dict[str, Any]
_CallKey = tuple[tuple[str, Any], ...]
_CallLazyValue: TypeAlias = Callable[[], _TargetMethodReturn]


class Markers(enum.Enum):
    """Markers for defining When.called_with arguments.

    Markers.any - means the argument could be anything
    """

    any = "any"


def make_container_hashable(
    container: tuple[tuple[str, Any], ...],
) -> tuple[tuple[str, Any], ...]:
    """Make call signature hashable recursively."""
    return tuple((arg, make_hashable(value)) for arg, value in container)


@functools.singledispatch
def make_hashable(val) -> Hashable:
    """Single dispatch function to ensure the generic val is hashable."""
    return val


@make_hashable.register
def _(val: Mapping) -> tuple[tuple[str, Any], ...]:
    return tuple((k, make_hashable(v)) for k, v in val.items())


@make_hashable.register(list)
@make_hashable.register(set)
def _(val: list[Any] | set[Any]) -> tuple[Any, ...]:
    return tuple(map(make_hashable, val))


def create_call_key(
    original_callable_sig: inspect.Signature,
    *args: _TargetMethodArgs,
    **kwargs: _TargetMethodKwargs,
) -> _CallKey:
    """Create a call identification key for the given function.

    This key represents a certain call to the function. The order
    of kwargs is not important and will be allocated based on order
    of the kwargs in the function signature.

    Supports normal functions as well as class methods.
    """
    call = original_callable_sig.bind(*args, **kwargs)

    return make_container_hashable(tuple(call.arguments.items()))


def handle_variadic_args_kwargs(key: tuple[str, Any]) -> tuple[str, Any]:
    if key[0] == "kwargs":
        return key[1]
    return (key,)  # type: ignore


def get_mocked_call_result(
    original_callable_sig: inspect.Signature,
    mocked_calls: dict[
        _CallKey,
        _CallLazyValue,
    ],
    *args: _TargetMethodArgs,
    **kwargs: _TargetMethodKwargs,
) -> _TargetMethodReturn:  # type: ignore
    call_key = create_call_key(
        original_callable_sig,
        *args,
        **kwargs,
    )

    def params_are_compatible(
        param_in_mocked_call: _CallKeyParamDef,
        param_in_call: _CallKeyParamDef,
    ) -> bool:
        def values_matching(v1, v2) -> bool:
            if isinstance(v1, tuple):
                return Seq(v1).zip(v2).starmap(values_matching).all()
            if v1 is Markers.any:
                return True
            return v1 == v2

        return (
            Seq(param_in_call)
            .map(
                lambda key: values_matching(
                    param_in_call[key],
                    param_in_mocked_call[key],
                )
            )
            .all()
        )

    def call_matched_call_key(mocked_call_key: _CallKey) -> bool:
        return params_are_compatible(
            (
                Seq(
                    call_key,
                )
                .map(handle_variadic_args_kwargs)
                .flatten()
                .to_dict()
            ),
            (
                Seq(
                    mocked_call_key,
                )
                .map(handle_variadic_args_kwargs)
                .flatten()
                .to_dict()
            ),
        )

    for call in filter(call_matched_call_key, mocked_calls):
        # unwrapping the result of the lazy value
        return mocked_calls[call]()
    raise KeyError(f"Call {call_key} is not in mocked_calls {mocked_calls}")


def side_effect_factory(
    origin_callable: Callable[_TargetMethodParams, _TargetMethodReturn],
    mocked_calls: dict[_CallKey, _CallLazyValue],
) -> Callable[_TargetMethodParams, _TargetMethodReturn]:
    def side_effect(
        *args: _TargetMethodParams.args,
        **kwargs: _TargetMethodParams.kwargs,
    ) -> _TargetMethodReturn:
        try:
            return get_mocked_call_result(
                inspect.signature(origin_callable),
                mocked_calls,
                *args,
                **kwargs,
            )
        except KeyError:
            return origin_callable(*args, **kwargs)

    return side_effect


class MockedCalls(
    Generic[
        _TargetCls,
        _TargetMethodParams,
        _TargetMethodReturn,
    ]
):
    mocked_calls_registry: dict[
        _TargetClsMethodKey,
        dict[_CallKey, _CallLazyValue],
    ] = {}  # noqa: RUF012

    def __init__(self, mocker: MockerFixture) -> None:
        self.mocker = mocker

    def add_call(
        self,
        cls: _TargetCls,
        method: _TargetMethodName,
        args: _TargetMethodArgs,
        kwargs: _TargetMethodKwargs,
        should_call: _CallLazyValue,
    ) -> MagicMock:
        self.mocked_calls_registry.setdefault(
            (_TargetClsName(cls.__name__), method),
            {},
        )
        self.mocked_calls_registry[(_TargetClsName(cls.__name__), method)][
            create_call_key(
                inspect.signature(getattr(cls, method)),
                *args,
                **kwargs,
            )
        ] = should_call

        return self.mocker.patch.object(
            cls,
            method,
            autospec=True,
            # it is important to send the origin target to the
            # side_effect_factory in order the result side_effect stores
            # the original target.
            side_effect=side_effect_factory(
                origin_callable=getattr(cls, method),
                mocked_calls=self.mocked_calls_registry[
                    (_TargetClsName(cls.__name__), method)
                ],
            ),
        )


class When(
    Generic[
        _TargetCls,
        _TargetMethodParams,
        _TargetMethodReturn,
    ]
):
    """Patching utility focused on readability.

    Example:

    >>> class Klass1:
    >>>     def some_method(
    >>>         self,
    >>>         arg1: str,
    >>>         arg2: int,
    >>>         *,
    >>>         kwarg1: str,
    >>>         kwarg2: str,
    >>>     ) -> str:
    >>>         return "Not mocked"


    >>> def test_should_properly_patch_calls(when):
    >>>     p = when(Klass1, "some_method").called_with(
    >>>         "a",
    >>>         when.Markers.any,
    >>>         kwarg1="b",
    >>>         kwarg2=Markers.any,
    >>>     ).then_return("Mocked")
    >>>
    >>>     assert (
    >>>         Klass1().some_method(
    >>>             "a",
    >>>             1,
    >>>             kwarg1="b",
    >>>             kwarg2="c",
    >>>         )
    >>>         == "Mocked"
    >>>     )
    >>>     assert (
    >>>         Klass1().some_method(
    >>>             "not mocked param",
    >>>             1,
    >>>             kwarg1="b",
    >>>             kwarg2="c",
    >>>         )
    >>>         == "Not mocked"
    >>>     )
    >>>     p.assert_called()

    It is possible to use 'when' with class methods and standalone functions
    (in this case cls parameter will become the python module).

    You can patch multiple times the same object with different "called_with"
    parameters in a single test.

    You can also patch multiple targets (cls, method).

    Instead of ".then_return", there are ".then_call" and  ".then_raise"
    methods are avaialble

    """

    cls: _TargetCls
    method: _TargetMethodName

    args: _TargetMethodArgs
    kwargs: _TargetMethodKwargs

    markers = Markers

    def __init__(self, mocker: MockerFixture):
        self.mocker = mocker
        self.mocked_calls = MockedCalls[
            _TargetCls,
            _TargetMethodParams,
            _TargetMethodReturn,
        ](self.mocker)

    def __call__(
        self,
        cls: _TargetCls,
        method: _TargetMethodName,
    ) -> When:
        def already_mocked(mock: MockCacheItem) -> bool:
            return mock.patch.target is cls and mock.patch.attribute == method  # type: ignore

        def stop_patching(mock: MockCacheItem) -> MockCacheItem:
            mock.patch.stop()  # type: ignore
            return mock

        def remove_mock_item_from_cache(mock: MockCacheItem) -> None:
            self.mocker._mock_cache.cache.remove(mock)

        (
            Seq[MockCacheItem](self.mocker._mock_cache.cache)
            .filter(already_mocked)
            .map(stop_patching)
            .map(remove_mock_item_from_cache)
            .exhaust()
        )

        self.cls = cls
        self.method = method
        return self

    def called_with(
        self,
        *args,
        **kwargs,
    ) -> When:
        """Specify args and kwargs for which mock should be activated.

        Example:
        >>> when(Klass1, "some_class_method").called_with(
        >>>     "a",
        >>>     when.markers.any,
        >>>     kwarg1="b",
        >>>     kwarg2=when.markers.any,
        >>> ).then_return("Mocked")

        In this case the "Mocked" will be returned only if `some method`
        will be called with:
        "a" - as first argument,
        any second argument,
        kwarg1 = "b" (only),
        any kwarg2 kwarg

        """
        params = tuple(
            inspect.signature(
                getattr(
                    self.cls,
                    self.method,
                )
            ).parameters
        )
        is_instance_method = False if not params else params[0] == "self"
        # prepend Markers.any in case of a method (for self arg)
        self.args = (Markers.any, *args) if is_instance_method else args
        self.kwargs = kwargs
        return self

    def then_return(self, value: _TargetMethodReturn) -> MagicMock:
        """Return value in case the called_with specification will match the call."""
        return self.then_call(lambda: value)

    def then_call(self, callable_: _CallLazyValue) -> MagicMock:
        """Call the callable_ in case the called_with specification will match the call.

        Callable shouldn't contain any args.
        In case the callable needs args, kwargs - use functools.partial
        to convert the callable into arg-less one, i.e.

        Example:
        >>> (
        >>>    when(example_module, "some_foo")
        >>>    .called_with()
        >>>    .then_call(functools.partial(foo_patched, *foo_args, **foo_kwargs)
        >>> )

        """
        return self.mocked_calls.add_call(
            self.cls,
            self.method,
            self.args,
            self.kwargs,
            callable_,
        )

    def then_raise(self, exc: BaseException) -> MagicMock:
        """Raise exc in case the called_with specification will match the call."""

        def _raise_exc(exc: BaseException) -> _TargetMethodReturn:
            raise exc

        return self.then_call(lambda: _raise_exc(exc))


@pytest.fixture
def when(mocker: MockerFixture) -> When:
    """Patching utility focused on readability.

    Example:

    >>> class Klass1:
    >>>     def some_method(
    >>>         self,
    >>>         arg1: str,
    >>>         arg2: int,
    >>>         *,
    >>>         kwarg1: str,
    >>>         kwarg2: str,
    >>>     ) -> str:
    >>>         return "Not mocked"
    >>>
    >>>
    >>> def test_should_properly_patch_calls(when):
    >>>     when(Klass1, "some_method").called_with(
    >>>         "a",
    >>>         Markers.any,
    >>>         kwarg1="b",
    >>>         kwarg2=Markers.any,
    >>>     ).then_return("Mocked")
    >>>
    >>>     assert (
    >>>         Klass1().some_method(
    >>>             "a",
    >>>             1,
    >>>             kwarg1="b",
    >>>             kwarg2="c",
    >>>         )
    >>>         == "Mocked"
    >>>     )
    >>>
    >>>     assert (
    >>>         Klass1().some_method(
    >>>             "not mocked param",
    >>>             1,
    >>>             kwarg1="b",
    >>>             kwarg2="c",
    >>>         )
    >>>         == "Not mocked"
    >>>     )

    It is possible to use 'when' with class methods and standalone functions
    (in this case cls parameter will become a python module).

    You can patch multiple times the same object with different "called_with"
    parameters in a single test.

    You can also patch multiple targets (cls, method)

    """
    return When(mocker)
