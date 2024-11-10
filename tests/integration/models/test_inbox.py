"""Test asyncpraw.models.inbox."""

import pytest
from prawcore import Forbidden

from asyncpraw.models import Comment, Message, Redditor, Subreddit

from .. import IntegrationTest


class TestInbox(IntegrationTest):
    async def test_all(self, reddit):
        reddit.read_only = False
        count = 0
        async for item in reddit.inbox.all():
            assert isinstance(item, Comment) or isinstance(item, Message)
            count += 1
        assert count == 100

    async def test_all__with_limit(self, reddit):
        reddit.read_only = False
        assert len(await self.async_list(reddit.inbox.all(limit=128))) == 128

    async def test_comment_replies(self, reddit):
        reddit.read_only = False
        count = 0
        async for item in reddit.inbox.comment_replies(limit=64):
            assert isinstance(item, Comment)
            assert item.parent_id.startswith(reddit.config.kinds["comment"])
            count += 1
        assert count == 64

    async def test_comment_reply__refresh(self, reddit):
        reddit.read_only = False
        comment = await self.async_next(reddit.inbox.comment_replies())
        saved_id = comment.id
        assert isinstance(comment, Comment)
        await comment.refresh()
        assert saved_id == comment.id

    async def test_mark_all_read(self, reddit):
        reddit.read_only = False
        await reddit.inbox.mark_unread(await self.async_list(reddit.inbox.all(limit=2)))
        await reddit.inbox.mark_all_read()
        assert not await self.async_list(reddit.inbox.unread())

    async def test_mark_read(self, reddit):
        reddit.read_only = False
        await reddit.inbox.mark_read(await self.async_list(reddit.inbox.unread()))

    async def test_mark_unread(self, reddit):
        reddit.read_only = False
        await reddit.inbox.mark_unread(await self.async_list(reddit.inbox.all()))

    async def test_mention__refresh(self, reddit):
        reddit.read_only = False
        mention = await self.async_next(reddit.inbox.mentions())
        assert isinstance(mention, Comment)
        await mention.refresh()

    async def test_mentions(self, reddit):
        reddit.read_only = False
        count = 0
        async for item in reddit.inbox.mentions(limit=16):
            assert isinstance(item, Comment)
            count += 1
        assert count > 0

    async def test_message(self, reddit):
        reddit.read_only = False
        message = await reddit.inbox.message("kfrjvh")
        assert message.name.split("_", 1)[1] == "kfrjvh"
        assert isinstance(message, Message)
        assert isinstance(message.author, Redditor)
        assert isinstance(message.dest, Subreddit)
        assert message.replies == []
        assert isinstance(message.subreddit, Subreddit)

    async def test_message__unauthorized(self, reddit):
        reddit.read_only = False
        with pytest.raises(Forbidden):
            await reddit.inbox.message("6i8om7")

    async def test_message_collapse(self, reddit):
        reddit.read_only = False
        await reddit.inbox.collapse(await self.async_list(reddit.inbox.messages()))

    async def test_message_uncollapse(self, reddit):
        reddit.read_only = False
        await reddit.inbox.uncollapse(await self.async_list(reddit.inbox.messages()))

    async def test_messages(self, reddit):
        reddit.read_only = False
        count = 0
        async for item in reddit.inbox.messages(limit=64):
            assert isinstance(item, Message)
            count += 1
        assert count == 64

    async def test_sent(self, reddit):
        reddit.read_only = False
        count = 0
        async for item in reddit.inbox.sent(limit=48):
            assert isinstance(item, Message)
            assert item.author == reddit.config.username
            count += 1
        assert count == 48

    async def test_stream(self, reddit):
        reddit.read_only = False
        item = await self.async_next(reddit.inbox.stream())
        assert isinstance(item, Comment) or isinstance(item, Message)

    async def test_submission_replies(self, reddit):
        reddit.read_only = False
        count = 0
        async for item in reddit.inbox.submission_replies(limit=64):
            assert isinstance(item, Comment)
            assert item.parent_id.startswith(reddit.config.kinds["submission"])
            count += 1
        assert count == 64

    async def test_unread(self, reddit):
        reddit.read_only = False
        count = 0
        async for item in reddit.inbox.unread(limit=64):
            count += 1
        assert count == 64
