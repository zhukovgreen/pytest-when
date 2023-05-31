def some_normal_function(
    arg1: str,
    arg2: int,
    *,
    kwarg1: str,
    kwarg2: str,
) -> str:
    return "Not mocked"


def arg_kwarg_function(*args, **kwargs):
    return "Not mocked"
