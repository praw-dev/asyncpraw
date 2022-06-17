import pytest

from asyncpraw import Reddit


@pytest.fixture
async def reddit():
    async with Reddit(
        client_id="dummy", client_secret="dummy", user_agent="dummy"
    ) as reddit:
        # Unit tests should never issue requests
        yield reddit
