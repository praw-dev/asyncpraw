"""Test asyncpraw.models.user."""
import asyncprawcore.exceptions
import pytest
from asynctest import mock

from asyncpraw.exceptions import RedditAPIException
from asyncpraw.models import Multireddit, Redditor, Submission, Subreddit

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
            assert not hasattr(me, "Async PRAW_is_cached")

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_moderator_subreddits(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            mod_subs = await self.async_list(
                self.reddit.user.moderator_subreddits(limit=None)
            )
            assert mod_subs
            assert all(isinstance(x, Subreddit) for x in mod_subs)

    async def test_multireddits(self):
        self.reddit.read_only = False
        with self.use_cassette():
            multireddits = await self.reddit.user.multireddits()
            assert isinstance(multireddits, list)
            assert multireddits
            assert all(isinstance(x, Multireddit) for x in multireddits)

    async def test_pin(self):
        self.reddit.read_only = False
        self.reddit.validate_on_submit = True
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            submission_list = []
            for i in range(1, 5):
                submission = await subreddit.submit(
                    title=f"Async PRAW Test {i}", selftext=f"Testing .pin method {i}"
                )
                submission_list.append(submission)
                await self.reddit.user.pin(submission)

            for i in range(5, 9):
                await subreddit.submit(
                    title=f"Async PRAW Test {i}", selftext=f"Testing .pin method {i}"
                )
            new_posts = await self.async_list(
                (await self.reddit.user.me()).new(limit=4)
            )
            new_posts.reverse()
            assert new_posts == submission_list

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_pin__comment(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            comment = await self.reddit.comment(id="hnxx8f2")
            await self.reddit.user.pin(comment)
            new_content = await self.async_next(
                (await self.reddit.user.me()).new(limit=1)
            )
            assert new_content != comment

    async def test_pin__deleted_submission(self):
        self.reddit.read_only = False
        with self.use_cassette():
            with pytest.raises(asyncprawcore.exceptions.BadRequest):
                await self.reddit.user.pin(Submission(self.reddit, "rmhl6m"))

    async def test_pin__empty_slot(self):
        self.reddit.read_only = False
        self.reddit.validate_on_submit = True
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            new_posts = await self.async_list(
                (await self.reddit.user.me()).new(limit=4)
            )
            new_posts.reverse()
            for i in range(2, 4):
                await self.reddit.user.pin(new_posts[i], state=False)
            submission = await subreddit.submit(
                title="Async PRAW Test 5", selftext="Testing .pin method 5"
            )
            await self.reddit.user.pin(submission, num=4)
            new_posts = await self.async_list(
                (await self.reddit.user.me()).new(limit=4)
            )
            new_posts.reverse()
            assert new_posts[-1] == submission

    async def test_pin__ignore_conflicts(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await self.reddit.user.pin(Submission(self.reddit, "rmi79w"))
            await self.reddit.user.pin(Submission(self.reddit, "rmi79w"))

    async def test_pin__invalid_num(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await self.reddit.user.pin(Submission(self.reddit, "rmi7hx"), num=7)
            submission = await self.async_next(
                (await self.reddit.user.me()).new(limit=1)
            )
            assert submission.id == "rmi7hx"

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_pin__num(self, _):
        self.reddit.read_only = False
        self.reddit.validate_on_submit = True
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            submission_list = []
            for i in range(1, 5):
                submission = await subreddit.submit(
                    title=f"Async PRAW Test {i}", selftext=f"Testing .pin method {i}"
                )
                submission_list.append(submission)
            submission_list.reverse()
            for num, submission in enumerate(submission_list, 1):
                await self.reddit.user.pin(submission, num=num)

            new_posts = await self.async_list(
                (await self.reddit.user.me()).new(limit=4)
            )
            assert new_posts == submission_list

    async def test_pin__remove(self):
        self.reddit.read_only = False
        with self.use_cassette():
            unpinned_posts = set()
            async for post in (await self.reddit.user.me()).new(limit=4):
                await self.reddit.user.pin(post, state=False)
                unpinned_posts.add(post.title)
            new_posts = set(
                [
                    submission.title
                    async for submission in (await self.reddit.user.me()).new(limit=4)
                ]
            )
            assert unpinned_posts != new_posts

    async def test_pin__remove_num(self):
        self.reddit.read_only = False
        self.reddit.validate_on_submit = True
        with self.use_cassette():
            await self.reddit.user.pin(
                Submission(self.reddit, "rmi7ab"), num=1, state=False
            )
            submission = await self.async_next(
                (await self.reddit.user.me()).new(limit=1)
            )
            assert submission.id != "rmi7ab"

    async def test_pin__removed_submission(self):
        self.reddit.read_only = False
        with self.use_cassette():
            with pytest.raises(asyncprawcore.exceptions.BadRequest):
                await self.reddit.user.pin(Submission(self.reddit, "rmi7ab"))

    async def test_pin__replace_slot(self):
        self.reddit.read_only = False
        self.reddit.validate_on_submit = True
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            submission = await subreddit.submit(
                title="Async PRAW Test replace slot 1", selftext="Testing .pin method 1"
            )
            await self.reddit.user.pin(submission, num=1)
            new_posts = await self.async_list(
                (await self.reddit.user.me()).new(limit=4)
            )
            new_posts.reverse()
            assert new_posts[-1] == submission

    async def test_subreddits(self):
        self.reddit.read_only = False
        with self.use_cassette():
            count = 0
            async for subreddit in self.reddit.user.subreddits():
                assert isinstance(subreddit, Subreddit)
                count += 1
            assert count > 0
