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
        reason1 = RemovalReason(
            reddit, subreddit=Subreddit(reddit, display_name="a"), id="x"
        )
        reason2 = RemovalReason(
            reddit, subreddit=Subreddit(reddit, display_name="a"), id="2"
        )
        reason3 = RemovalReason(
            reddit, subreddit=Subreddit(reddit, display_name="b"), id="1"
        )
        reason4 = RemovalReason(
            reddit, subreddit=Subreddit(reddit, display_name="A"), id="x"
        )
        reason5 = RemovalReason(
            reddit,
            subreddit=Subreddit(reddit, display_name="a"),
            id="X",
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
                subreddit=Subreddit(reddit, display_name="a"),
                id="test",
                _data={},
            )
        with pytest.raises(ValueError):
            RemovalReason(reddit, subreddit=Subreddit(reddit, display_name="a"), id="")
        with pytest.raises(ValueError):
            RemovalReason(
                reddit,
                subreddit=Subreddit(reddit, display_name="a"),
                id="",
            )

    def test_hash(self, reddit):
        reason1 = RemovalReason(
            reddit, subreddit=Subreddit(reddit, display_name="a"), id="x"
        )
        reason2 = RemovalReason(
            reddit, subreddit=Subreddit(reddit, display_name="a"), id="2"
        )
        reason3 = RemovalReason(
            reddit, subreddit=Subreddit(reddit, display_name="b"), id="1"
        )
        reason4 = RemovalReason(
            reddit, subreddit=Subreddit(reddit, display_name="A"), id="x"
        )
        reason5 = RemovalReason(
            reddit,
            subreddit=Subreddit(reddit, display_name="a"),
            id="X",
        )
        assert hash(reason1) == hash(reason1)
        assert hash(reason2) == hash(reason2)
        assert hash(reason3) == hash(reason3)
        assert hash(reason1) != hash(reason2)
        assert hash(reason1) != hash(reason3)
        assert hash(reason1) == hash(reason4)
        assert hash(reason1) != hash(reason5)

    def test_repr(self, reddit):
        reason = RemovalReason(
            reddit, subreddit=Subreddit(reddit, display_name="a"), id="x"
        )
        assert repr(reason) == "RemovalReason(id='x')"

    def test_str(self, reddit):
        reason = RemovalReason(
            reddit, subreddit=Subreddit(reddit, display_name="a"), id="x"
        )
        assert str(reason) == "x"


class TestSubredditRemovalReasons(UnitTest):
    def test_repr(self, reddit):
        sr = SubredditRemovalReasons(subreddit=Subreddit(reddit, display_name="a"))
        assert repr(sr)  # assert it has some repr
