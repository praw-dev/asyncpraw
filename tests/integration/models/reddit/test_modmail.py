import sys
from datetime import datetime

from asynctest import mock

from asyncpraw.models import ModmailMessage, Subreddit

from ... import IntegrationTest


class TestModmailConversation(IntegrationTest):
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_archive(self, _):
        self.reddit.read_only = False
        subreddit = Subreddit(self.reddit, "all")
        with self.use_cassette():
            conversation = await subreddit.modmail("faj6z")
            await conversation.archive()
            conversation = await subreddit.modmail("faj6z")
            assert conversation.state == 2

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_highlight(self, _):
        self.reddit.read_only = False
        subreddit = Subreddit(self.reddit, "all")
        with self.use_cassette():
            conversation = await subreddit.modmail("faj6z")
            await conversation.highlight()
            conversation = await subreddit.modmail("faj6z")
            assert conversation.is_highlighted

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_mute(self, _):
        self.reddit.read_only = False
        subreddit = Subreddit(self.reddit, "all")
        with self.use_cassette():
            conversation = await subreddit.modmail("faj6z")
            await conversation.mute()
            conversation = await subreddit.modmail("faj6z")
            assert conversation.user.mute_status["isMuted"]

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_mute_duration(self, _):
        self.reddit.read_only = False
        subreddit = Subreddit(self.reddit, "all")
        with self.use_cassette():
            conversation = await subreddit.modmail("g46rw")
            await conversation.mute(7)
            conversation = await subreddit.modmail("g46rw")
            assert conversation.user.mute_status["isMuted"]
            if sys.version_info >= (3, 7, 0):
                diff = datetime.fromisoformat(
                    conversation.user.mute_status["endDate"]
                ) - datetime.fromisoformat(conversation.mod_actions[-1].date)
            else:
                end_date = "".join(
                    conversation.user.mute_status["endDate"].rsplit(":", 1)
                )
                start_date = "".join(conversation.mod_actions[-1].date.rsplit(":", 1))
                date_format = "%Y-%m-%dT%H:%M:%S.%f%z"
                diff = datetime.strptime(end_date, date_format) - datetime.strptime(
                    start_date, date_format
                )
            assert diff.days == 6  # 6 here because it is not 7 whole days

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_read(self, _):
        self.reddit.read_only = False
        subreddit = Subreddit(self.reddit, "all")
        with self.use_cassette():
            conversation = await subreddit.modmail("faj6z")
            await conversation.read()

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_read__other_conversations(self, _):
        self.reddit.read_only = False
        subreddit = Subreddit(self.reddit, "all")
        with self.use_cassette():
            conversation = await subreddit.modmail("faj6z")
            other_conversation = await subreddit.modmail("fajcu")
            await conversation.read(other_conversations=[other_conversation])

    async def test_reply(self):
        self.reddit.read_only = False
        subreddit = Subreddit(self.reddit, "all")
        with self.use_cassette():
            conversation = await subreddit.modmail("faj6z")
            reply = await conversation.reply("A message")
        assert isinstance(reply, ModmailMessage)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_unarchive(self, _):
        self.reddit.read_only = False
        subreddit = Subreddit(self.reddit, "all")
        with self.use_cassette():
            conversation = await subreddit.modmail("faj6z")
            await conversation.unarchive()
            conversation = await subreddit.modmail("faj6z")
            assert conversation.state == 1

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_unhighlight(self, _):
        self.reddit.read_only = False
        subreddit = Subreddit(self.reddit, "all")
        with self.use_cassette():
            conversation = await subreddit.modmail("faj6z")
            await conversation.unhighlight()
            conversation = await subreddit.modmail("faj6z")
            assert not conversation.is_highlighted

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_unmute(self, _):
        self.reddit.read_only = False
        subreddit = Subreddit(self.reddit, "all")
        with self.use_cassette():
            conversation = await subreddit.modmail("faj6z")
            await conversation.unmute()
            conversation = await subreddit.modmail("faj6z")
            assert not conversation.user.mute_status["isMuted"]

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_unread(self, _):
        self.reddit.read_only = False
        subreddit = Subreddit(self.reddit, "all")
        with self.use_cassette():
            conversation = await subreddit.modmail("faj6z")
            await conversation.unread()
            conversation = await subreddit.modmail("faj6z")
            assert conversation.last_unread is not None
