from asyncpraw.models import MoreComments

from ... import UnitTest


class TestComment(UnitTest):
    def test_repr(self, reddit):
        more = MoreComments(reddit, {"children": ["a", "b", "c", "d", "e"], "count": 5})
        assert repr(more) == "<MoreComments count=5, children=['a', 'b', 'c', '...']>"

        more = MoreComments(reddit, {"children": ["a", "b", "c", "d"], "count": 4})
        assert repr(more) == "<MoreComments count=4, children=['a', 'b', 'c', 'd']>"

    def test_equality(self, reddit):
        more = MoreComments(reddit, {"children": ["a", "b", "c", "d"], "count": 4})
        more2 = MoreComments(reddit, {"children": ["a", "b", "c", "d"], "count": 4})
        assert more == more2
        assert more != 5
