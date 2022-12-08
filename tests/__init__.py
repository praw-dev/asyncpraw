"""Async PRAW Test Suite."""


class HelperMethodMixin:
    @staticmethod
    async def async_list(async_generator):
        """Return a list from an async iterator."""
        return [item async for item in async_generator]

    @staticmethod
    async def async_next(async_generator):
        """Return the next item from an async iterator."""
        return await async_generator.__anext__()
