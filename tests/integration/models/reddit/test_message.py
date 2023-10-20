import pytest

from asyncpraw.models import Message, Redditor, Subreddit, SubredditMessage

from ... import IntegrationTest


class TestMessage(IntegrationTest):
    async def test_attributes(self, reddit):
        reddit.read_only = False
        messages = await self.async_list(reddit.inbox.messages())
        count = len(messages)
        while messages:
            message = messages.pop(0)
            messages.extend(message.replies)
            count -= 1
            try:
                assert message.author is None or isinstance(message.author, Redditor)
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

    async def test_block(self, reddit):
        reddit.read_only = False
        message = None
        async for item in reddit.inbox.messages():
            if item.author and item.author != pytest.placeholders.username:
                message = item
                break
        else:
            msg = "no message found"
            raise AssertionError(msg)
        await message.block()

    async def test_delete(self, reddit):
        reddit.read_only = False
        message = await self.async_next(reddit.inbox.messages())
        await message.delete()

    async def test_mark_read(self, reddit):
        reddit.read_only = False
        message = None
        async for item in reddit.inbox.unread():
            if isinstance(item, Message):
                message = item
                break
        else:
            msg = "no message found in unread"
            raise AssertionError(msg)
        await message.mark_read()

    async def test_mark_unread(self, reddit):
        reddit.read_only = False
        message = await self.async_next(reddit.inbox.messages())
        await message.mark_unread()

    async def test_message_collapse(self, reddit):
        reddit.read_only = False
        message = await self.async_next(reddit.inbox.messages())
        await message.collapse()

    async def test_message_uncollapse(self, reddit):
        reddit.read_only = False
        message = await self.async_next(reddit.inbox.messages())
        await message.uncollapse()

    async def test_parent(self, reddit):
        reddit.read_only = False
        message = await reddit.inbox.message("1aogu6u")
        parent = message.parent
        assert isinstance(parent, Message)
        assert parent.fullname == message.parent_id

    async def test_parent__from_inbox_listing(self, reddit):
        reddit.read_only = False
        message = await self.async_next(reddit.inbox.sent(limit=1))
        parent = message.parent
        assert isinstance(parent, Message)
        assert parent.fullname == message.parent_id
        assert not parent._fetched
        with pytest.raises(AttributeError) as excinfo:
            _ = parent.parent
            assert (
                excinfo.value.args[0]
                == "Message must be fetched with `.load()` before accessing the"
                " parent."
            )
        await parent.load()
        assert isinstance(parent.parent, Message)
        assert parent.body

    async def test_reply(self, reddit):
        reddit.read_only = False
        message = await self.async_next(reddit.inbox.messages())
        reply = await message.reply("Message reply")
        assert reply.author == pytest.placeholders.username
        assert reply.body == "Message reply"
        assert reply.first_message_name == message.fullname

    async def test_unblock_subreddit(self, reddit):
        reddit.read_only = False
        message1 = await self.async_next(reddit.inbox.messages(limit=1))
        assert isinstance(message1, SubredditMessage)
        message_fullname = message1.fullname
        await message1.block()
        message2 = await self.async_next(reddit.inbox.messages(limit=1))
        assert message2.fullname == message_fullname
        assert message2.subject == "[message from blocked subreddit]"
        await message2.unblock_subreddit()
        message3 = await self.async_next(reddit.inbox.messages(limit=1))
        assert message3.fullname == message_fullname
        assert message3.subject != "[message from blocked subreddit]"


class TestSubredditMessage(IntegrationTest):
    async def test_mute(self, reddit):
        reddit.read_only = False
        message = SubredditMessage(reddit, _data={"id": "faj6z"})
        await message.mute()

    async def test_unmute(self, reddit):
        reddit.read_only = False
        message = SubredditMessage(reddit, _data={"id": "faj6z"})
        await message.unmute()
