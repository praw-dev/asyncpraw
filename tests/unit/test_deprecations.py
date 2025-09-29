"""This file should be updated as files/classes/functions are deprecated."""

import pytest

from asyncpraw import Reddit
from asyncpraw.models import Comment, Subreddit
from asyncpraw.exceptions import WebSocketException
from asyncpraw.models.reddit.user_subreddit import UserSubreddit

from . import UnitTest


@pytest.mark.filterwarnings("error", category=DeprecationWarning)
class TestDeprecation(UnitTest):
    async def test_comment_forest_list_async(self, reddit):
        submission = await reddit.submission("1234", fetch=False)
        submission._fetched = True
        submission.comments._comments = []
        with pytest.deprecated_call():
            await submission.comments.list()

    async def test_lazy_argument_rename(self, reddit):
        with pytest.deprecated_call() as warning_info:
            await reddit.submission("1234", lazy=True)
        assert (
            str(warning_info.list[0].message)
            == "The parameter ``lazy`` has been renamed to ``fetch`` and support for"
            " the ``lazy`` parameter will be removed in a future version of Async PRAW."
        )

    async def test_submission_comments_async(self, reddit):
        submission = await reddit.submission("1234", fetch=False)
        submission._fetched = True
        with pytest.deprecated_call():
            await submission.comments()

    async def test_synchronous_context_manager(self, reddit):
        with pytest.deprecated_call() as warning_info:
            with reddit:
                pass
            assert (
                str(warning_info.list[0].message)
                == "Using this class as a synchronous context manager is deprecated and"
                " will be removed in the next release. Use this class as an"
                " asynchronous context manager instead."
            )
