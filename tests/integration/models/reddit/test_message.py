import pytest
from asynctest import mock

from asyncpraw.models import Message, Redditor, Subreddit, SubredditMessage

from ... import IntegrationTest


class TestMessage(IntegrationTest):
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_attributes(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            messages = await self.async_list(self.reddit.inbox.messages())
            count = len(messages)
            while messages:
                message = messages.pop(0)
                messages.extend(message.replies)
                count -= 1
                try:
                    assert message.author is None or isinstance(
                        message.author, Redditor
                    )
                    assert isinstance(message.dest, (Redditor, Subreddit))
                    assert isinstance(message.replies, list)
                    assert message.subreddit is None or isinstance(
                        message.subreddit, Subreddit
                    )
                except Exception:
                    import pprint

                    pprint.pprint(vars(message))
                    raise
        assert count < 0

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_block(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            message = None
            async for item in self.reddit.inbox.messages():
                if item.author and item.author != pytest.placeholders.username:
                    message = item
                    break
            else:
                assert False, "no message found"
            await message.block()

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_delete(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            message = await self.async_next(self.reddit.inbox.messages())
            await message.delete()

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_mark_read(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            message = None
            async for item in self.reddit.inbox.unread():
                if isinstance(item, Message):
                    message = item
                    break
            else:
                assert False, "no message found in unread"
            await message.mark_read()

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_mark_unread(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            message = await self.async_next(self.reddit.inbox.messages())
            await message.mark_unread()

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_message_collapse(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            message = await self.async_next(self.reddit.inbox.messages())
            await message.collapse()

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_message_uncollapse(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            message = await self.async_next(self.reddit.inbox.messages())
            await message.uncollapse()

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_reply(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            message = await self.async_next(self.reddit.inbox.messages())
            reply = await message.reply("Message reply")
            assert reply.author == pytest.placeholders.username
            assert reply.body == "Message reply"
            assert reply.first_message_name == message.fullname


class TestSubredditMessage(IntegrationTest):
    async def test_mute(self):
        self.reddit.read_only = False
        with self.use_cassette():
            message = SubredditMessage(self.reddit, _data={"id": "faj6z"})
            await message.mute()

    async def test_unmute(self):
        self.reddit.read_only = False
        with self.use_cassette():
            message = SubredditMessage(self.reddit, _data={"id": "faj6z"})
            await message.unmute()
