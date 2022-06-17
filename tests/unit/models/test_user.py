import pytest

from asyncpraw import Reddit
from asyncpraw.exceptions import ReadOnlyException
from asyncpraw.models import User

from .. import UnitTest


class TestUser(UnitTest):
    async def test_me__in_read_only_mode(self):
        async with Reddit(
            client_id="dummy",
            client_secret="dummy",
            praw8_raise_exception_on_me=True,
            user_agent="dummy",
        ) as reddit:
            assert reddit.read_only
            user = User(reddit)
            with pytest.raises(ReadOnlyException):
                await user.me()

    async def test_me__in_read_only_mode__deprecated(self, reddit):
        assert reddit.read_only
        assert await User(reddit).me() is None
