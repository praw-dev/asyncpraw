import pytest
from asynctest import mock

from asyncpraw.exceptions import ClientException
from asyncpraw.models import RemovalReason

from ... import IntegrationTest


class TestRemovalReason(IntegrationTest):
    @mock.patch("asyncio.sleep", return_value=None)
    async def test__fetch(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            reason = await subreddit.mod.removal_reasons.get_reason("159bqhvme3rxe")
            assert reason.title.startswith("Be Kind")

    @mock.patch("asyncio.sleep", return_value=None)
    async def test__fetch_int(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette("TestRemovalReason.test__fetch"):
            reason = await subreddit.mod.removal_reasons.get_reason(0)
            assert isinstance(reason, RemovalReason)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test__fetch_slice(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette("TestRemovalReason.test__fetch"):
            reasons = await subreddit.mod.removal_reasons.get_reason(slice(-3, None))
            assert len(reasons) == 3
            for reason in reasons:
                assert isinstance(reason, RemovalReason)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test__fetch__invalid_reason(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            with pytest.raises(ClientException) as excinfo:
                await subreddit.mod.removal_reasons.get_reason("invalid")
            assert str(excinfo.value) == (
                f"Subreddit {subreddit} does not have the removal reason invalid"
            )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            reason = await subreddit.mod.removal_reasons.get_reason("159bqhvme3rxe")
            await reason.update(message="New Message", title="New Title")

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update_empty(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            reasons = [reason async for reason in subreddit.mod.removal_reasons]
            reason = reasons[0]
            await reason.update()

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_delete(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            reason = await subreddit.mod.removal_reasons.get_reason("157l8fono55wf")
            await reason.delete()


class TestSubredditRemovalReasons(IntegrationTest):
    @mock.patch("asyncio.sleep", return_value=None)
    async def test__aiter(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            count = 0
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            async for reason in subreddit.mod.removal_reasons:
                assert isinstance(reason, RemovalReason)
                count += 1
            assert count > 0

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_add(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            reason = await subreddit.mod.removal_reasons.add("test", "Test")
            assert isinstance(reason, RemovalReason)
