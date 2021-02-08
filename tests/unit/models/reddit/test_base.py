"""Test classes from base.py."""
from copy import deepcopy

from asyncpraw.models.reddit.base import RedditBase

from ... import UnitTest


class TestRedditBase(UnitTest):
    def test_deepcopy(self):
        class Test:
            def __init__(self, attr):
                self.attr = attr

        test_attr = Test("test")
        test_object = Test(test_attr)
        reddit_base = RedditBase(
            self.reddit,
            _data={
                "title": "test_title",
                "STR_FIELD": "title",
                "test_object": test_object,
            },
        )
        result = deepcopy(reddit_base)
        assert isinstance(result, type(reddit_base))
        assert result._reddit == self.reddit
        assert result.test_object != test_object
        assert result.test_object.attr != test_attr
