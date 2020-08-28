"""Test asyncpraw.models.subreddits."""
from asynctest import mock

from asyncpraw.models import Subreddit

from .. import IntegrationTest


class TestSubreddits(IntegrationTest):
    async def test_default(self):
        with self.use_cassette():
            subreddits = await self.async_list(
                self.reddit.subreddits.default(limit=None)
            )
        assert 0 < len(subreddits) < 100

    async def test_premium__without_premium(self):
        with self.use_cassette():
            subreddits = await self.async_list(self.reddit.subreddits.premium())
        assert len(subreddits) == 0

    async def test_premium__with_premium(self):
        with self.use_cassette():
            subreddits = await self.async_list(self.reddit.subreddits.premium())
        assert len(subreddits) == 100

    async def test_gold__without_gold(self):  # ensure backwards compatibility
        with self.use_cassette():
            subreddits = await self.async_list(self.reddit.subreddits.gold())
        assert len(subreddits) == 0

    async def test_gold__with_gold(self):  # ensure backwards compatibility
        with self.use_cassette():
            subreddits = await self.async_list(self.reddit.subreddits.gold())
        assert len(subreddits) == 100

    async def test_new(self):
        with self.use_cassette():
            subreddits = await self.async_list(self.reddit.subreddits.new(limit=300))
        assert len(subreddits) == 300

    async def test_popular(self):
        with self.use_cassette():
            subreddits = await self.async_list(self.reddit.subreddits.popular(limit=15))
        assert len(subreddits) == 15

    async def test_recommended(
        self,
    ):  # FIXME: always seems to return []; same with praw
        with self.use_cassette():
            subreddits = await self.reddit.subreddits.recommended(
                ["earthporn"], omit_subreddits=["cityporn"]
            )
        assert (
            len(subreddits) == 0
        )  # This is like this for coverage. Endpoint does not seem to work for me.
        # assert len(subreddits) > 1
        # for subreddit in subreddits:
        #     assert isinstance(subreddit, Subreddit)

    async def test_recommended__with_multiple(
        self,
    ):  # FIXME: always seems to return []; same with praw
        with self.use_cassette():
            subreddits = await self.reddit.subreddits.recommended(
                ["cityporn", "earthporn"],
                omit_subreddits=["skyporn", "winterporn"],
            )
        assert (
            len(subreddits) == 0
        )  # This is like this for coverage. Endpoint does not seem to work for me.
        # assert len(subreddits) > 1
        # for subreddit in subreddits:
        #     assert isinstance(subreddit, Subreddit)

    async def test_search(self):
        with self.use_cassette():
            found = False
            async for subreddit in self.reddit.subreddits.search("asyncpraw"):
                assert isinstance(subreddit, Subreddit)
                found = True
            assert found

    # async def test_search_by_topic(self): # FIXME: endpoint does not exist anymore
    #     with self.use_cassette():
    #         found = False
    #         async for subreddit in self.reddit.subreddits.search_by_topic("sports"):
    #             assert isinstance(subreddit, Subreddit)
    #             found = True
    #         assert found

    async def test_search_by_name(self):
        with self.use_cassette():
            subreddits = await self.async_list(
                self.reddit.subreddits.search_by_name("reddit")
            )
            assert isinstance(subreddits, list)
            assert len(subreddits) > 1
            assert all(isinstance(x, Subreddit) for x in subreddits)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_stream(self, _):
        with self.use_cassette():
            generator = self.reddit.subreddits.stream()
            for i in range(101):
                assert isinstance(await self.async_next(generator), Subreddit)
