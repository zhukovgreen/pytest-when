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


def test_should_work_with_foo_without_args(when):
    patched_foo = (
        when(example_module, "some_foo_without_args")
        .called_with()
        .then_return("Mocked")
    )
    assert example_module.some_foo_without_args() == "Mocked"
    patched_foo.assert_called()
