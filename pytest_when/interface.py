import abc

from typing import Generic
from unittest.mock import MagicMock

from pytest_when.constant import (
    _CallLazyValue,
    _TargetCls,
    _TargetMethodName,
    _TargetMethodReturn,
)


class ThenResponse(abc.ABC, Generic[_TargetMethodReturn,]):
    @abc.abstractmethod
    def then_return(self, value: _TargetMethodReturn) -> MagicMock:
        """Return value in case the called_with specification will match the call."""
        raise NotImplementedError("Not implemented")

    @abc.abstractmethod
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
        raise NotImplementedError("Not implemented")

    @abc.abstractmethod
    def then_raise(self, exc: BaseException) -> MagicMock:
        """Raise exc in case the called_with specification will match the call."""
        raise NotImplementedError("Not implemented")


class WhenResponse(abc.ABC):

    @abc.abstractmethod
    def called_with(
        self,
        *args,
        **kwargs,
    ) -> ThenResponse:
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
        raise NotImplementedError("Not implemented")


class WhenInitial(abc.ABC, Generic[_TargetCls]):
    @abc.abstractmethod
    def __call__(
        self,
        cls: _TargetCls,
        method: _TargetMethodName,
    ) -> WhenResponse:
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
        raise NotImplementedError("Not implemented")
