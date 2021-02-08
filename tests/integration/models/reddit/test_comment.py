import pytest
from asynctest import mock

from asyncpraw.exceptions import AsyncPRAWException, ClientException, RedditAPIException
from asyncpraw.models import Comment, Submission

from ... import IntegrationTest


class TestComment(IntegrationTest):
    async def test_attributes(self):
        with self.use_cassette():
            comment = await self.reddit.comment("cklhv0f")
            assert comment.author == "bboe"
            assert comment.body.startswith("Yes it does.")
            assert not comment.is_root
            assert comment.submission == "2gmzqe"

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_block(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            comment = None
            async for item in self.reddit.inbox.submission_replies():
                if item.author and item.author != pytest.placeholders.username:
                    comment = item
                    break
            else:
                assert False, "no comment found"
            await comment.block()

    async def test_clear_vote(self):
        self.reddit.read_only = False
        with self.use_cassette():
            comment = await self.reddit.comment("fwxxs5d")
            await comment.clear_vote()

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_delete(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            comment = Comment(self.reddit, "fx1tgzm")
            await comment.delete()
            comment = await self.reddit.comment("fx1tgzm")
            assert comment.author is None
            assert comment.body == "[deleted]"

    async def test_disable_inbox_replies(self):
        self.reddit.read_only = False
        comment = Comment(self.reddit, "fwxxs5d")
        with self.use_cassette():
            await comment.disable_inbox_replies()

    async def test_downvote(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Comment(self.reddit, "fwxxs5d").downvote()

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_edit(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            comment = Comment(self.reddit, "fwxxs5d")
            await comment.edit("New text")
            assert comment.body == "New text"

    async def test_enable_inbox_replies(self):
        self.reddit.read_only = False
        comment = Comment(self.reddit, "fwxxs5d")
        with self.use_cassette():
            await comment.enable_inbox_replies()

    async def test_award(self):
        self.reddit.read_only = False
        with self.use_cassette():
            award_data = await Comment(self.reddit, "g7cmlgc").award()
            assert award_data["gildings"]["gid_2"] == 2

    async def test_award__not_enough_coins(self):
        self.reddit.read_only = False
        with self.use_cassette():
            with pytest.raises(RedditAPIException) as excinfo:
                await Comment(self.reddit, "g7cmlgc").award(
                    gild_type="award_2385c499-a1fb-44ec-b9b7-d260f3dc55de"
                )
            exception = excinfo.value
            assert "INSUFFICIENT_COINS_WITH_AMOUNT" == exception.error_type

    async def test_award__self_gild(self):
        self.reddit.read_only = False
        with self.use_cassette():
            with pytest.raises(RedditAPIException) as excinfo:
                await Comment(self.reddit, "g7cn9xb").award(
                    gild_type="award_2385c499-a1fb-44ec-b9b7-d260f3dc55de"
                )
            exception = excinfo.value
            assert "SELF_GILDING_NOT_ALLOWED" == exception.error_type

    async def test_gild(self):
        self.reddit.read_only = False
        with self.use_cassette("TestComment.test_award"):
            award_data = await Comment(self.reddit, "g7cmlgc").gild()
            assert award_data["gildings"]["gid_2"] == 2

    async def test_invalid(self):
        with self.use_cassette():
            with pytest.raises(AsyncPRAWException) as excinfo:
                await self.reddit.comment("0")
            assert excinfo.value.args[0].startswith("No data returned for comment")

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_mark_read(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            comment = await self.async_next(self.reddit.inbox.unread())
            assert isinstance(comment, Comment)
            await comment.mark_read()

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_mark_unread(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            comment = await self.async_next(self.reddit.inbox.comment_replies())
            await comment.mark_unread()

    async def test_parent__comment(self):
        comment = Comment(self.reddit, "cklhv0f")
        with self.use_cassette():
            parent = await comment.parent()
            await parent.refresh()
            assert comment in parent.replies
        assert isinstance(parent, Comment)
        assert parent.fullname == comment.parent_id

    async def test_parent__chain(self):
        comment = Comment(self.reddit, "dkk4qjd")
        counter = 0
        with self.use_cassette():
            await comment.refresh()
            parent = await comment.parent()
            while parent != comment.submission:
                if counter % 9 == 0:
                    await parent.refresh()
                counter += 1
                parent = await parent.parent()

    async def test_parent__comment_from_forest(self):
        with self.use_cassette():
            submission = await self.reddit.submission("2gmzqe")
            comments = await submission.comments()
            comment = comments[0].replies[0]
            parent = await comment.parent()
        assert comment in parent.replies
        assert isinstance(parent, Comment)
        assert parent.fullname == comment.parent_id

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_parent__from_replies(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            comment = await self.async_next(self.reddit.inbox.comment_replies())
            parent = await comment.parent()
        assert isinstance(parent, Comment)
        assert parent.fullname == comment.parent_id

    async def test_parent__submission(self):
        comment = Comment(self.reddit, "cklfmye")
        with self.use_cassette():
            parent = await comment.parent()
            parent_comments = await parent.comments()
            assert comment in parent_comments
        assert isinstance(parent, Submission)
        assert parent.fullname == comment.parent_id

    async def test_refresh(self):
        with self.use_cassette():
            comment = await self.reddit.comment("d81vwef")
            assert len(comment.replies) == 0
            await comment.refresh()
            assert len(comment.replies) > 0

    async def test_refresh__raises_exception(self):
        with self.use_cassette():
            with pytest.raises(ClientException) as excinfo:
                await Comment(self.reddit, "fx1tgzm").refresh()
        assert (
            "This comment does not appear to be in the comment tree",
        ) == excinfo.value.args

    async def test_refresh__twice(self):
        with self.use_cassette():
            comment = await Comment(self.reddit, "d81vwef").refresh()
            await comment.refresh()

    async def test_refresh__deleted_comment(self):
        with self.use_cassette():
            with pytest.raises(ClientException) as excinfo:
                await Comment(self.reddit, "d7ltvl0").refresh()
        assert (
            "This comment does not appear to be in the comment tree",
        ) == excinfo.value.args

    async def test_refresh__removed_comment(self):
        with self.use_cassette():
            with pytest.raises(ClientException) as excinfo:
                await Comment(self.reddit, "fx1hmwb").refresh()
        assert (
            "This comment does not appear to be in the comment tree",
        ) == excinfo.value.args

    async def test_refresh__with_reply_sort_and_limit(self):
        with self.use_cassette():
            comment = Comment(self.reddit, "e4j4830")
            comment.reply_limit = 4
            comment.reply_sort = "new"
            await comment.refresh()
            replies = comment.replies
        last_created = float("inf")
        for reply in replies:
            if isinstance(reply, Comment):
                if reply.created_utc > last_created:
                    assert False, "sort order incorrect"
                last_created = reply.created_utc
        assert len(comment.replies) == 3

    async def test_reply(self):
        self.reddit.read_only = False
        with self.use_cassette():
            parent_comment = Comment(self.reddit, "fx1ec2p")
            comment = await parent_comment.reply("Comment reply")
            assert comment.author == pytest.placeholders.username
            assert comment.body == "Comment reply"
            assert not comment.is_root
            assert comment.parent_id == parent_comment.fullname

    # async def test_reply__none(self): # TODO: I have not been able to reproduce this again; same with praw
    #     self.reddit.read_only = False
    #     comment = Comment(self.reddit, "fx1rxr1")
    #     with self.use_cassette():
    #         reply = await comment.reply("TEST")
    #     assert reply is None

    async def test_report(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Comment(self.reddit, "fx1it87").report("custom")

    async def test_save(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Comment(self.reddit, "fx19hsi").save("foo")

    async def test_unsave(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Comment(self.reddit, "fx19hsi").unsave()

    async def test_upvote(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Comment(self.reddit, "fx19hsi").upvote()


class TestCommentModeration(IntegrationTest):
    async def test_approve(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Comment(self.reddit, "fx1jgsp").mod.approve()

    async def test_distinguish(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Comment(self.reddit, "fy79crc").mod.distinguish()

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_distinguish__sticky(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            await Comment(self.reddit, "fy79crc").mod.distinguish(sticky=True)

    async def test_ignore_reports(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Comment(self.reddit, "fx1jgsp").mod.ignore_reports()

    async def test_lock(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Comment(self.reddit, "fx1jgsp").mod.lock()

    async def test_remove(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Comment(self.reddit, "fx1jgsp").mod.remove(spam=True)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_remove_with_reason_id(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            await Comment(self.reddit, "fx1jgsp").mod.remove(reason_id="157l6k4g6s365")

    async def test_show(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Comment(self.reddit, "fx1jgsp").mod.show()

    async def test_unlock(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Comment(self.reddit, "fx1jgsp").mod.unlock()

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_add_removal_reason(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            comment = await self.reddit.comment("fx1jgsp")
            await comment.mod.remove()
            await comment.mod._add_removal_reason(
                mod_note="Blah", reason_id="157l6k4g6s365"
            )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_add_removal_reason_without_id(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            comment = await self.reddit.comment("fx1jgsp")
            await comment.mod.remove()
            await comment.mod._add_removal_reason(mod_note="Test")

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_add_removal_reason_without_id_or_note(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            with pytest.raises(ValueError) as excinfo:
                comment = await self.reddit.comment("fx1jgsp")
                await comment.mod.remove()
                await comment.mod._add_removal_reason()
            assert excinfo.value.args[0].startswith("mod_note cannot be blank")

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_send_removal_message(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            comment = await self.reddit.comment("fx1jgsp")
            mod = comment.mod
            await mod.remove()
            message = "message"
            res = [
                await mod.send_removal_message(message, "title", type)
                for type in ("public", "private", "private_exposed")
            ]
            assert isinstance(res[0], Comment)
            assert res[0].parent_id == f"t1_{comment.id}"
            assert res[0].body == message
            assert res[1] is None
            assert res[2] is None

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_send_removal_message__error(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            comment = await self.reddit.comment("fx1jgsp")
            await comment.mod.remove()
            with pytest.raises(RedditAPIException) as excinfo:
                await comment.mod.send_removal_message("message", "a" * 51)
            exception = excinfo.value
            assert "title" == exception.field
            assert "TOO_LONG" == exception.error_type

    async def test_undistinguish(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Comment(self.reddit, "fy79crc").mod.undistinguish()

    async def test_unignore_reports(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Comment(self.reddit, "fx1jgsp").mod.unignore_reports()
