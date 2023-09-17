import enum
import inspect

from collections.abc import Mapping
from typing import Any, Callable, Dict, Generic, Protocol, Tuple, TypeVar
from unittest.mock import MagicMock

import pytest

from pytest_mock import MockerFixture
from typing_extensions import ParamSpec


class HasNameDunder(Protocol):
    __name__: str  # noqa: A003


_TargetClsType = TypeVar("_TargetClsType", bound=HasNameDunder)
_TargetMethodParams = ParamSpec("_TargetMethodParams")
_TargetMethodReturn = TypeVar("_TargetMethodReturn")
_TargetMethodKey = Tuple[str, str]

_TargetMethodArgs = Tuple[Any, ...]
_TargetMethodKwargs = Dict[str, Any]

_CallKeyParamDef = Tuple[str, Any]
_CallKey = Tuple[_CallKeyParamDef, ...]


class Markers(enum.Enum):
    """Markers for defining When.called_with arguments.

    Markers.any - means the argument could be anything
    """

    any: str = "any"  # noqa: A003


def make_hashable(
    container: Tuple[Tuple[str, Any], ...]
) -> Tuple[Tuple[str, Any], ...]:
    def unwrap_mapping(value):
        if isinstance(value, Mapping):
            return tuple((k, unwrap_mapping(v)) for k, v in value.items())
        if isinstance(value, (list, set)):
            return tuple(unwrap_mapping(v) for v in value)
        assert hash(
            value
        ), f"Not hashable function arg {value!r} is not supported currently."
        return value

    return tuple((arg, unwrap_mapping(value)) for arg, value in container)


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

    return make_hashable(tuple(call.arguments.items()))


def get_mocked_call_result(
    original_callable_sig: inspect.Signature,
    mocked_calls: Dict[
        _CallKey,
        _TargetMethodReturn,
    ],
    *args: _TargetMethodArgs,
    **kwargs: _TargetMethodKwargs,
) -> _TargetMethodReturn:
    call_key = create_call_key(
        original_callable_sig,
        *args,
        **kwargs,
    )

    def params_are_compatible(
        param_in_mocked_calls: _CallKeyParamDef,
        param_in_call: _CallKeyParamDef,
    ) -> bool:
        assert param_in_mocked_calls[0] == param_in_call[0]
        return (
            param_in_mocked_calls[1] is Markers.any
            or param_in_mocked_calls[1] == param_in_call[1]
        )

    def call_matched_call_key(mocked_call_key: _CallKey) -> bool:
        return all(
            params_are_compatible(param_1, param_2)
            for param_1, param_2 in zip(mocked_call_key, call_key)
        )

    for call in filter(call_matched_call_key, mocked_calls):
        return mocked_calls[call]
    raise KeyError(f"Call {call_key} is not in mocked_calls {mocked_calls}")


def side_effect_factory(
    origin_callable: Callable[_TargetMethodParams, _TargetMethodReturn],
    mocked_calls: Dict[_CallKey, _TargetMethodReturn],
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
        _TargetClsType,
        _TargetMethodParams,
        _TargetMethodReturn,
    ]
):
    mocked_calls_registry: Dict[
        _TargetMethodKey,
        Dict[_CallKey, _TargetMethodReturn],
    ] = {}  # noqa: RUF012

    def __init__(self, mocker: MockerFixture) -> None:
        self.mocker = mocker

    def add_call(
        self,
        cls: _TargetClsType,
        method: str,
        args: _TargetMethodArgs,
        kwargs: _TargetMethodKwargs,
        should_return: _TargetMethodReturn,
    ) -> MagicMock:
        self.mocked_calls_registry.setdefault(
            (cls.__name__, method),
            {},
        )
        self.mocked_calls_registry[(cls.__name__, method)][
            create_call_key(
                inspect.signature(getattr(cls, method)),
                *args,
                **kwargs,
            )
        ] = should_return

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
                    (cls.__name__, method)
                ],
            ),
        )


class When(
    Generic[
        _TargetClsType,
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

    You can also patch multiple targets (cls, method)
    """

    cls: _TargetClsType
    method: str

    args: _TargetMethodArgs
    kwargs: _TargetMethodKwargs

    markers = Markers

    def __init__(self, mocker: MockerFixture):
        self.mocker = mocker
        self.mocked_calls = MockedCalls[
            _TargetClsType,
            _TargetMethodParams,
            _TargetMethodReturn,
        ](self.mocker)

    def __call__(
        self,
        cls: _TargetClsType,
        method: str,
    ) -> "When":
        def matched_current_obj(patch_and_function) -> bool:
            patch, _ = patch_and_function
            return patch.target is cls and patch.attribute == method

        # if current object was already patched, we have to re-patch it again
        for mocked_obj, func in filter(
            matched_current_obj,
            self.mocker._patches_and_mocks,  # noqa: SLF001
        ):
            mocked_obj.stop()
            self.mocker._patches_and_mocks.remove(  # noqa: SLF001
                (mocked_obj, func)
            )

        self.cls = cls
        self.method = method
        return self

    def called_with(
        self,
        *args,
        **kwargs,
    ) -> "When":
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
        return self.mocked_calls.add_call(
            self.cls,
            self.method,
            self.args,
            self.kwargs,
            value,
        )


@pytest.fixture()
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


    >>> def test_should_properly_patch_calls(when):
    >>>     when(Klass1, "some_method").called_with(
    >>>         "a",
    >>>         Markers.any,
    >>>         kwarg1="b",
    >>>         kwarg2=Markers.any,
    >>>     ).then_return("Mocked")

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

    It is possible to use 'when' with class methods and standalone functions
    (in this case cls parameter will become a python module).

    You can patch multiple times the same object with different "called_with"
    parameters in a single test.

    You can also patch multiple targets (cls, method)
    """
    return When(mocker)
