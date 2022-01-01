"""This file should be updated as files/classes/functions are deprecated."""
import inspect
from contextlib import contextmanager
from enum import IntFlag, auto

import pytest

from asyncpraw.util import _deprecate_args

from .. import UnitTest

keyword_only = {
    "args": [
        [("arg2", "arg1", "arg3", "arg0"), dict()],
        ("arg0", "arg1", "arg2", "arg3"),
    ],
    "kwargs": [
        [(), dict(arg2="arg2", arg1="arg1", arg3="arg3", arg0="arg0")],
        ("arg0", "arg1", "arg2", "arg3"),
    ],
    "mix": [
        [("arg2",), dict(arg1="arg1")],
        (None, "arg1", "arg2", None),
    ],
    "one_kwarg": [
        [(), dict(arg0="arg0")],
        ("arg0", None, None, None),
    ],
    "one_arg": [
        [("arg2",), dict()],
        (None, None, "arg2", None),
    ],
}
with_positional = {
    "args": [
        [("arg0", "arg2", "arg1", "arg3"), dict()],
        ("arg0", "arg1", "arg2", "arg3"),
    ],
    "kwargs": [
        [("arg0",), dict(arg2="arg2", arg1="arg1", arg3="arg3")],
        ("arg0", "arg1", "arg2", "arg3"),
    ],
    "mix": [
        [("arg0", "arg2"), dict(arg1="arg1", arg3=None)],
        ("arg0", "arg1", "arg2", None),
    ],
    "one_kwarg": [
        [(), dict(arg0="arg0")],
        ("arg0", None, None, None),
    ],
    "one_arg": [
        [("arg0",), dict()],
        ("arg0", None, None, None),
    ],
}


class AsyncType(IntFlag):
    ASYNC = auto()
    ASYNC_GENERATOR = auto()
    SYNC = auto()

    def __str__(self):
        return f"__{self.name.lower()}"

    def __repr__(self):
        return self.name.lower()


def _gen_warning(func, args):
    arg_list = list(map(repr, args))
    arg_count = len(args)
    plural = arg_count > 1
    arg_string = (
        " and ".join(arg_list)
        if arg_count < 3
        else f"{', '.join(arg_list[:-1])}, and {arg_list[-1]}"
    )
    arg_string += f" as {'' if plural else 'a '}"
    arg_string += f"keyword argument{'s' if plural else ''}"
    return (
        f"Positional arguments for {func.__qualname__!r} will no longer be supported in"
        f" Async PRAW 8.\nCall this function with {arg_string}."
    )


@contextmanager
def _check_warning(func, args):
    if args:
        with pytest.warns(DeprecationWarning, match=_gen_warning(func, args)):
            yield
    else:
        yield


def _prepare_args(arguments, func):
    args, kwargs = arguments
    parameters = inspect.signature(func).parameters.values()
    check_args = args[
        len(
            [
                param
                for param in parameters
                if param.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
            ]
        ) :
    ]
    return args, check_args, kwargs


@_deprecate_args("arg2", "arg1", "arg3", "arg0")
def arg_test_global(*, arg0=None, arg1=None, arg2=None, arg3=None):
    return arg0, arg1, arg2, arg3


@_deprecate_args("arg2", "arg1", "arg3", "arg0")
async def arg_test_global__async(*, arg0=None, arg1=None, arg2=None, arg3=None):
    return arg0, arg1, arg2, arg3


@_deprecate_args("arg2", "arg1", "arg3", "arg0")
async def arg_test_global__async_generator(
    *, arg0=None, arg1=None, arg2=None, arg3=None
):
    yield arg0
    yield arg1
    yield arg2
    yield arg3


@_deprecate_args("arg0", "arg2", "arg1", "arg3")
def arg_test_global_with_positional(arg0, *, arg1=None, arg2=None, arg3=None):
    return arg0, arg1, arg2, arg3


@_deprecate_args("arg0", "arg2", "arg1", "arg3")
async def arg_test_global_with_positional__async(
    arg0, *, arg1=None, arg2=None, arg3=None
):
    return arg0, arg1, arg2, arg3


@_deprecate_args("arg0", "arg2", "arg1", "arg3")
async def arg_test_global_with_positional__async_generator(
    arg0, *, arg1=None, arg2=None, arg3=None
):
    yield arg0
    yield arg1
    yield arg2
    yield arg3


class ArgTest:
    @_deprecate_args("arg2", "arg1", "arg3", "arg0")
    def arg_test(self, *, arg0=None, arg1=None, arg2=None, arg3=None):
        return arg0, arg1, arg2, arg3

    @_deprecate_args("arg2", "arg1", "arg3", "arg0")
    async def arg_test__async(self, *, arg0=None, arg1=None, arg2=None, arg3=None):
        return arg0, arg1, arg2, arg3

    @_deprecate_args("arg2", "arg1", "arg3", "arg0")
    async def arg_test__async_generator(
        self, *, arg0=None, arg1=None, arg2=None, arg3=None
    ):
        yield arg0
        yield arg1
        yield arg2
        yield arg3

    @_deprecate_args("arg0", "arg2", "arg1", "arg3")
    def arg_test_with_positional(self, arg0, *, arg1=None, arg2=None, arg3=None):
        return arg0, arg1, arg2, arg3

    @_deprecate_args("arg0", "arg2", "arg1", "arg3")
    async def arg_test_with_positional__async(
        self, arg0, *, arg1=None, arg2=None, arg3=None
    ):
        return arg0, arg1, arg2, arg3

    @_deprecate_args("arg0", "arg2", "arg1", "arg3")
    async def arg_test_with_positional__async_generator(
        self, arg0, *, arg1=None, arg2=None, arg3=None
    ):
        yield arg0
        yield arg1
        yield arg2
        yield arg3


def pytest_generate_tests(metafunc):
    # called once per each test function
    if "positional" in metafunc.function.__name__:
        test_cases = metafunc.cls.params["positional"]
    else:
        test_cases = metafunc.cls.params["keyword"]
    name = "_".join(metafunc.function.__name__.split("_")[1:])
    cases = []
    ids = []
    for async_type in list(AsyncType):
        function_name = name
        if async_type in AsyncType.ASYNC | AsyncType.ASYNC_GENERATOR:
            function_name += str(async_type)
        for test_case, parameters in test_cases.items():
            cases.append([function_name, *parameters, async_type])
            ids.append(",".join([repr(async_type), test_case]))
    signature = inspect.signature(metafunc.function)
    args = [arg.name for arg in signature.parameters.values() if arg.name != "self"]
    metafunc.parametrize(argnames=args, argvalues=cases, ids=ids)


@pytest.mark.filterwarnings("error", category=DeprecationWarning)
class TestDeprecateArgs(UnitTest):
    def setup(self):
        self.arg_test = ArgTest()

    params = {
        "keyword": keyword_only,
        "positional": with_positional,
    }

    async def _execute_test(self, func_name, arguments, expected_results, async_type):
        if "global" in func_name:
            func = globals()[func_name]
        else:
            func = getattr(self.arg_test, func_name)
        args, check_args, kwargs = _prepare_args(arguments, func)
        with _check_warning(func, check_args):
            if async_type is AsyncType.ASYNC:
                results = await func(*args, **kwargs)
            elif async_type is AsyncType.ASYNC_GENERATOR:
                results = tuple([item async for item in func(*args, **kwargs)])
            else:
                results = func(*args, **kwargs)
        assert expected_results == results

    async def test_arg_test_global(
        self, func_name, arguments, expected_result, async_type
    ):
        await self._execute_test(func_name, arguments, expected_result, async_type)

    async def test_arg_test_global_with_positional(
        self, func_name, arguments, expected_result, async_type
    ):
        await self._execute_test(func_name, arguments, expected_result, async_type)

    async def test_arg_test(self, func_name, arguments, expected_result, async_type):
        await self._execute_test(func_name, arguments, expected_result, async_type)

    async def test_arg_test_with_positional(
        self, func_name, arguments, expected_result, async_type
    ):
        await self._execute_test(func_name, arguments, expected_result, async_type)
