"""Test asyncpraw.models.util."""

from collections import namedtuple

import pytest

from asyncpraw.models.util import (
    BoundedSet,
    ExponentialCounter,
    permissions_string,
    stream_generator,
)

from .. import UnitTest


class TestBoundedSet(UnitTest):
    def test_bound(self):
        bset = BoundedSet(max_items=10)
        [bset.add(i) for i in range(11)]
        assert len(bset._set) == 10
        assert 0 not in bset

    def test_contains(self):
        bset = BoundedSet(max_items=10)
        bset.add(1)
        assert 1 in bset

    def test_lru_add(self):
        bset = BoundedSet(max_items=10)
        [bset.add(i) for i in range(10)]
        bset.add(0)
        bset.add(10)
        assert 0 in bset
        assert 1 not in bset

    def test_lru_contains(self):
        bset = BoundedSet(max_items=10)
        [bset.add(i) for i in range(10)]
        assert 0 in bset
        bset.add(10)
        assert 0 in bset
        assert 1 not in bset


class TestExponentialCounter(UnitTest):
    MAX_DELTA = 1.0 / 32

    def test_exponential_counter__counter(self):
        def assert_range(number, exponent):
            assert number >= 2**exponent * (1 - self.MAX_DELTA)
            assert number <= 2**exponent * (1 + self.MAX_DELTA)

        counter = ExponentialCounter(1024)
        prev_value = counter.counter()
        assert_range(prev_value, 0)

        for i in range(9):
            value = counter.counter()
            assert_range(value, 1 + i)
            assert value > prev_value
            prev_value = value

    def test_exponential_counter__max_value(self):
        counter = ExponentialCounter(5)
        max_value = 5 * (1 + self.MAX_DELTA)
        for _ in range(100):
            value = counter.counter()
            assert value <= max_value

    def test_exponential_counter__reset(self):
        counter = ExponentialCounter(1024)
        for _ in range(100):
            value = counter.counter()
            assert value >= 1 - self.MAX_DELTA
            assert value <= 1 + self.MAX_DELTA
            counter.reset()


class TestPermissionsString(UnitTest):
    PERMISSIONS = {"a", "b", "c"}

    def test_permissions_string__all_explicit(self):
        assert permissions_string(known_permissions=self.PERMISSIONS, permissions=["b", "a", "c"]) == "-all,+b,+a,+c"

    def test_permissions_string__empty_list(self):
        assert permissions_string(known_permissions=set(), permissions=[]) == "-all"
        assert permissions_string(known_permissions=self.PERMISSIONS, permissions=[]) == "-all,-a,-b,-c"

    def test_permissions_string__none(self):
        assert permissions_string(known_permissions=set(), permissions=None) == "+all"
        assert permissions_string(known_permissions=self.PERMISSIONS, permissions=None) == "+all"

    def test_permissions_string__with_additional_permissions(self):
        assert permissions_string(known_permissions=set(), permissions=["d"]) == "-all,+d"
        assert permissions_string(known_permissions=self.PERMISSIONS, permissions=["d"]) == "-all,-a,-b,-c,+d"


class TestStream(UnitTest):
    async def test_comments__with_continue_after_id(
        self,
    ):
        Thing = namedtuple("Thing", ["fullname"])
        initial_things = [Thing(n) for n in reversed(range(100))]
        counter = 99

        async def generate(limit, params=None, **kwargs):
            nonlocal counter
            counter += 1
            sliced_things = initial_things
            if params:
                sliced_things = initial_things[
                    : next(i for i, thing in enumerate(initial_things) if thing.fullname == params["before"])
                ]
            if counter % 2 == 0:
                things = sliced_things
            else:
                things = [Thing(counter)] + sliced_things[:-1]
            for thing in things:
                yield thing

        stream = stream_generator(generate, continue_after_id=49)
        expected_fullname = 50
        for _ in range(50):
            thing = await self.async_next(stream)
            assert thing.fullname == expected_fullname, thing
            expected_fullname += 1

    async def test_stream(self):
        Thing = namedtuple("Thing", ["fullname"])
        initial_things = [Thing(n) for n in reversed(range(100))]
        counter = 99

        async def generate(limit, **kwargs):
            nonlocal counter
            counter += 1
            if counter % 2 == 0:
                things = initial_things
            else:
                things = [Thing(counter)] + initial_things[:-1]
            for thing in things:
                yield thing

        stream = stream_generator(generate)
        seen = set()
        async for thing in stream:
            assert thing not in seen
            seen.add(thing)
            counter += 1
            if counter == 400:
                break

    async def test_stream__exception_handler(self, monkeypatch):
        async def _sleep(*_):
            pass

        monkeypatch.setattr("asyncpraw.models.util.asyncio.sleep", _sleep)
        Thing = namedtuple("Thing", ["fullname"])
        handled = []
        responses = [RuntimeError("boom"), [Thing(1)], [Thing(2)]]

        async def generate(limit, **kwargs):
            response = responses.pop(0)
            if isinstance(response, Exception):
                raise response
            for item in response:
                yield item

        stream = stream_generator(generate, exception_handler=handled.append)
        # The first fetch raises and is handled; the stream then resumes and keeps
        # yielding new items on subsequent iterations.
        assert (await self.async_next(stream)).fullname == 1
        assert (await self.async_next(stream)).fullname == 2
        assert len(handled) == 1
        assert str(handled[0]) == "boom"

    async def test_stream__exception_handler__reraise(self):
        async def generate(limit, **kwargs):
            raise RuntimeError("boom")
            yield  # unreachable; makes ``generate`` an async generator

        def handler(exception):
            raise exception

        stream = stream_generator(generate, exception_handler=handler)
        with pytest.raises(RuntimeError):
            await self.async_next(stream)

    async def test_stream__exception_propagates_without_handler(self):
        async def generate(limit, **kwargs):
            raise RuntimeError("boom")
            yield  # unreachable; makes ``generate`` an async generator

        stream = stream_generator(generate)
        with pytest.raises(RuntimeError):
            await self.async_next(stream)
