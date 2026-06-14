import pickle

import pytest

from asyncpraw.models import RemovalReason, Subreddit
from asyncpraw.models.reddit.removal_reasons import SubredditRemovalReasons

from ... import UnitTest


class TestRemovalReason(UnitTest):
    async def test__get(self, reddit):
        subreddit = Subreddit(reddit, display_name="a")
        removal_reason = await subreddit.mod.removal_reasons.get_reason("a", fetch=False)
        assert isinstance(removal_reason, RemovalReason)

    def test_equality(self, reddit):
        reason1 = RemovalReason(reddit, id="x", subreddit=Subreddit(reddit, display_name="a"))
        reason2 = RemovalReason(reddit, id="2", subreddit=Subreddit(reddit, display_name="a"))
        reason3 = RemovalReason(reddit, id="1", subreddit=Subreddit(reddit, display_name="b"))
        reason4 = RemovalReason(reddit, id="x", subreddit=Subreddit(reddit, display_name="A"))
        reason5 = RemovalReason(
            reddit,
            id="X",
            subreddit=Subreddit(reddit, display_name="a"),
        )
        assert reason1 == reason1
        assert reason1 == "x"
        assert reason2 == reason2
        assert reason3 == reason3
        assert reason1 != reason2
        assert reason1 != reason3
        assert reason1 == reason4
        assert reason1 != reason5

    def test_exception(self, reddit):
        with pytest.raises(ValueError):
            RemovalReason(reddit, subreddit=Subreddit(reddit, display_name="a"))
        with pytest.raises(ValueError):
            RemovalReason(
                reddit,
                _data={},
                id="test",
                subreddit=Subreddit(reddit, display_name="a"),
            )
        with pytest.raises(ValueError):
            RemovalReason(reddit, id="", subreddit=Subreddit(reddit, display_name="a"))
        with pytest.raises(ValueError):
            RemovalReason(
                reddit,
                id="",
                subreddit=Subreddit(reddit, display_name="a"),
            )

    def test_hash(self, reddit):
        reason1 = RemovalReason(reddit, id="x", subreddit=Subreddit(reddit, display_name="a"))
        reason2 = RemovalReason(reddit, id="2", subreddit=Subreddit(reddit, display_name="a"))
        reason3 = RemovalReason(reddit, id="1", subreddit=Subreddit(reddit, display_name="b"))
        reason4 = RemovalReason(reddit, id="x", subreddit=Subreddit(reddit, display_name="A"))
        reason5 = RemovalReason(
            reddit,
            id="X",
            subreddit=Subreddit(reddit, display_name="a"),
        )
        assert hash(reason1) == hash(reason1)
        assert hash(reason2) == hash(reason2)
        assert hash(reason3) == hash(reason3)
        assert hash(reason1) != hash(reason2)
        assert hash(reason1) != hash(reason3)
        assert hash(reason1) == hash(reason4)
        assert hash(reason1) != hash(reason5)

    def test_pickle(self, reddit):
        reason = RemovalReason(reddit, id="x", subreddit=Subreddit(reddit, display_name="a"))
        for level in range(pickle.HIGHEST_PROTOCOL + 1):
            other = pickle.loads(pickle.dumps(reason, protocol=level))
            assert reason == other

    def test_repr(self, reddit):
        reason = RemovalReason(reddit, id="x", subreddit=Subreddit(reddit, display_name="a"))
        assert repr(reason) == "RemovalReason(id='x')"

    def test_str(self, reddit):
        reason = RemovalReason(reddit, id="x", subreddit=Subreddit(reddit, display_name="a"))
        assert str(reason) == "x"


class TestSubredditRemovalReasons(UnitTest):
    def test_repr(self, reddit):
        sr = SubredditRemovalReasons(subreddit=Subreddit(reddit, display_name="a"))
        assert repr(sr)  # assert it has some repr
