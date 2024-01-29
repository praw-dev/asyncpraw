"""Test asyncpraw.models.front."""

from .. import IntegrationTest


class TestFront(IntegrationTest):
    async def test_best(self, reddit):
        submissions = await self.async_list(reddit.front.best())
        assert len(submissions) == 100

    async def test_controversial(self, reddit):
        submissions = await self.async_list(reddit.front.controversial())
        assert len(submissions) == 100

    async def test_gilded(self, reddit):
        submissions = await self.async_list(reddit.front.gilded())
        assert len(submissions) == 100

    async def test_hot(self, reddit):
        submissions = await self.async_list(reddit.front.hot())
        assert len(submissions) == 100

    async def test_new(self, reddit):
        submissions = await self.async_list(reddit.front.new())
        assert len(submissions) == 100

    async def test_top(self, reddit):
        submissions = await self.async_list(reddit.front.top())
        assert len(submissions) == 100
