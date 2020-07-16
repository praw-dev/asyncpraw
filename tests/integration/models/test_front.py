"""Test asyncpraw.models.front."""
from .. import IntegrationTest


class TestFront(IntegrationTest):
    async def test_best(self):
        with self.use_cassette():
            submissions = await self.async_list(self.reddit.front.best())
        assert len(submissions) == 100

    async def test_controversial(self):
        with self.use_cassette():
            submissions = await self.async_list(self.reddit.front.controversial())
        assert len(submissions) == 100

    async def test_gilded(self):
        with self.use_cassette():
            submissions = await self.async_list(self.reddit.front.gilded())
        assert len(submissions) == 100

    async def test_hot(self):
        with self.use_cassette():
            submissions = await self.async_list(self.reddit.front.hot())
        assert len(submissions) == 100

    async def test_new(self):
        with self.use_cassette():
            submissions = await self.async_list(self.reddit.front.new())
        assert len(submissions) == 100

    async def test_top(self):
        with self.use_cassette():
            submissions = await self.async_list(self.reddit.front.top())
        assert len(submissions) == 100
