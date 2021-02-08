"""Test asyncpraw.models.inbox."""
import pytest
from asyncprawcore import Forbidden
from asynctest import mock

from asyncpraw.models import Comment, Message, Redditor, Subreddit

from .. import IntegrationTest


class TestInbox(IntegrationTest):
    async def test_all(self):
        self.reddit.read_only = False
        with self.use_cassette():
            count = 0
            async for item in self.reddit.inbox.all():
                assert isinstance(item, Comment) or isinstance(item, Message)
                count += 1
            assert count == 100

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_all__with_limit(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            assert len(await self.async_list(self.reddit.inbox.all(limit=128))) == 128

    async def test_comment_replies(self):
        self.reddit.read_only = False
        with self.use_cassette():
            count = 0
            async for item in self.reddit.inbox.comment_replies(limit=64):
                assert isinstance(item, Comment)
                assert item.parent_id.startswith(self.reddit.config.kinds["comment"])
                count += 1
            assert count == 64

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_comment_reply__refresh(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            comment = await self.async_next(self.reddit.inbox.comment_replies())
            saved_id = comment.id
            assert isinstance(comment, Comment)
            await comment.refresh()
            assert saved_id == comment.id

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_mark_read(self, _):
        self.reddit.read_only = False
        with self.use_cassette(match_requests_on=["uri", "method", "body"]):
            await self.reddit.inbox.mark_read(
                await self.async_list(self.reddit.inbox.unread())
            )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_mark_unread(self, _):
        self.reddit.read_only = False
        with self.use_cassette(match_requests_on=["uri", "method", "body"]):
            await self.reddit.inbox.mark_unread(
                await self.async_list(self.reddit.inbox.all())
            )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_mention__refresh(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            mention = await self.async_next(self.reddit.inbox.mentions())
            assert isinstance(mention, Comment)
            await mention.refresh()

    async def test_mentions(self):
        self.reddit.read_only = False
        with self.use_cassette():
            count = 0
            async for item in self.reddit.inbox.mentions(limit=16):
                assert isinstance(item, Comment)
                count += 1
            assert count > 0

    async def test_message(self):
        self.reddit.read_only = False
        with self.use_cassette():
            message = await self.reddit.inbox.message("kfrjvh")
        assert message.name.split("_", 1)[1] == "kfrjvh"
        assert isinstance(message, Message)
        assert isinstance(message.author, Redditor)
        assert isinstance(message.dest, Subreddit)
        assert message.replies == []
        assert isinstance(message.subreddit, Subreddit)

    async def test_message__unauthorized(self):
        self.reddit.read_only = False
        with self.use_cassette():
            with pytest.raises(Forbidden):
                await self.reddit.inbox.message("6i8om7")

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_message_collapse(self, _):
        self.reddit.read_only = False
        with self.use_cassette(match_requests_on=["uri", "method", "body"]):
            await self.reddit.inbox.collapse(
                await self.async_list(self.reddit.inbox.messages())
            )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_message_uncollapse(self, _):
        self.reddit.read_only = False
        with self.use_cassette(match_requests_on=["uri", "method", "body"]):
            await self.reddit.inbox.uncollapse(
                await self.async_list(self.reddit.inbox.messages())
            )

    async def test_messages(self):
        self.reddit.read_only = False
        with self.use_cassette():
            count = 0
            async for item in self.reddit.inbox.messages(limit=64):
                assert isinstance(item, Message)
                count += 1
            assert count == 64

    async def test_sent(self):
        self.reddit.read_only = False
        with self.use_cassette():
            count = 0
            async for item in self.reddit.inbox.sent(limit=48):
                assert isinstance(item, Message)
                assert item.author == self.reddit.config.username
                count += 1
            assert count == 48

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_stream(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            item = await self.async_next(self.reddit.inbox.stream())
            assert isinstance(item, Comment) or isinstance(item, Message)

    async def test_submission_replies(self):
        self.reddit.read_only = False
        with self.use_cassette():
            count = 0
            async for item in self.reddit.inbox.submission_replies(limit=64):
                assert isinstance(item, Comment)
                assert item.parent_id.startswith(self.reddit.config.kinds["submission"])
                count += 1
            assert count == 64

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_unread(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            count = 0
            async for item in self.reddit.inbox.unread(limit=64):
                count += 1
            assert count == 64
