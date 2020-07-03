"""Test asyncpraw.objector."""
import pytest

from asyncpraw.exceptions import RedditAPIException

from . import IntegrationTest


class TestObjector(IntegrationTest):
    async def test_raise_api_exception(self):
        message = "USER_REQUIRED: 'Please log in to do that.'"
        with self.recorder.use_cassette("TestObjector.test_raise_api_exception"):
            submission = await self.reddit.submission("4b536h")
            with pytest.raises(RedditAPIException) as excinfo:
                await submission.mod.approve()
            assert excinfo.value.items[0].error_type == "USER_REQUIRED"
            assert str(excinfo.value.items[0]) == message
