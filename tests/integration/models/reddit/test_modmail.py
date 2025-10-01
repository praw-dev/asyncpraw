from datetime import datetime

from asyncpraw.models import ModmailMessage, Subreddit

from ... import IntegrationTest


class TestModmailConversation(IntegrationTest):
    async def test_archive(self, reddit):
        reddit.read_only = False
        subreddit = Subreddit(reddit, "all")
        conversation = await subreddit.modmail("faj6z")
        await conversation.archive()
        conversation = await subreddit.modmail("faj6z")
        assert conversation.state == 2

    async def test_highlight(self, reddit):
        reddit.read_only = False
        subreddit = Subreddit(reddit, "all")
        conversation = await subreddit.modmail("faj6z")
        await conversation.highlight()
        conversation = await subreddit.modmail("faj6z")
        assert conversation.is_highlighted

    async def test_mute(self, reddit):
        reddit.read_only = False
        subreddit = Subreddit(reddit, "all")
        conversation = await subreddit.modmail("faj6z")
        await conversation.mute()
        conversation = await subreddit.modmail("faj6z")
        assert conversation.user.mute_status["isMuted"]

    async def test_mute_duration(self, reddit):
        reddit.read_only = False
        subreddit = Subreddit(reddit, "all")
        conversation = await subreddit.modmail("g46rw")
        await conversation.mute(num_days=7)
        conversation = await subreddit.modmail("g46rw")
        assert conversation.user.mute_status["isMuted"]
        diff = datetime.fromisoformat(conversation.user.mute_status["endDate"]) - datetime.fromisoformat(
            conversation.mod_actions[-1].date
        )
        assert diff.days == 6  # 6 here because it is not 7 whole days

    async def test_read(self, reddit):
        reddit.read_only = False
        subreddit = Subreddit(reddit, "all")
        conversation = await subreddit.modmail("faj6z")
        await conversation.read()

    async def test_read__other_conversations(self, reddit):
        reddit.read_only = False
        subreddit = Subreddit(reddit, "all")
        conversation = await subreddit.modmail("faj6z")
        other_conversation = await subreddit.modmail("fajcu")
        await conversation.read(other_conversations=[other_conversation])

    async def test_reply(self, reddit):
        reddit.read_only = False
        subreddit = Subreddit(reddit, "all")
        conversation = await subreddit.modmail("faj6z")
        reply = await conversation.reply(body="A message")
        assert isinstance(reply, ModmailMessage)

    async def test_reply__internal(self, reddit):
        reddit.read_only = False
        subreddit = Subreddit(reddit, "all")
        conversation = await subreddit.modmail("1mahha")
        reply = await conversation.reply(internal=True, body="A message")
        assert isinstance(reply, ModmailMessage)

    async def test_unarchive(self, reddit):
        reddit.read_only = False
        subreddit = Subreddit(reddit, "all")
        conversation = await subreddit.modmail("faj6z")
        await conversation.unarchive()
        conversation = await subreddit.modmail("faj6z")
        assert conversation.state == 1

    async def test_unhighlight(self, reddit):
        reddit.read_only = False
        subreddit = Subreddit(reddit, "all")
        conversation = await subreddit.modmail("faj6z")
        await conversation.unhighlight()
        conversation = await subreddit.modmail("faj6z")
        assert not conversation.is_highlighted

    async def test_unmute(self, reddit):
        reddit.read_only = False
        subreddit = Subreddit(reddit, "all")
        conversation = await subreddit.modmail("faj6z")
        await conversation.unmute()
        conversation = await subreddit.modmail("faj6z")
        assert not conversation.user.mute_status["isMuted"]

    async def test_unread(self, reddit):
        reddit.read_only = False
        subreddit = Subreddit(reddit, "all")
        conversation = await subreddit.modmail("faj6z")
        await conversation.unread()
        conversation = await subreddit.modmail("faj6z")
        assert conversation.last_unread is not None
