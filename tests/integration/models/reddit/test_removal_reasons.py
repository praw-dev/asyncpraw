import pytest

from asyncpraw.exceptions import ClientException
from asyncpraw.models import RemovalReason

from ... import IntegrationTest


class TestRemovalReason(IntegrationTest):
    async def test__fetch(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        reason = await subreddit.mod.removal_reasons.get_reason("159bqhvme3rxe")
        assert reason.title.startswith("Be Kind")

    @pytest.mark.cassette_name("TestRemovalReason.test__fetch")
    async def test__fetch_int(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        reason = await subreddit.mod.removal_reasons.get_reason(0)
        assert isinstance(reason, RemovalReason)

    @pytest.mark.cassette_name("TestRemovalReason.test__fetch")
    async def test__fetch_slice(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        reasons = await subreddit.mod.removal_reasons.get_reason(slice(-3, None))
        assert len(reasons) == 3
        for reason in reasons:
            assert isinstance(reason, RemovalReason)

    async def test__fetch__invalid_reason(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        with pytest.raises(ClientException) as excinfo:
            await subreddit.mod.removal_reasons.get_reason("invalid")
        assert (
            str(excinfo.value)
            == f"Subreddit {subreddit} does not have the removal reason invalid"
        )

    async def test_update(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        reason = await subreddit.mod.removal_reasons.get_reason("159bqhvme3rxe")
        await reason.update(title="New Title", message="New Message")

    async def test_update_empty(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        reasons = [reason async for reason in subreddit.mod.removal_reasons]
        reason = reasons[0]
        await reason.update()

    async def test_delete(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        reason = await subreddit.mod.removal_reasons.get_reason("157l8fono55wf")
        await reason.delete()


class TestSubredditRemovalReasons(IntegrationTest):
    async def test__aiter(self, reddit):
        reddit.read_only = False
        count = 0
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        async for reason in subreddit.mod.removal_reasons:
            assert isinstance(reason, RemovalReason)
            count += 1
        assert count > 0

    async def test_add(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        reason = await subreddit.mod.removal_reasons.add(title="Test", message="test")
        assert isinstance(reason, RemovalReason)
