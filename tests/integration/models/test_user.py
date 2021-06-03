"""Test asyncpraw.models.user."""
import pytest
from asynctest import mock

from asyncpraw.exceptions import RedditAPIException
from asyncpraw.models import Multireddit, Redditor, Subreddit

from .. import IntegrationTest


class TestUser(IntegrationTest):
    async def test_blocked(self):
        self.reddit.read_only = False
        with self.use_cassette():
            blocked = await self.reddit.user.blocked()
        assert len(blocked) > 0
        assert all(isinstance(user, Redditor) for user in blocked)

    async def test_blocked_fullname(self):
        self.reddit.read_only = False
        with self.use_cassette():
            blocked = next(iter(await self.reddit.user.blocked()))
            assert blocked.fullname.startswith("t2_")
            assert not blocked.fullname.startswith("t2_t2")

    async def test_contributor_subreddits(self):
        self.reddit.read_only = False
        with self.use_cassette():
            count = 0
            async for subreddit in self.reddit.user.contributor_subreddits():
                assert isinstance(subreddit, Subreddit)
                count += 1
            assert count > 0

    async def test_friends(self):
        self.reddit.read_only = False
        with self.use_cassette():
            friends = await self.reddit.user.friends()
        assert len(friends) > 0
        assert all(isinstance(friend, Redditor) for friend in friends)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_friend_exist(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            friend = await self.reddit.user.friends(user=await self.reddit.user.me())
            assert isinstance(friend, Redditor)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_friend_not_exist(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            with pytest.raises(RedditAPIException):
                await self.reddit.user.friends(user="fake__user_user_user")

    async def test_karma(self):
        self.reddit.read_only = False
        with self.use_cassette():
            karma = await self.reddit.user.karma()
        assert isinstance(karma, dict)
        for subreddit in karma:
            assert isinstance(subreddit, Subreddit)
            keys = sorted(karma[subreddit].keys())
            assert ["comment_karma", "link_karma"] == keys

    async def test_me(self):
        self.reddit.read_only = False
        with self.use_cassette():
            me = await self.reddit.user.me()
        assert isinstance(me, Redditor)
        me.praw_is_cached = True
        me = await self.reddit.user.me()
        assert me.praw_is_cached

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_me__bypass_cache(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            me = await self.reddit.user.me()
            me.praw_is_cached = True
            me = await self.reddit.user.me(use_cache=False)
            assert not hasattr(me, "praw_is_cached")

    async def test_multireddits(self):
        self.reddit.read_only = False
        with self.use_cassette():
            multireddits = await self.reddit.user.multireddits()
            assert isinstance(multireddits, list)
            assert multireddits
            assert all(isinstance(x, Multireddit) for x in multireddits)

    async def test_subreddits(self):
        self.reddit.read_only = False
        with self.use_cassette():
            count = 0
            async for subreddit in self.reddit.user.subreddits():
                assert isinstance(subreddit, Subreddit)
                count += 1
            assert count > 0
