"""Async PRAW Test Suite."""
import sys

if sys.version_info < (3, 8):
    from asynctest import TestCase

    class BaseTest(TestCase):
        """Base class for Async PRAW tests."""

else:

    class BaseTest:
        """Base class for Async PRAW tests."""


class HelperMethodMixin:
    @staticmethod
    async def async_list(async_generator):
        """Return a list from an async iterator."""
        return [item async for item in async_generator]

    @staticmethod
    async def async_next(async_generator):
        """Return the next item from an async iterator."""
        return await async_generator.__anext__()
