"""Test asyncpraw.models.Trophy"""

from .. import IntegrationTest


class TestTrophy(IntegrationTest):
    async def test_equality(self, reddit):
        reddit.read_only = False
        user = await reddit.user.me()
        trophies = await user.trophies()
        trophies2 = await user.trophies()
        assert trophies == trophies2
