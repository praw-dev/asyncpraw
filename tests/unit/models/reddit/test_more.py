from asyncpraw.models import MoreComments

from ... import UnitTest


class TestComment(UnitTest):
    def test_repr(self):
        more = MoreComments(
            self.reddit, {"children": ["a", "b", "c", "d", "e"], "count": 5}
        )
        assert repr(more) == "<MoreComments count=5, children=['a', 'b', 'c', '...']>"

        more = MoreComments(self.reddit, {"children": ["a", "b", "c", "d"], "count": 4})
        assert repr(more) == "<MoreComments count=4, children=['a', 'b', 'c', 'd']>"

    def test_equality(self):
        more = MoreComments(self.reddit, {"children": ["a", "b", "c", "d"], "count": 4})
        more2 = MoreComments(
            self.reddit, {"children": ["a", "b", "c", "d"], "count": 4}
        )
        assert more == more2
        assert more != 5
