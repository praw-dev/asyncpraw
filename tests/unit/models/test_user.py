from asyncpraw.models import User

from .. import UnitTest


class TestUser(UnitTest):
    async def test_me__in_read_only_mode(self):
        assert self.reddit.read_only
        user = User(self.reddit)
        assert await user.me() is None
