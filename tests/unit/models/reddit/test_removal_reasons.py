import pytest

from asyncpraw.models import RemovalReason, Subreddit
from asyncpraw.models.reddit.removal_reasons import SubredditRemovalReasons

from ... import UnitTest


class TestRemovalReason(UnitTest):
    def test_equality(self):
        reason1 = RemovalReason(
            self.reddit, subreddit=Subreddit(self.reddit, display_name="a"), id="x"
        )
        reason2 = RemovalReason(
            self.reddit, subreddit=Subreddit(self.reddit, display_name="a"), id="2"
        )
        reason3 = RemovalReason(
            self.reddit, subreddit=Subreddit(self.reddit, display_name="b"), id="1"
        )
        reason4 = RemovalReason(
            self.reddit, subreddit=Subreddit(self.reddit, display_name="A"), id="x"
        )
        reason5 = RemovalReason(
            self.reddit,
            subreddit=Subreddit(self.reddit, display_name="a"),
            reason_id="X",
        )
        assert reason1 == reason1
        assert reason1 == "x"
        assert reason2 == reason2
        assert reason3 == reason3
        assert reason1 != reason2
        assert reason1 != reason3
        assert reason1 == reason4
        assert reason1 != reason5

    def test_exception(self):
        with pytest.raises(ValueError):
            RemovalReason(
                self.reddit, subreddit=Subreddit(self.reddit, display_name="a")
            )
        with pytest.raises(ValueError):
            RemovalReason(
                self.reddit,
                subreddit=Subreddit(self.reddit, display_name="a"),
                id="test",
                _data={},
            )
        with pytest.raises(ValueError):
            RemovalReason(
                self.reddit, subreddit=Subreddit(self.reddit, display_name="a"), id=""
            )
        with pytest.raises(ValueError):
            RemovalReason(
                self.reddit,
                subreddit=Subreddit(self.reddit, display_name="a"),
                reason_id="",
            )

    async def test__get(self):
        subreddit = Subreddit(self.reddit, display_name="a")
        removal_reason = await subreddit.mod.removal_reasons.get_reason("a", lazy=True)
        assert isinstance(removal_reason, RemovalReason)

    def test_hash(self):
        reason1 = RemovalReason(
            self.reddit, subreddit=Subreddit(self.reddit, display_name="a"), id="x"
        )
        reason2 = RemovalReason(
            self.reddit, subreddit=Subreddit(self.reddit, display_name="a"), id="2"
        )
        reason3 = RemovalReason(
            self.reddit, subreddit=Subreddit(self.reddit, display_name="b"), id="1"
        )
        reason4 = RemovalReason(
            self.reddit, subreddit=Subreddit(self.reddit, display_name="A"), id="x"
        )
        reason5 = RemovalReason(
            self.reddit,
            subreddit=Subreddit(self.reddit, display_name="a"),
            reason_id="X",
        )
        assert hash(reason1) == hash(reason1)
        assert hash(reason2) == hash(reason2)
        assert hash(reason3) == hash(reason3)
        assert hash(reason1) != hash(reason2)
        assert hash(reason1) != hash(reason3)
        assert hash(reason1) == hash(reason4)
        assert hash(reason1) != hash(reason5)

    def test_repr(self):
        reason = RemovalReason(
            self.reddit, subreddit=Subreddit(self.reddit, display_name="a"), id="x"
        )
        assert repr(reason) == "RemovalReason(id='x')"

    def test_str(self):
        reason = RemovalReason(
            self.reddit, subreddit=Subreddit(self.reddit, display_name="a"), id="x"
        )
        assert str(reason) == "x"


class TestSubredditRemovalReasons(UnitTest):
    def test_repr(self):
        sr = SubredditRemovalReasons(subreddit=Subreddit(self.reddit, display_name="a"))
        assert repr(sr)  # assert it has some repr
