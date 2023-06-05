def some_normal_function(
    arg1: str,
    arg2: int,
    *,
    kwarg1: str,
    kwarg2: str,
) -> str:
    return "Not mocked"


def some_foo_with_variadic_args_kwargs(
    *args,
    **kwargs,
) -> str:
    return "Not mocked"


def some_foo_without_args() -> str:
    return "Not mocked"
