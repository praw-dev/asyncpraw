from asynctest import mock

from asyncpraw.models import Comment, Submission, Subreddit

from ... import IntegrationTest


class TestMultireddit(IntegrationTest):
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_add(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            multireddits = await self.reddit.user.multireddits()
            multi = multireddits[0]
            await multi.add("redditdev")
            await multi.load()
            assert "redditdev" in multi.subreddits

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_copy(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            multi = await self.reddit.multireddit(
                "kjoneslol", "sfwpornnetwork", fetch=True
            )
            new = await multi.copy()
        assert new.name == multi.name
        assert new.display_name == multi.display_name
        assert "kjoneslol" not in new.path

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_copy__with_display_name(self, _):
        self.reddit.read_only = False
        multi = await self.reddit.multireddit("kjoneslol", "sfwpornnetwork")
        name = "A--B\n" * 10
        with self.use_cassette():
            new = await multi.copy(display_name=name)
        assert new.name == "a_b_a_b_a_b_a_b_a_b"
        assert new.display_name == name
        assert "kjoneslol" not in new.path

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_create(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            multireddit = await self.reddit.multireddit.create(
                "Async PRAW create test", subreddits=["redditdev"]
            )
        assert multireddit.display_name == "Async PRAW create test"
        assert multireddit.name == "async_praw_create_test"

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_delete(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            multireddits = await self.reddit.user.multireddits()
            multi = multireddits[0]
            await multi.delete()

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_remove(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            multireddits = await self.reddit.user.multireddits()
            multi = multireddits[0]
            await multi.remove("redditdev")
            await multi.load()
            assert "redditdev" not in multi.subreddits

    async def test_subreddits(self):
        with self.use_cassette():
            multi = await self.reddit.multireddit(
                "kjoneslol", "sfwpornnetwork", fetch=True
            )
            assert multi.subreddits
        assert all(isinstance(x, Subreddit) for x in multi.subreddits)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update(self, _):
        self.reddit.read_only = False
        subreddits = ["pokemongo", "pokemongodev"]
        with self.use_cassette():
            multireddits = await self.reddit.user.multireddits()
            multi = multireddits[0]
            prev_path = multi.path
            await multi.update(
                display_name="Updated display name", subreddits=subreddits
            )
        assert multi.display_name == "Updated display name"
        assert multi.path == prev_path
        assert multi.subreddits == subreddits


class TestMultiredditListings(IntegrationTest):
    async def test_comments(self):
        multi = await self.reddit.multireddit("kjoneslol", "sfwpornnetwork")
        with self.use_cassette():
            comments = await self.async_list(multi.comments())
        assert len(comments) == 100

    async def test_controversial(self):
        multi = await self.reddit.multireddit("kjoneslol", "sfwpornnetwork")
        with self.use_cassette():
            submissions = await self.async_list(multi.controversial())
        assert len(submissions) == 100

    async def test_gilded(self):
        multi = await self.reddit.multireddit("kjoneslol", "sfwpornnetwork")
        with self.use_cassette():
            submissions = await self.async_list(multi.gilded())
        assert len(submissions) == 100

    async def test_hot(self):
        multi = await self.reddit.multireddit("kjoneslol", "sfwpornnetwork")
        with self.use_cassette():
            submissions = await self.async_list(multi.hot())
        assert len(submissions) == 100

    async def test_new(self):
        multi = await self.reddit.multireddit("kjoneslol", "sfwpornnetwork")
        with self.use_cassette():
            submissions = await self.async_list(multi.new())
        assert len(submissions) == 100

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_new__self_multi(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            multireddits = await self.reddit.user.multireddits()
            multi = multireddits[0]
            submissions = await self.async_list(multi.new())
        assert len(submissions) == 100

    async def test_random_rising(self):
        multi = await self.reddit.multireddit("kjoneslol", "sfwpornnetwork")
        with self.use_cassette():
            submissions = await self.async_list(multi.random_rising())
        assert len(submissions) > 0

    async def test_rising(self):
        multi = await self.reddit.multireddit("kjoneslol", "sfwpornnetwork")
        with self.use_cassette():
            submissions = await self.async_list(multi.rising())
        assert len(submissions) > 0

    async def test_top(self):
        multi = await self.reddit.multireddit("kjoneslol", "sfwpornnetwork")
        with self.use_cassette():
            submissions = await self.async_list(multi.top())
        assert len(submissions) == 100


class TestMultiredditStreams(IntegrationTest):
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_comments(self, _):
        multi = await self.reddit.multireddit("kjoneslol", "sfwpornnetwork")
        with self.use_cassette():
            generator = multi.stream.comments()
            for i in range(101):
                assert isinstance(await self.async_next(generator), Comment)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_comments__with_pause(self, _):
        multi = await self.reddit.multireddit("kjoneslol", "sfwpornnetwork")
        with self.use_cassette():
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

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_submissions(self, _):
        multi = await self.reddit.multireddit("kjoneslol", "sfwpornnetwork")
        with self.use_cassette():
            generator = multi.stream.submissions()
            for i in range(102):
                assert isinstance(await self.async_next(generator), Submission)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_submissions__with_pause(self, _):
        multi = await self.reddit.multireddit("kjoneslol", "sfwpornnetwork")
        with self.use_cassette("TestMultiredditStreams.test_submissions"):
            generator = multi.stream.submissions(pause_after=-1)
            submission = await self.async_next(generator)
            submission_count = 0
            while submission is not None:
                submission_count += 1
                submission = await self.async_next(generator)
            assert submission_count == 100
