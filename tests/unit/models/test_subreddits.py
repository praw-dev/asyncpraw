"""Test asyncpraw.models.subreddits."""
import pytest

from .. import UnitTest


class TestSubreddits(UnitTest):
    async def test_recommended__invalid_omit_subreddits(self):
        with pytest.raises(TypeError) as excinfo:
            await self.reddit.subreddits.recommended(["earthporn"], "invalid")
        assert str(excinfo.value) == "omit_subreddits must be a list or None"

    async def test_recommended__invalid_subreddits(self):
        with pytest.raises(TypeError) as excinfo:
            await self.reddit.subreddits.recommended("earthporn")
        assert str(excinfo.value) == "subreddits must be a list"

    def test_search__params_not_modified(self):
        params = {"dummy": "value"}
        generator = self.reddit.subreddits.search(None, params=params)
        assert generator.params["dummy"] == "value"
        assert params == {"dummy": "value"}
