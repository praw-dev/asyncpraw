"""Test asyncpraw.objector."""
import pytest

from asyncpraw.exceptions import RedditAPIException
from asyncpraw.models import Submission

from . import IntegrationTest


class TestObjector(IntegrationTest):
    async def test_raise_api_exception(self):
        message = "USER_REQUIRED: 'Please log in to do that.'"
        with self.use_cassette():
            submission = Submission(self.reddit, "4b536h")
            with pytest.raises(RedditAPIException) as excinfo:
                await submission.mod.approve()
            assert excinfo.value.items[0].error_type == "USER_REQUIRED"
            assert str(excinfo.value.items[0]) == message
