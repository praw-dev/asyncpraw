"""Test asyncpraw.models.redditor."""
import pytest
from asyncprawcore import Forbidden
from asynctest import mock

from asyncpraw.exceptions import RedditAPIException
from asyncpraw.models import Comment, Redditor, Submission

from ... import IntegrationTest


class TestRedditor(IntegrationTest):
    FRIEND = "PyAPITestUser3"
    FRIEND_FULLNAME = "t2_6c1xj"

    async def test_block(self):
        self.reddit.read_only = False
        with self.use_cassette():
            redditor = await self.reddit.redditor(self.FRIEND, fetch=True)
            await redditor.block()

    async def test_friend(self):
        self.reddit.read_only = False
        with self.use_cassette():
            redditor = await self.reddit.redditor(self.FRIEND.lower(), fetch=True)
            await redditor.friend()

    async def test_friend__with_note__no_gold(self):
        self.reddit.read_only = False
        with self.use_cassette():
            with pytest.raises(RedditAPIException) as excinfo:
                redditor = await self.reddit.redditor(self.FRIEND.lower(), fetch=True)
                await redditor.friend(note="asyncpraw")
            assert "GOLD_REQUIRED" == excinfo.value.error_type

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_friend_info(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            friend = await self.reddit.redditor(self.FRIEND, fetch=True)
            redditor = await friend.friend_info()
            assert self.FRIEND == redditor
            assert "date" in redditor.__dict__
            assert "created_utc" not in redditor.__dict__
            await redditor.load()
            assert hasattr(redditor, "created_utc")

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_fullname_init(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            redditor = await self.reddit.redditor(
                fullname=self.FRIEND_FULLNAME, fetch=True
            )
            assert redditor.name == self.FRIEND

    async def test_gild__no_creddits(self):
        self.reddit.read_only = False
        with self.use_cassette():
            with pytest.raises(RedditAPIException) as excinfo:
                redditor = await self.reddit.redditor("subreddit_stats")
                await redditor.gild()
            assert "INSUFFICIENT_COINS" == excinfo.value.error_type

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_message(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            redditor = await self.reddit.redditor("subreddit_stats")
            await redditor.message("Async PRAW test", "This is a test fromAsync PRAW")

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_message_from_subreddit(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            redditor = await self.reddit.redditor("subreddit_stats")
            await redditor.message(
                "Async PRAW test",
                "This is a test from Async PRAW",
                from_subreddit=pytest.placeholders.test_subreddit,
            )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_moderated(self, _):
        with self.use_cassette():
            redditor = await self.reddit.redditor("spez")
            redditor_no_mod = await self.reddit.redditor("Turambar420")
            moderated = await redditor.moderated()
            assert len(moderated) > 0
            assert len(moderated[0].display_name) > 0
            not_moderated = await redditor_no_mod.moderated()
            assert len(not_moderated) == 0

    async def test_multireddits(self):
        with self.use_cassette():
            redditor = await self.reddit.redditor("kjoneslol")
            multireddits = await redditor.multireddits()
            for multireddit in multireddits:
                if "sfwpornnetwork" == multireddit.name:
                    break
            else:
                assert False, "sfwpornnetwork not found in multireddits"

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_stream__comments(self, _):
        with self.use_cassette():
            redditor = await self.reddit.redditor("AutoModerator")
            generator = redditor.stream.comments()
            for i in range(101):
                assert isinstance(await self.async_next(generator), Comment)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_stream__submissions(self, _):
        with self.use_cassette():
            redditor = await self.reddit.redditor(pytest.placeholders.username)
            generator = redditor.stream.submissions()
            for i in range(101):
                assert isinstance(await self.async_next(generator), Submission)

    async def test_trophies(self):
        with self.use_cassette():
            redditor = await self.reddit.redditor("spez")
            trophies = await redditor.trophies()
            assert len(trophies) > 0
            assert len(trophies[0].name) > 0

    async def test_trophies__user_not_exist(self):
        with self.use_cassette():
            redditor = Redditor(self.reddit, "thisusershouldnotexist")
            with pytest.raises(RedditAPIException) as excinfo:
                await redditor.trophies()
            assert "USER_DOESNT_EXIST" == excinfo.value.error_type

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_unblock(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            blocked = await self.reddit.user.blocked()
            for redditor in blocked:
                await redditor.unblock()

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_unfriend(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            friends = await self.reddit.user.friends()
            redditor = friends[0]
            assert await redditor.unfriend() is None


class TestRedditorListings(IntegrationTest):
    async def test_comments__controversial(self):
        with self.use_cassette():
            redditor = await self.reddit.redditor("spez")
            comments = await self.async_list(redditor.comments.controversial())
        assert len(comments) == 100

    async def test_comments__hot(self):
        with self.use_cassette():
            redditor = await self.reddit.redditor("spez")
            comments = await self.async_list(redditor.comments.hot())
        assert len(comments) == 100

    async def test_comments__new(self):
        with self.use_cassette():
            redditor = await self.reddit.redditor("spez")
            comments = await self.async_list(redditor.comments.new())
        assert len(comments) == 100

    async def test_comments__top(self):
        with self.use_cassette():
            redditor = await self.reddit.redditor("spez")
            comments = await self.async_list(redditor.comments.top())
        assert len(comments) == 100

    async def test_controversial(self):
        with self.use_cassette():
            redditor = await self.reddit.redditor("spez")
            items = await self.async_list(redditor.controversial())
        assert len(items) == 100

    async def test_downvoted(self):
        self.reddit.read_only = False
        with self.use_cassette():
            redditor = await self.reddit.redditor(pytest.placeholders.username)
            submissions = await self.async_list(redditor.downvoted())
        assert len(submissions) > 0

    async def test_downvoted__in_read_only_mode(self):
        with self.use_cassette():
            redditor = await self.reddit.redditor(pytest.placeholders.username)
            with pytest.raises(Forbidden):
                await self.async_list(redditor.downvoted())

    async def test_downvoted__other_user(self):
        self.reddit.read_only = False
        with self.use_cassette():
            redditor = await self.reddit.redditor("spez")
            with pytest.raises(Forbidden):
                await self.async_list(redditor.downvoted())

    async def test_gilded(self):
        with self.use_cassette():
            redditor = await self.reddit.redditor("spez")
            items = await self.async_list(redditor.gilded(limit=50))
        assert len(items) == 50

    async def test_gildings(self):
        self.reddit.read_only = False
        with self.use_cassette():
            redditor = await self.reddit.redditor(pytest.placeholders.username)
            items = await self.async_list(redditor.gildings())
        assert isinstance(items, list)

    async def test_gildings__in_read_only_mode(self):
        with self.use_cassette():
            redditor = await self.reddit.redditor(pytest.placeholders.username)
            with pytest.raises(Forbidden):
                await self.async_list(redditor.gildings())

    async def test_gildings__other_user(self):
        self.reddit.read_only = False
        with self.use_cassette():
            redditor = await self.reddit.redditor("spez")
            with pytest.raises(Forbidden):
                await self.async_list(redditor.gildings())

    async def test_hidden(self):
        self.reddit.read_only = False
        with self.use_cassette():
            redditor = await self.reddit.redditor(pytest.placeholders.username)
            submissions = await self.async_list(redditor.hidden())
        assert len(submissions) > 0

    async def test_hidden__in_read_only_mode(self):
        with self.use_cassette():
            redditor = await self.reddit.redditor(pytest.placeholders.username)
            with pytest.raises(Forbidden):
                await self.async_list(redditor.hidden())

    async def test_hidden__other_user(self):
        self.reddit.read_only = False
        with self.use_cassette():
            redditor = await self.reddit.redditor("spez")
            with pytest.raises(Forbidden):
                await self.async_list(redditor.hidden())

    async def test_hot(self):
        with self.use_cassette():
            redditor = await self.reddit.redditor("spez")
            items = await self.async_list(redditor.hot())
        assert len(items) == 100

    async def test_new(self):
        with self.use_cassette():
            redditor = await self.reddit.redditor("spez")
            items = await self.async_list(redditor.new())
        assert len(items) == 100

    async def test_saved(self):
        self.reddit.read_only = False
        with self.use_cassette():
            redditor = await self.reddit.redditor(pytest.placeholders.username)
            items = await self.async_list(redditor.saved())
        assert len(items) > 0

    async def test_saved__in_read_only_mode(self):
        with self.use_cassette():
            redditor = await self.reddit.redditor(pytest.placeholders.username)
            with pytest.raises(Forbidden):
                await self.async_list(redditor.saved())

    async def test_saved__other_user(self):
        self.reddit.read_only = False
        with self.use_cassette():
            redditor = await self.reddit.redditor("spez")
            with pytest.raises(Forbidden):
                await self.async_list(redditor.saved())

    async def test_submissions__controversial(self):
        with self.use_cassette():
            redditor = await self.reddit.redditor("spladug")
            submissions = await self.async_list(redditor.submissions.controversial())
        assert len(submissions) == 100

    async def test_submissions__hot(self):
        with self.use_cassette():
            redditor = await self.reddit.redditor("spez")
            submissions = await self.async_list(redditor.submissions.hot())
        assert len(submissions) == 100

    async def test_submissions__new(self):
        with self.use_cassette():
            redditor = await self.reddit.redditor("spez")
            submissions = await self.async_list(redditor.submissions.new())
        assert len(submissions) == 100

    async def test_submissions__top(self):
        with self.use_cassette():
            redditor = await self.reddit.redditor("spladug")
            submissions = await self.async_list(redditor.submissions.top())
        assert len(submissions) == 100

    async def test_top(self):
        with self.use_cassette():
            redditor = await self.reddit.redditor("spez")
            items = await self.async_list(redditor.top())
        assert len(items) == 100

    async def test_trust_and_distrust(self):
        self.reddit.read_only = False
        with self.use_cassette():
            redditor = await self.reddit.redditor("PyAPITestUser3")
            await redditor.trust()
            redditor = (await self.reddit.user.trusted())[0]
            await redditor.distrust()

    async def test_trust_blocked_user(self):
        self.reddit.read_only = False
        with self.use_cassette():
            redditor = await self.reddit.redditor("kn0thing")
            await redditor.block()
            with pytest.raises(RedditAPIException) as excinfo:
                await redditor.trust()
            assert "CANT_WHITELIST_AN_ENEMY" == excinfo.value.error_type

    async def test_upvoted(self):
        self.reddit.read_only = False
        with self.use_cassette():
            redditor = await self.reddit.redditor(pytest.placeholders.username)
            submissions = await self.async_list(redditor.upvoted())
        assert len(submissions) > 0

    async def test_upvoted__in_read_only_mode(self):
        with self.use_cassette():
            redditor = await self.reddit.redditor(pytest.placeholders.username)
            with pytest.raises(Forbidden):
                await self.async_list(redditor.upvoted())

    async def test_upvoted__other_user(self):
        self.reddit.read_only = False
        with self.use_cassette():
            redditor = await self.reddit.redditor("spez")
            with pytest.raises(Forbidden):
                await self.async_list(redditor.upvoted())
