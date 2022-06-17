from json import dumps

from pytest import raises

from asyncpraw.models import (
    Subreddit,
    SubredditWidgets,
    SubredditWidgetsModeration,
    Widget,
    WidgetModeration,
)
from asyncpraw.models.base import AsyncPRAWBase
from asyncpraw.models.reddit.widgets import WidgetEncoder

from ... import UnitTest


class TestWidgetEncoder(UnitTest):
    def test_bad_encode(self, reddit):
        data = [
            1,
            "two",
            SubredditWidgetsModeration(
                Subreddit(reddit, display_name="subreddit"), reddit
            ),
        ]
        with raises(TypeError):
            dumps(data, cls=WidgetEncoder)  # should throw TypeError

    def test_good_encode(self, reddit):
        data = [
            1,
            "two",
            AsyncPRAWBase(reddit, _data={"_secret": "no", "3": 3}),
            Subreddit(reddit, "four"),
        ]
        assert '[1, "two", {"3": 3}, "four"]' == dumps(data, cls=WidgetEncoder)


class TestWidgets(UnitTest):
    def test_subredditwidgets_mod(self, reddit):
        sw = SubredditWidgets(Subreddit(reddit, "fake_subreddit"))
        assert isinstance(sw.mod, SubredditWidgetsModeration)

    def test_widget_mod(self, reddit):
        w = Widget(reddit, {})
        assert isinstance(w.mod, WidgetModeration)
        assert w.mod.widget == w
