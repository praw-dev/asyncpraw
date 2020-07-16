"""Test asyncpraw.models.Trophy"""
from asynctest import mock

from .. import IntegrationTest


class TestTrophy(IntegrationTest):
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_equality(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            user = await self.reddit.user.me()
            trophies = await user.trophies()
            trophies2 = await user.trophies()
            assert trophies == trophies2
