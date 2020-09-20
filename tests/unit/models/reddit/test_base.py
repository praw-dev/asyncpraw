"""Test classes from base.py."""
from copy import deepcopy

from asyncpraw.models.reddit.base import RedditBase
from ... import UnitTest


class TestRedditBase(UnitTest):
    def test_deepcopy(self):
        test_string = "test_string"
        reddit_base = RedditBase(
            None, _data={"title": test_string, "STR_FIELD": "title"}
        )
        result = deepcopy(reddit_base)
        assert isinstance(result, str)
        assert result == test_string
