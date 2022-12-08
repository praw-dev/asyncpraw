import pytest

from asyncpraw.exceptions import ClientException
from asyncpraw.models import Emoji

from ... import IntegrationTest


class TestEmoji(IntegrationTest):
    async def test__fetch(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        emoji = await subreddit.emoji.get_emoji("test_png")
        assert emoji.created_by.startswith("t2_")

    async def test__fetch__invalid_emoji(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        with pytest.raises(ClientException) as excinfo:
            await subreddit.emoji.get_emoji("invalid")
        assert str(excinfo.value) == f"r/{subreddit} does not have the emoji invalid"
        with pytest.raises(ClientException) as excinfo2:
            await subreddit.emoji.get_emoji("Test_png")
        assert str(excinfo2.value) == f"r/{subreddit} does not have the emoji Test_png"

    async def test_delete(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        emoji = await subreddit.emoji.get_emoji("test_png")
        await emoji.delete()

    async def test_update(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        emoji = await subreddit.emoji.get_emoji("test_png")
        await emoji.update(
            mod_flair_only=False, post_flair_allowed=True, user_flair_allowed=True
        )

    async def test_update__with_preexisting_values(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        emoji = await subreddit.emoji.get_emoji("test_png")
        await emoji.update(mod_flair_only=True)


class TestSubredditEmoji(IntegrationTest):
    async def test__iter(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        count = 0
        async for emoji in subreddit.emoji:
            assert isinstance(emoji, Emoji)
            count += 1
        assert count > 0

    async def test_add(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        for extension in ["jpg", "png"]:
            emoji = await subreddit.emoji.add(
                name=f"test_{extension}",
                image_path=f"tests/integration/files/test.{extension}",
            )
            assert isinstance(emoji, Emoji)

    async def test_add_with_perms(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        for extension in ["jpg", "png"]:
            emoji = await subreddit.emoji.add(
                name=f"test_{extension}",
                image_path=f"tests/integration/files/test.{extension}",
                mod_flair_only=True,
                post_flair_allowed=True,
                user_flair_allowed=False,
            )
            assert isinstance(emoji, Emoji)
