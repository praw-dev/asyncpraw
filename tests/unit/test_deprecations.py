"""This file should be updated as files/classes/functions are deprecated."""

import pytest

from asyncpraw import Reddit
from asyncpraw.models import Comment, Subreddit
from asyncpraw.exceptions import WebSocketException
from asyncpraw.models.reddit.user_subreddit import UserSubreddit

from . import UnitTest


@pytest.mark.filterwarnings("error", category=DeprecationWarning)
class TestDeprecation(UnitTest):
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
