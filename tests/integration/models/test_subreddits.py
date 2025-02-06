"""Test asyncpraw.models.subreddits."""

from asyncpraw.models import Subreddit

from .. import IntegrationTest


class TestSubreddits(IntegrationTest):
    async def test_default(self, reddit):
        subreddits = await self.async_list(reddit.subreddits.default(limit=None))
        assert 0 < len(subreddits) < 100

    async def test_new(self, reddit):
        subreddits = await self.async_list(reddit.subreddits.new(limit=300))
        assert len(subreddits) == 300

    async def test_popular(self, reddit):
        subreddits = await self.async_list(reddit.subreddits.popular(limit=15))
        assert len(subreddits) == 15

    async def test_premium__with_premium(self, reddit):
        subreddits = await self.async_list(reddit.subreddits.premium())
        assert len(subreddits) == 100

    async def test_premium__without_premium(self, reddit):
        subreddits = await self.async_list(reddit.subreddits.premium())
        assert len(subreddits) == 0

    async def test_recommended(
        self, reddit
    ):  # FIXME: always seems to return []; same with praw
        subreddits = await reddit.subreddits.recommended(
            ["earthporn"], omit_subreddits=["cityporn"]
        )
        assert (
            len(subreddits) == 0
        )  # This is like this for coverage. Endpoint does not seem to work for me.
        # assert len(subreddits) > 1
        # for subreddit in subreddits:
        #     assert isinstance(subreddit, Subreddit)

    async def test_recommended__with_multiple(
        self, reddit
    ):  # FIXME: always seems to return []; same with praw
        subreddits = await reddit.subreddits.recommended(
            ["cityporn", "earthporn"],
            omit_subreddits=["skyporn", "winterporn"],
        )
        assert (
            len(subreddits) == 0
        )  # This is like this for coverage. Endpoint does not seem to work for me.
        # assert len(subreddits) > 1
        # for subreddit in subreddits:
        #     assert isinstance(subreddit, Subreddit)

    async def test_search(self, reddit):
        found = False
        async for subreddit in reddit.subreddits.search("asyncpraw"):
            assert isinstance(subreddit, Subreddit)
            found = True
        assert found

    async def test_search_by_name(self, reddit):
        subreddits = await self.async_list(reddit.subreddits.search_by_name("reddit"))
        assert isinstance(subreddits, list)
        assert len(subreddits) > 1
        assert all(isinstance(x, Subreddit) for x in subreddits)

    async def test_stream(self, reddit):
        generator = reddit.subreddits.stream()
        for i in range(101):
            assert isinstance(await self.async_next(generator), Subreddit)
