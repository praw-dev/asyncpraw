"""Prepare pytest for unit tests."""
import pytest

from asyncpraw import Reddit


async def dummy_request(*args, **kwargs):
    pass


@pytest.fixture
async def reddit():
    """Return an instance of :class:`.Reddit` that doesn't make requests to Reddit."""
    async with Reddit(
        client_id="dummy", client_secret="dummy", user_agent="dummy"
    ) as reddit:
        # Unit tests should never issue requests
        reddit._core.request = dummy_request
        yield reddit
