"""Test asyncpraw.models.comment_forest."""
import pytest
from asynctest import mock

from asyncpraw.exceptions import DuplicateReplaceException
from asyncpraw.models import Comment, MoreComments, Submission

from .. import IntegrationTest


class TestCommentForest(IntegrationTest):
    def setUp(self):
        super().setUp()
        # Responses do not decode well on travis so manually re-enable gzip.
        self.reddit._core._requestor._http._default_headers["Accept-Encoding"] = "gzip"

    async def test_replace__all(self):
        with self.use_cassette(match_requests_on=["uri", "method", "body"]):
            submission = await self.reddit.submission("3hahrw")
            comments = await submission.comments()
            before_count = len(await comments.list())
            skipped = await comments.replace_more(None, threshold=0)
            assert len(skipped) == 0
            assert all([isinstance(x, Comment) for x in await comments.list()])
            assert all([x.submission == submission for x in await comments.list()])
            assert before_count < len(await comments.list())

    async def test_replace__all_large(self):
        with self.use_cassette(match_requests_on=["uri", "method", "body"]):
            submission = Submission(self.reddit, "n49rw")
            comments = await submission.comments()
            skipped = await comments.replace_more(None, threshold=0)
            assert len(skipped) == 0
            assert all([isinstance(x, Comment) for x in await comments.list()])
            assert len(await comments.list()) > 1000
            assert len(await comments.list()) == len(submission._comments_by_id)

    async def test_replace__all_with_comment_limit(self):
        with self.use_cassette(match_requests_on=["uri", "method", "body"]):
            submission = await self.reddit.submission("3hahrw")
            submission.comment_limit = 10
            comments = await submission.comments()
            skipped = await comments.replace_more(None, threshold=0)
            assert len(skipped) == 0
            assert len(await comments.list()) >= 500

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_replace__all_with_comment_sort(self, _):
        with self.use_cassette(match_requests_on=["uri", "method", "body"]):
            submission = await self.reddit.submission("3hahrw")
            submission.comment_sort = "old"
            comments = await submission.comments()
            skipped = await comments.replace_more(None, threshold=0)
            assert len(skipped) == 0
            assert len(await comments.list()) >= 500

    async def test_replace__skip_at_limit(self):
        with self.use_cassette(match_requests_on=["uri", "method", "body"]):
            submission = await self.reddit.submission("3hahrw")
            comments = await submission.comments()
            skipped = await comments.replace_more(1)
            assert len(skipped) == 5

    # async def test_replace__skip_below_threshold(self): # FIXME: not currently working; same with praw
    #     with self.use_cassette(match_requests_on=["uri", "method", "body"]):
    #         submission = Submission(self.reddit, "hkwbo0")
    #         comments = await submission.comments()
    #         before_count = len(await comments.list())
    #         skipped = await comments.replace_more(16, 5)
    #         assert len(skipped) == 6
    #         assert all(x.count < 5 for x in skipped)
    #         assert all(x.submission == submission for x in skipped)
    #         assert before_count < len(await comments.list())

    async def test_replace__skip_all(self):
        with self.use_cassette(match_requests_on=["uri", "method", "body"]):
            submission = await self.reddit.submission("3hahrw")
            comments = await submission.comments()
            before_count = len(await comments.list())
            skipped = await comments.replace_more(limit=0)
            assert len(skipped) == 6
            assert all(x.submission == submission for x in skipped)
            after_count = len(await comments.list())
            assert before_count == after_count + len(skipped)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_replace__on_comment_from_submission(self, _):
        with self.use_cassette(match_requests_on=["uri", "method", "body"]):
            submission = await self.reddit.submission("3hahrw")
            comments = await submission.comments()
            types = [type(x) for x in await comments.list()]
            assert types.count(Comment) == 527
            assert types.count(MoreComments) == 6
            new_comments = await submission.comments()
            replace_more = await new_comments[0].replies.replace_more()
            assert replace_more == []
            types = [type(x) for x in await comments.list()]
            assert types.count(Comment) == 531
            assert types.count(MoreComments) == 3

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_replace__on_direct_comment(self, _):
        with self.use_cassette(match_requests_on=["uri", "method", "body"]):
            comment = await self.reddit.comment("d8r4im1")
            await comment.refresh()
            assert any(
                [isinstance(x, MoreComments) for x in await comment.replies.list()]
            )
            await comment.replies.replace_more()
            assert all([isinstance(x, Comment) for x in await comment.replies.list()])

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_comment_forest_refresh_error(self, _):
        self.reddit.read_only = False
        with self.use_cassette(match_requests_on=["uri", "method", "body"]):
            submission = await self.async_next(self.reddit.front.top())
            # await submission._fetch()
            submission.comment_limit = 1
            comments = await submission.comments()
            await comments[1].comments()
            with pytest.raises(DuplicateReplaceException):
                await comments.replace_more(limit=1)
