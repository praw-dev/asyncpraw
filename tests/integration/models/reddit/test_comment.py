import pytest

from asyncpraw.exceptions import AsyncPRAWException, ClientException, RedditAPIException
from asyncpraw.models import Comment, Submission

from ... import IntegrationTest


class TestComment(IntegrationTest):
    async def test_attributes(self, reddit):
        comment = await reddit.comment("cklhv0f")
        assert comment.author == "bboe"
        assert comment.body.startswith("Yes it does.")
        assert not comment.is_root
        assert comment.submission == "2gmzqe"

    async def test_award(self, reddit):
        reddit.read_only = False
        award_data = await Comment(reddit, "g7cmlgc").award()
        assert award_data["gildings"]["gid_2"] == 2

    async def test_award__not_enough_coins(self, reddit):
        reddit.read_only = False
        with pytest.raises(RedditAPIException) as excinfo:
            await Comment(reddit, "g7cmlgc").award(
                gild_type="award_2385c499-a1fb-44ec-b9b7-d260f3dc55de"
            )
        exception = excinfo.value
        assert "INSUFFICIENT_COINS_WITH_AMOUNT" == exception.error_type

    async def test_award__self_gild(self, reddit):
        reddit.read_only = False
        with pytest.raises(RedditAPIException) as excinfo:
            await Comment(reddit, "g7cn9xb").award(
                gild_type="award_2385c499-a1fb-44ec-b9b7-d260f3dc55de"
            )
        exception = excinfo.value
        assert "SELF_GILDING_NOT_ALLOWED" == exception.error_type

    async def test_block(self, reddit):
        reddit.read_only = False
        async for item in reddit.inbox.submission_replies():
            if item.author and item.author != pytest.placeholders.username:
                comment = item
                break
        else:
            assert False, "no comment found"
        await comment.block()

    async def test_clear_vote(self, reddit):
        reddit.read_only = False
        comment = await reddit.comment("fwxxs5d")
        await comment.clear_vote()

    async def test_delete(self, reddit):
        reddit.read_only = False
        comment = Comment(reddit, "fx1tgzm")
        await comment.delete()
        comment = await reddit.comment("fx1tgzm")
        assert comment.author is None
        assert comment.body == "[deleted]"

    async def test_disable_inbox_replies(self, reddit):
        reddit.read_only = False
        comment = Comment(reddit, "fwxxs5d")
        await comment.disable_inbox_replies()

    async def test_downvote(self, reddit):
        reddit.read_only = False
        await Comment(reddit, "fwxxs5d").downvote()

    async def test_edit(self, reddit):
        reddit.read_only = False
        comment = Comment(reddit, "fwxxs5d")
        await comment.edit("New text")
        assert comment.body == "New text"

    async def test_enable_inbox_replies(self, reddit):
        reddit.read_only = False
        comment = Comment(reddit, "fwxxs5d")
        await comment.enable_inbox_replies()

    @pytest.mark.cassette_name("TestComment.test_award")
    async def test_gild(self, reddit):
        reddit.read_only = False
        award_data = await Comment(reddit, "g7cmlgc").gild()
        assert award_data["gildings"]["gid_2"] == 2

    async def test_invalid(self, reddit):
        with pytest.raises(AsyncPRAWException) as excinfo:
            await reddit.comment("0")
        assert excinfo.value.args[0].startswith("No data returned for comment")

    async def test_mark_read(self, reddit):
        reddit.read_only = False
        comment = await self.async_next(reddit.inbox.unread())
        assert isinstance(comment, Comment)
        await comment.mark_read()

    async def test_mark_unread(self, reddit):
        reddit.read_only = False
        comment = await self.async_next(reddit.inbox.comment_replies())
        await comment.mark_unread()

    async def test_notes(self, reddit):
        reddit.read_only = False
        comment = await reddit.comment("id4adsw")
        note = await comment.mod.create_note(label="HELPFUL_USER", note="test note")
        notes = await self.async_list(comment.mod.author_notes())
        assert note in notes
        assert notes[notes.index(note)].user == comment.author

    async def test_parent__chain(self, reddit):
        comment = Comment(reddit, "dkk4qjd")
        counter = 0
        await comment.refresh()
        parent = await comment.parent()
        while parent != comment.submission:
            if counter % 9 == 0:
                await parent.refresh()
            counter += 1
            parent = await parent.parent()

    async def test_parent__comment(self, reddit):
        comment = Comment(reddit, "cklhv0f")
        parent = await comment.parent()
        await parent.refresh()
        assert comment in parent.replies
        assert isinstance(parent, Comment)
        assert parent.fullname == comment.parent_id

    async def test_parent__comment_from_forest(self, reddit):
        submission = await reddit.submission("2gmzqe")
        comment = submission.comments[0].replies[0]
        parent = await comment.parent()
        assert comment in parent.replies
        assert isinstance(parent, Comment)
        assert parent.fullname == comment.parent_id

    async def test_parent__from_replies(self, reddit):
        reddit.read_only = False
        comment = await self.async_next(reddit.inbox.comment_replies())
        parent = await comment.parent()
        assert isinstance(parent, Comment)
        assert parent.fullname == comment.parent_id

    async def test_parent__submission(self, reddit):
        comment = Comment(reddit, "cklfmye")
        parent = await comment.parent()
        await parent.load()
        assert comment in parent.comments
        assert isinstance(parent, Submission)
        assert parent.fullname == comment.parent_id

    async def test_refresh(self, reddit):
        comment = await reddit.comment("d81vwef")
        assert len(comment.replies) == 0
        await comment.refresh()
        assert len(comment.replies) > 0

    async def test_refresh__deleted_comment(self, reddit):
        with pytest.raises(ClientException) as excinfo:
            await Comment(reddit, "d7ltvl0").refresh()
        assert (
            "This comment does not appear to be in the comment tree",
        ) == excinfo.value.args

    async def test_refresh__raises_exception(self, reddit):
        with pytest.raises(ClientException) as excinfo:
            await Comment(reddit, "fx1tgzm").refresh()
        assert (
            "This comment does not appear to be in the comment tree",
        ) == excinfo.value.args

    async def test_refresh__removed_comment(self, reddit):
        with pytest.raises(ClientException) as excinfo:
            await Comment(reddit, "fx1hmwb").refresh()
        assert (
            "This comment does not appear to be in the comment tree",
        ) == excinfo.value.args

    async def test_refresh__twice(self, reddit):
        comment = await Comment(reddit, "d81vwef").refresh()
        await comment.refresh()

    async def test_refresh__with_reply_sort_and_limit(self, reddit):
        comment = Comment(reddit, "e4j4830")
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

    async def test_reply(self, reddit):
        reddit.read_only = False
        parent_comment = Comment(reddit, "fx1ec2p")
        comment = await parent_comment.reply("Comment reply")
        assert comment.author == pytest.placeholders.username
        assert comment.body == "Comment reply"
        assert not comment.is_root
        assert comment.parent_id == parent_comment.fullname

    # async def test_reply__none(self, reddit): # TODO: I have not been able to reproduce this again; same with praw
    #     reddit.read_only = False
    #     comment = Comment(reddit, "fx1rxr1")
    #     reply = await comment.reply("TEST")
    #     assert reply is None

    async def test_report(self, reddit):
        reddit.read_only = False
        await Comment(reddit, "fx1it87").report("custom")

    async def test_save(self, reddit):
        reddit.read_only = False
        await Comment(reddit, "fx19hsi").save(category="foo")

    async def test_unsave(self, reddit):
        reddit.read_only = False
        await Comment(reddit, "fx19hsi").unsave()

    async def test_upvote(self, reddit):
        reddit.read_only = False
        await Comment(reddit, "fx19hsi").upvote()


class TestCommentModeration(IntegrationTest):
    async def test_add_removal_reason(self, reddit):
        reddit.read_only = False
        comment = await reddit.comment("fx1jgsp")
        await comment.mod.remove()
        await comment.mod._add_removal_reason(
            mod_note="Blah", reason_id="157l6k4g6s365"
        )

    async def test_add_removal_reason_without_id(self, reddit):
        reddit.read_only = False
        comment = await reddit.comment("fx1jgsp")
        await comment.mod.remove()
        await comment.mod._add_removal_reason(mod_note="Test")

    async def test_add_removal_reason_without_id_or_note(self, reddit):
        reddit.read_only = False
        with pytest.raises(ValueError) as excinfo:
            comment = await reddit.comment("fx1jgsp")
            await comment.mod.remove()
            await comment.mod._add_removal_reason()
        assert excinfo.value.args[0].startswith("mod_note cannot be blank")

    async def test_approve(self, reddit):
        reddit.read_only = False
        await Comment(reddit, "fx1jgsp").mod.approve()

    async def test_distinguish(self, reddit):
        reddit.read_only = False
        await Comment(reddit, "fy79crc").mod.distinguish()

    async def test_distinguish__sticky(self, reddit):
        reddit.read_only = False
        await Comment(reddit, "fy79crc").mod.distinguish(sticky=True)

    async def test_ignore_reports(self, reddit):
        reddit.read_only = False
        await Comment(reddit, "fx1jgsp").mod.ignore_reports()

    async def test_lock(self, reddit):
        reddit.read_only = False
        await Comment(reddit, "fx1jgsp").mod.lock()

    async def test_remove(self, reddit):
        reddit.read_only = False
        await Comment(reddit, "fx1jgsp").mod.remove(spam=True)

    async def test_remove_with_reason_id(self, reddit):
        reddit.read_only = False
        await Comment(reddit, "fx1jgsp").mod.remove(reason_id="157l6k4g6s365")

    async def test_send_removal_message(self, reddit):
        reddit.read_only = False
        comment = await reddit.comment("fx1jgsp")
        mod = comment.mod
        await mod.remove()
        message = "message"
        res = [
            await mod.send_removal_message(message=message, title="title", type=type)
            for type in ("public", "private", "private_exposed")
        ]
        assert isinstance(res[0], Comment)
        assert res[0].parent_id == f"t1_{comment.id}"
        assert res[0].body == message
        assert res[1] is None
        assert res[2] is None

    async def test_send_removal_message__error(self, reddit):
        reddit.read_only = False
        comment = await reddit.comment("fx1jgsp")
        await comment.mod.remove()
        with pytest.raises(RedditAPIException) as excinfo:
            await comment.mod.send_removal_message(message="message", title="a" * 51)
        exception = excinfo.value
        assert "title" == exception.field
        assert "TOO_LONG" == exception.error_type

    async def test_show(self, reddit):
        reddit.read_only = False
        await Comment(reddit, "fx1jgsp").mod.show()

    async def test_undistinguish(self, reddit):
        reddit.read_only = False
        await Comment(reddit, "fy79crc").mod.undistinguish()

    async def test_unignore_reports(self, reddit):
        reddit.read_only = False
        await Comment(reddit, "fx1jgsp").mod.unignore_reports()

    async def test_unlock(self, reddit):
        reddit.read_only = False
        await Comment(reddit, "fx1jgsp").mod.unlock()
