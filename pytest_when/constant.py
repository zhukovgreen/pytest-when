# ruff: noqa: PYI047, PYI018

from __future__ import annotations

from collections.abc import Callable
from typing import Any, NewType, Protocol, TypeAlias, TypeVar

from typing_extensions import ParamSpec


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
