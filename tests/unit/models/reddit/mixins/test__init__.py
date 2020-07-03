import pytest

from asyncpraw.models.reddit.mixins import ThingModerationMixin

from .... import UnitTest


class TestThingModerationMixin(UnitTest):
    async def test_must_be_extended(self):
        with pytest.raises(NotImplementedError):
            await ThingModerationMixin().send_removal_message(
                "public", "title", "message"
            )
