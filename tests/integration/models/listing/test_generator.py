"""Test asyncpraw.models.listing.generator."""

from ... import IntegrationTest


class TestListingGenerator(IntegrationTest):
    async def test_exhaust_items(self, reddit):
        spez = await reddit.redditor("spez")
        submissions = await self.async_list(spez.top(limit=None))
        assert len(submissions) > 100

    async def test_exhaust_items_with_before(self, reddit):
        spez = await reddit.redditor("spez")
        submissions = await self.async_list(spez.top(limit=None, params={"before": "3cxedn"}))
        assert len(submissions) > 100

    async def test_no_items(self, reddit):
        spez = await reddit.redditor("spez")
        submissions = await self.async_list(spez.top(time_filter="hour"))
        assert len(submissions) == 0
