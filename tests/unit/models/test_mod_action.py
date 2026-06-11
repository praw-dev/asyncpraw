from asyncpraw.models import ModAction

from .. import UnitTest


class TestModAction(UnitTest):
    async def test_mod__already_a_redditor(self, reddit):
        action = ModAction(reddit, _data={"id": "abc"})
        redditor = await reddit.redditor("spez", fetch=False)
        action.mod = redditor
        assert action.mod is redditor
