import pytest

from asyncpraw.models import Comment, Submission, Subreddit

from ... import IntegrationTest


class TestMultireddit(IntegrationTest):
    async def test_add(self, reddit):
        reddit.read_only = False
        multireddits = await reddit.user.multireddits()
        multi = multireddits[0]
        await multi.add("redditdev")
        await multi.load()
        assert "redditdev" in multi.subreddits

    async def test_copy(self, reddit):
        reddit.read_only = False
        multi = await reddit.multireddit(redditor="kjoneslol", name="sfwpornnetwork", fetch=True)
        new = await multi.copy()
        assert new.name == multi.name
        assert new.display_name == multi.display_name
        assert "kjoneslol" not in new.path

    async def test_copy__with_display_name(self, reddit):
        reddit.read_only = False
        multi = await reddit.multireddit(redditor="kjoneslol", name="sfwpornnetwork")
        name = "A--B\n" * 10
        new = await multi.copy(display_name=name)
        assert new.name == "a_b_a_b_a_b_a_b_a_b"
        assert new.display_name == name
        assert "kjoneslol" not in new.path

    async def test_create(self, reddit):
        reddit.read_only = False
        multireddit = await reddit.multireddit.create(display_name="Async PRAW create test", subreddits=["redditdev"])
        assert multireddit.display_name == "Async PRAW create test"
        assert multireddit.name == "async_praw_create_test"

    async def test_delete(self, reddit):
        reddit.read_only = False
        multireddits = await reddit.user.multireddits()
        multi = multireddits[0]
        await multi.delete()

    async def test_remove(self, reddit):
        reddit.read_only = False
        multireddits = await reddit.user.multireddits()
        multi = multireddits[0]
        await multi.remove("redditdev")
        await multi.load()
        assert "redditdev" not in multi.subreddits

    async def test_subreddits(self, reddit):
        multi = await reddit.multireddit(redditor="kjoneslol", name="sfwpornnetwork", fetch=True)
        assert multi.subreddits
        assert all(isinstance(x, Subreddit) for x in multi.subreddits)

    async def test_update(self, reddit):
        reddit.read_only = False
        subreddits = ["pokemongo", "pokemongodev"]
        multireddits = await reddit.user.multireddits()
        multi = multireddits[0]
        prev_path = multi.path
        await multi.update(display_name="Updated display name", subreddits=subreddits)
        assert multi.display_name == "Updated display name"
        assert multi.path == prev_path
        assert multi.subreddits == subreddits


class TestMultiredditListings(IntegrationTest):
    async def test_comments(self, reddit):
        multi = await reddit.multireddit(redditor="kjoneslol", name="sfwpornnetwork")
        comments = await self.async_list(multi.comments())
        assert len(comments) == 100

    async def test_controversial(self, reddit):
        multi = await reddit.multireddit(redditor="kjoneslol", name="sfwpornnetwork")
        submissions = await self.async_list(multi.controversial())
        assert len(submissions) == 100

    async def test_hot(self, reddit):
        multi = await reddit.multireddit(redditor="kjoneslol", name="sfwpornnetwork")
        submissions = await self.async_list(multi.hot())
        assert len(submissions) == 100

    async def test_new(self, reddit):
        multi = await reddit.multireddit(redditor="kjoneslol", name="sfwpornnetwork")
        submissions = await self.async_list(multi.new())
        assert len(submissions) == 100

    async def test_new__self_multi(self, reddit):
        reddit.read_only = False
        multireddits = await reddit.user.multireddits()
        multi = multireddits[0]
        submissions = await self.async_list(multi.new())
        assert len(submissions) == 100

    async def test_rising(self, reddit):
        multi = await reddit.multireddit(redditor="kjoneslol", name="sfwpornnetwork")
        submissions = await self.async_list(multi.rising())
        assert len(submissions) > 0

    async def test_top(self, reddit):
        multi = await reddit.multireddit(redditor="kjoneslol", name="sfwpornnetwork")
        submissions = await self.async_list(multi.top())
        assert len(submissions) == 100


class TestMultiredditStreams(IntegrationTest):
    async def test_comments(self, reddit):
        multi = await reddit.multireddit(redditor="kjoneslol", name="sfwpornnetwork")
        generator = multi.stream.comments()
        for i in range(101):
            assert isinstance(await self.async_next(generator), Comment)

    async def test_comments__with_pause(self, reddit):
        multi = await reddit.multireddit(redditor="kjoneslol", name="sfwpornnetwork")
        comment_stream = multi.stream.comments(pause_after=0)
        comment_count = 1
        pause_count = 1
        comment = await self.async_next(comment_stream)
        while comment is not None:
            comment_count += 1
            comment = await self.async_next(comment_stream)
        while comment is None:
            pause_count += 1
            comment = await self.async_next(comment_stream)
        assert comment_count == 101
        assert pause_count == 2

    async def test_submissions(self, reddit):
        multi = await reddit.multireddit(redditor="kjoneslol", name="sfwpornnetwork")
        generator = multi.stream.submissions()
        for i in range(102):
            assert isinstance(await self.async_next(generator), Submission)

    @pytest.mark.cassette_name("TestMultiredditStreams.test_submissions")
    async def test_submissions__with_pause(self, reddit):
        multi = await reddit.multireddit(redditor="kjoneslol", name="sfwpornnetwork")
        generator = multi.stream.submissions(pause_after=-1)
        submission = await self.async_next(generator)
        submission_count = 0
        while submission is not None:
            submission_count += 1
            submission = await self.async_next(generator)
        assert submission_count == 100
