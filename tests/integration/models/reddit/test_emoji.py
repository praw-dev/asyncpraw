import pytest
from asynctest import mock

from asyncpraw.exceptions import ClientException
from asyncpraw.models import Emoji

from ... import IntegrationTest


class TestEmoji(IntegrationTest):
    @mock.patch("asyncio.sleep", return_value=None)
    async def test__fetch(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            emoji = await subreddit.emoji.get_emoji("test_png")
            assert emoji.created_by.startswith("t2_")

    @mock.patch("asyncio.sleep", return_value=None)
    async def test__fetch__invalid_emoji(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            with pytest.raises(ClientException) as excinfo:
                await subreddit.emoji.get_emoji("invalid")
            assert str(excinfo.value) == (
                f"r/{subreddit} does not have the emoji invalid"
            )
            with pytest.raises(ClientException) as excinfo2:
                await subreddit.emoji.get_emoji("Test_png")
            assert str(excinfo2.value) == (
                f"r/{subreddit} does not have the emoji Test_png"
            )

    async def test_delete(self):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            emoji = await subreddit.emoji.get_emoji("test_png")
            await emoji.delete()

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            emoji = await subreddit.emoji.get_emoji("test_png")
            await emoji.update(
                mod_flair_only=False,
                post_flair_allowed=True,
                user_flair_allowed=True,
            )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update__with_preexisting_values(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            emoji = await subreddit.emoji.get_emoji("test_png")
            await emoji.update(mod_flair_only=True)


class TestSubredditEmoji(IntegrationTest):
    @mock.patch("asyncio.sleep", return_value=None)
    async def test__iter(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            count = 0
            async for emoji in subreddit.emoji:
                assert isinstance(emoji, Emoji)
                count += 1
            assert count > 0

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_add(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            for extension in ["jpg", "png"]:
                emoji = await subreddit.emoji.add(
                    f"test_{extension}",
                    f"tests/integration/files/test.{extension}",
                )
                assert isinstance(emoji, Emoji)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_add_with_perms(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            for extension in ["jpg", "png"]:
                emoji = await subreddit.emoji.add(
                    f"test_{extension}",
                    f"tests/integration/files/test.{extension}",
                    mod_flair_only=True,
                    post_flair_allowed=True,
                    user_flair_allowed=False,
                )
                assert isinstance(emoji, Emoji)
