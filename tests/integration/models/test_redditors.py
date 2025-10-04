"""Test asyncpraw.models.redditors."""

from asyncpraw.models import Redditor, Subreddit

from .. import IntegrationTest


class TestRedditors(IntegrationTest):
    async def test_new(self, reddit):
        profiles = await self.async_list(reddit.redditors.new(limit=300))
        assert len(profiles) == 300
        assert all(isinstance(profile, Subreddit) for profile in profiles)
        assert all(str(profile).startswith("u_") for profile in profiles)

    async def test_partial_redditors(self, reddit):
        gen = reddit.redditors.partial_redditors(["t2_1w72", "t2_4x25quk"])
        user_data = await self.async_list(gen)

        fullnames = [user.fullname for user in user_data]
        assert fullnames == ["t2_1w72", "t2_4x25quk"]
        assert user_data[0].fullname == "t2_1w72"
        assert user_data[0].name == "spez"

    async def test_partial_redditors__not_found(self, reddit):
        gen = reddit.redditors.partial_redditors(["t2_invalid_abc", "t2_invalid_123"])
        assert await self.async_list(gen) == []

        gen = reddit.redditors.partial_redditors(["t2_invalid_abc" for _ in range(100)] + ["t2_4x25quk"])
        assert [user.fullname async for user in gen] == ["t2_4x25quk"]

    async def test_popular(self, reddit):
        profiles = await self.async_list(reddit.redditors.popular(limit=15))
        assert len(profiles) == 15
        assert all(isinstance(profile, Subreddit) for profile in profiles)
        assert all(str(profile).startswith("u_") for profile in profiles)

    async def test_search(self, reddit):
        found = False
        async for profile in reddit.redditors.search("praw"):
            assert isinstance(profile, Redditor)
            found = True
        assert found

    async def test_stream(self, reddit):
        generator = reddit.redditors.stream()
        for i in range(101):
            assert isinstance(await self.async_next(generator), Subreddit)
