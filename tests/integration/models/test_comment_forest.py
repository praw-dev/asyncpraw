"""Test asyncpraw.models.comment_forest."""

import pytest

from asyncpraw.exceptions import DuplicateReplaceException
from asyncpraw.models import Comment, MoreComments

from .. import IntegrationTest


class TestCommentForest(IntegrationTest):
    async def test_replace__all(self, reddit):
        submission = await reddit.submission("3hahrw")
        before_count = len(submission.comments.list())
        skipped = await submission.comments.replace_more(limit=None, threshold=0)
        assert len(skipped) == 0
        assert all(isinstance(x, Comment) for x in submission.comments.list())
        assert all(x.submission == submission for x in submission.comments.list())
        assert before_count < len(submission.comments.list())

    async def test_replace__all_large(self, reddit):
        submission = await reddit.submission("n49rw")
        skipped = await submission.comments.replace_more(limit=None, threshold=0)
        assert len(skipped) == 0
        assert all(isinstance(x, Comment) for x in submission.comments.list())
        assert len(submission.comments.list()) > 1000
        assert len(submission.comments.list()) == len(submission._comments_by_id)

    async def test_replace__all_with_comment_limit(self, reddit):
        submission = await reddit.submission("3hahrw")
        submission.comment_limit = 10
        skipped = await submission.comments.replace_more(limit=None, threshold=0)
        assert len(skipped) == 0
        assert len(submission.comments.list()) >= 500

    async def test_replace__all_with_comment_sort(self, reddit):
        submission = await reddit.submission("3hahrw", fetch=False)
        submission.comment_sort = "old"
        await submission.load()
        skipped = await submission.comments.replace_more(limit=None, threshold=0)
        assert len(skipped) == 0
        assert len(submission.comments.list()) >= 500

    async def test_replace__skip_at_limit(self, reddit):
        submission = await reddit.submission("3hahrw")
        skipped = await submission.comments.replace_more(limit=1)
        assert len(skipped) == 5

    # def test_replace__skip_below_threshold(self, reddit): # FIXME: not currently working; same with praw
    #     submission = await reddit.submission("3hahrw")
    #     before_count = len(submission.comments.list())
    #     skipped = submission.comments.replace_more(limit=16, threshold=5)
    #     assert len(skipped) == 13
    #     assert all(x.count < 5 for x in skipped)
    #     assert all(x.submission == submission for x in skipped)
    #     assert before_count < len(submission.comments.list())

    async def test_replace__skip_all(self, reddit):
        submission = await reddit.submission("3hahrw")
        before_count = len(submission.comments.list())
        skipped = await submission.comments.replace_more(limit=0)
        assert len(skipped) == 6
        assert all(x.submission == submission for x in skipped)
        after_count = len(submission.comments.list())
        assert before_count == after_count + len(skipped)

    async def test_replace__on_comment_from_submission(self, reddit):
        submission = await reddit.submission("3hahrw")
        types = [type(x) for x in submission.comments.list()]
        assert types.count(Comment) == 527
        assert types.count(MoreComments) == 6
        assert (await submission.comments[0].replies.replace_more()) == []
        types = [type(x) for x in submission.comments.list()]
        assert types.count(Comment) == 531
        assert types.count(MoreComments) == 3

    async def test_replace__on_direct_comment(self, reddit):
        comment = await reddit.comment("d8r4im1", fetch=False)
        await comment.refresh()
        assert any(isinstance(x, MoreComments) for x in comment.replies.list())
        await comment.replies.replace_more()
        assert all(isinstance(x, Comment) for x in comment.replies.list())

    async def test_comment_forest_refresh_error(self, reddit):
        reddit.read_only = False
        submission = await self.async_next(reddit.front.top())
        submission.comment_limit = 1
        await submission.load()
        await submission.comments[1].comments()
        with pytest.raises(DuplicateReplaceException):
            await submission.comments.replace_more(limit=1)
