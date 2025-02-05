"""Test asyncpraw.models.redditor."""

import pytest
from asyncprawcore import Forbidden

from asyncpraw.exceptions import RedditAPIException
from asyncpraw.models import Comment, Redditor, Submission

from ... import IntegrationTest


class TestRedditor(IntegrationTest):
    FRIEND = "PyAPITestUser3"
    FRIEND_FULLNAME = "t2_6c1xj"

    async def test_block(self, reddit):
        reddit.read_only = False
        redditor = await reddit.redditor(self.FRIEND, fetch=True)
        await redditor.block()

    async def test_friend(self, reddit):
        reddit.read_only = False
        redditor = await reddit.redditor(self.FRIEND.lower(), fetch=True)
        await redditor.friend()

    async def test_friend__with_note__no_gold(self, reddit):
        reddit.read_only = False
        with pytest.raises(RedditAPIException) as excinfo:
            redditor = await reddit.redditor(self.FRIEND.lower(), fetch=True)
            await redditor.friend(note="asyncpraw")
        assert "GOLD_REQUIRED" == excinfo.value.items[0].error_type

    async def test_friend_info(self, reddit):
        reddit.read_only = False
        friend = await reddit.redditor(self.FRIEND, fetch=True)
        redditor = await friend.friend_info()
        assert self.FRIEND == redditor
        assert "date" in redditor.__dict__
        assert "created_utc" not in redditor.__dict__
        await redditor.load()
        assert hasattr(redditor, "created_utc")

    async def test_fullname_init(self, reddit):
        reddit.read_only = False
        redditor = await reddit.redditor(fetch=True, fullname=self.FRIEND_FULLNAME)
        assert redditor.name == self.FRIEND

    async def test_gild__no_creddits(self, reddit):
        reddit.read_only = False
        with pytest.raises(RedditAPIException) as excinfo:
            redditor = await reddit.redditor("subreddit_stats")
            await redditor.gild()
        assert "INSUFFICIENT_COINS" == excinfo.value.items[0].error_type

    async def test_message(self, reddit):
        reddit.read_only = False
        redditor = await reddit.redditor("subreddit_stats")
        await redditor.message(
            subject="Async PRAW test", message="This is a test from Async PRAW"
        )

    async def test_message_from_subreddit(self, reddit):
        reddit.read_only = False
        redditor = await reddit.redditor("subreddit_stats")
        await redditor.message(
            subject="Async PRAW test",
            message="This is a test from Async PRAW",
            from_subreddit=pytest.placeholders.test_subreddit,
        )

    async def test_moderated(self, reddit):
        redditor = await reddit.redditor("spez")
        redditor_no_mod = await reddit.redditor("Turambar420")
        moderated = await redditor.moderated()
        assert len(moderated) > 0
        assert len(moderated[0].display_name) > 0
        not_moderated = await redditor_no_mod.moderated()
        assert len(not_moderated) == 0

    async def test_multireddits(self, reddit):
        redditor = await reddit.redditor("kjoneslol")
        multireddits = await redditor.multireddits()
        for multireddit in multireddits:
            if "sfwpornnetwork" == multireddit.name:
                break
        else:
            assert False, "sfwpornnetwork not found in multireddits"

    async def test_notes__subreddits(self, reddit):
        reddit.read_only = False
        redditor = await reddit.redditor("Lil_SpazTest")
        notes = await self.async_list(
            redditor.notes.subreddits(
                pytest.placeholders.test_subreddit, "Lil_SpazTest"
            )
        )
        assert len(notes) == 2
        assert notes[0].user == redditor
        assert notes[1] is None

    async def test_stream__comments(self, reddit):
        redditor = await reddit.redditor("AutoModerator")
        generator = redditor.stream.comments()
        for i in range(101):
            assert isinstance(await self.async_next(generator), Comment)

    async def test_stream__submissions(self, reddit):
        redditor = await reddit.redditor(pytest.placeholders.username)
        generator = redditor.stream.submissions()
        for i in range(101):
            assert isinstance(await self.async_next(generator), Submission)

    async def test_trophies(self, reddit):
        redditor = await reddit.redditor("spez")
        trophies = await redditor.trophies()
        assert len(trophies) > 0
        assert len(trophies[0].name) > 0

    async def test_trophies__user_not_exist(self, reddit):
        redditor = Redditor(reddit, "thisusershouldnotexist")
        with pytest.raises(RedditAPIException) as excinfo:
            await redditor.trophies()
        assert "USER_DOESNT_EXIST" == excinfo.value.items[0].error_type

    async def test_unblock(self, reddit):
        reddit.read_only = False
        blocked = await reddit.user.blocked()
        for redditor in blocked:
            await redditor.unblock()

    async def test_unfriend(self, reddit):
        reddit.read_only = False
        friends = await reddit.user.friends()
        redditor = friends[0]
        assert await redditor.unfriend() is None


class TestRedditorListings(IntegrationTest):
    async def test_comments__controversial(self, reddit):
        redditor = await reddit.redditor("spez")
        comments = await self.async_list(redditor.comments.controversial())
        assert len(comments) == 100

    async def test_comments__hot(self, reddit):
        redditor = await reddit.redditor("spez")
        comments = await self.async_list(redditor.comments.hot())
        assert len(comments) == 100

    async def test_comments__new(self, reddit):
        redditor = await reddit.redditor("spez")
        comments = await self.async_list(redditor.comments.new())
        assert len(comments) == 100

    async def test_comments__top(self, reddit):
        redditor = await reddit.redditor("spez")
        comments = await self.async_list(redditor.comments.top())
        assert len(comments) == 100

    async def test_controversial(self, reddit):
        redditor = await reddit.redditor("spez")
        items = await self.async_list(redditor.controversial())
        assert len(items) == 100

    async def test_downvoted(self, reddit):
        reddit.read_only = False
        redditor = await reddit.redditor(pytest.placeholders.username)
        submissions = await self.async_list(redditor.downvoted())
        assert len(submissions) > 0

    async def test_downvoted__in_read_only_mode(self, reddit):
        redditor = await reddit.redditor(pytest.placeholders.username)
        with pytest.raises(Forbidden):
            await self.async_list(redditor.downvoted())

    async def test_downvoted__other_user(self, reddit):
        reddit.read_only = False
        redditor = await reddit.redditor("spez")
        with pytest.raises(Forbidden):
            await self.async_list(redditor.downvoted())

    async def test_gilded(self, reddit):
        redditor = await reddit.redditor("spez")
        items = await self.async_list(redditor.gilded(limit=50))
        assert len(items) == 50

    async def test_gildings(self, reddit):
        reddit.read_only = False
        redditor = await reddit.redditor(pytest.placeholders.username)
        items = await self.async_list(redditor.gildings())
        assert isinstance(items, list)

    async def test_gildings__in_read_only_mode(self, reddit):
        redditor = await reddit.redditor(pytest.placeholders.username)
        with pytest.raises(Forbidden):
            await self.async_list(redditor.gildings())

    async def test_gildings__other_user(self, reddit):
        reddit.read_only = False
        redditor = await reddit.redditor("spez")
        with pytest.raises(Forbidden):
            await self.async_list(redditor.gildings())

    async def test_hidden(self, reddit):
        reddit.read_only = False
        redditor = await reddit.redditor(pytest.placeholders.username)
        submissions = await self.async_list(redditor.hidden())
        assert len(submissions) > 0

    async def test_hidden__in_read_only_mode(self, reddit):
        redditor = await reddit.redditor(pytest.placeholders.username)
        with pytest.raises(Forbidden):
            await self.async_list(redditor.hidden())

    async def test_hidden__other_user(self, reddit):
        reddit.read_only = False
        redditor = await reddit.redditor("spez")
        with pytest.raises(Forbidden):
            await self.async_list(redditor.hidden())

    async def test_hot(self, reddit):
        redditor = await reddit.redditor("spez")
        items = await self.async_list(redditor.hot())
        assert len(items) == 100

    async def test_new(self, reddit):
        redditor = await reddit.redditor("spez")
        items = await self.async_list(redditor.new())
        assert len(items) == 100

    async def test_saved(self, reddit):
        reddit.read_only = False
        redditor = await reddit.redditor(pytest.placeholders.username)
        items = await self.async_list(redditor.saved())
        assert len(items) > 0

    async def test_saved__in_read_only_mode(self, reddit):
        redditor = await reddit.redditor(pytest.placeholders.username)
        with pytest.raises(Forbidden):
            await self.async_list(redditor.saved())

    async def test_saved__other_user(self, reddit):
        reddit.read_only = False
        redditor = await reddit.redditor("spez")
        with pytest.raises(Forbidden):
            await self.async_list(redditor.saved())

    async def test_submissions__controversial(self, reddit):
        redditor = await reddit.redditor("spladug")
        submissions = await self.async_list(redditor.submissions.controversial())
        assert len(submissions) == 100

    async def test_submissions__hot(self, reddit):
        redditor = await reddit.redditor("spez")
        submissions = await self.async_list(redditor.submissions.hot())
        assert len(submissions) == 100

    async def test_submissions__new(self, reddit):
        redditor = await reddit.redditor("spez")
        submissions = await self.async_list(redditor.submissions.new())
        assert len(submissions) == 100

    async def test_submissions__top(self, reddit):
        redditor = await reddit.redditor("spladug")
        submissions = await self.async_list(redditor.submissions.top())
        assert len(submissions) == 100

    async def test_top(self, reddit):
        redditor = await reddit.redditor("spez")
        items = await self.async_list(redditor.top())
        assert len(items) == 100

    async def test_trust_and_distrust(self, reddit):
        reddit.read_only = False
        redditor = await reddit.redditor("PyAPITestUser3")
        await redditor.trust()
        redditor = (await reddit.user.trusted())[0]
        await redditor.distrust()

    async def test_trust_blocked_user(self, reddit):
        reddit.read_only = False
        redditor = await reddit.redditor("kn0thing")
        await redditor.block()
        with pytest.raises(RedditAPIException) as excinfo:
            await redditor.trust()
        assert "CANT_WHITELIST_AN_ENEMY" == excinfo.value.items[0].error_type

    async def test_upvoted(self, reddit):
        reddit.read_only = False
        redditor = await reddit.redditor(pytest.placeholders.username)
        submissions = await self.async_list(redditor.upvoted())
        assert len(submissions) > 0

    async def test_upvoted__in_read_only_mode(self, reddit):
        redditor = await reddit.redditor(pytest.placeholders.username)
        with pytest.raises(Forbidden):
            await self.async_list(redditor.upvoted())

    async def test_upvoted__other_user(self, reddit):
        reddit.read_only = False
        redditor = await reddit.redditor("spez")
        with pytest.raises(Forbidden):
            await self.async_list(redditor.upvoted())
