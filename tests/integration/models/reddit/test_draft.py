import sys

import pytest

if sys.version_info < (3, 8):
    from asynctest import mock
else:
    from unittest import mock

from asyncpraw.exceptions import ClientException
from asyncpraw.models import Draft, Subreddit

from ... import IntegrationTest


class TestDraft(IntegrationTest):
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_create(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)

            draft = await self.reddit.drafts.create(
                title="test", url="https://reddit.com", subreddit=subreddit
            )
            await draft.load()
            assert draft.subreddit == subreddit
            assert draft.title == "test"
            assert not hasattr(draft, "selftext")
            assert draft.url == "https://reddit.com"

            draft = await self.reddit.drafts.create(
                title="test2", selftext="", subreddit=subreddit
            )
            await draft.load()
            assert draft.subreddit == subreddit
            assert draft.selftext == ""
            assert draft.title == "test2"
            assert not hasattr(draft, "url")

            draft = await self.reddit.drafts.create(
                title="test2",
                selftext="selftext",
                subreddit=pytest.placeholders.test_subreddit,
            )
            await draft.load()
            assert draft.subreddit == subreddit
            assert draft.selftext == "selftext"
            assert draft.title == "test2"
            assert not hasattr(draft, "url")

    async def test_delete(self):
        self.reddit.read_only = False
        with self.use_cassette():
            draft = await self.reddit.drafts(
                draft_id="bc647daa-3b83-11ec-a790-7e0ed9af0c88"
            )
            await draft.delete()
            assert len(await self.reddit.drafts()) == 6

    async def test_fetch(self):
        self.reddit.read_only = False
        with self.use_cassette():
            draft = await self.reddit.drafts(
                draft_id="bc647daa-3b83-11ec-a790-7e0ed9af0c88"
            )
            assert draft.title == "title"
            with pytest.raises(ClientException):
                draft = Draft(self.reddit, id="non-existent")
                await draft._fetch()

    async def test_list(self):
        self.reddit.read_only = False
        with self.use_cassette():
            assert len(await self.reddit.drafts()) == 7

    async def test_submit(self):
        self.reddit.read_only = False
        with self.use_cassette():
            total_drafts = len(await self.reddit.drafts())

            draft = await self.reddit.drafts(
                draft_id="9a77f398-3b83-11ec-8890-fa0ad7056e98"
            )
            submission = await draft.submit()
            await submission.load()
            assert submission.title == draft.title
            assert submission.selftext == draft.selftext
            assert submission.subreddit == draft.subreddit
            remaining_drafts = len(await self.reddit.drafts())
            assert remaining_drafts < total_drafts

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_submit__different_subreddit(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            total_drafts = len(await self.reddit.drafts())

            draft = await self.reddit.drafts(
                draft_id="86339940-3b8e-11ec-88a2-fa740ec7656c"
            )
            submission = await draft.submit(
                subreddit=await self.reddit.subreddit(
                    pytest.placeholders.test_subreddit
                )
            )
            await submission.load()
            assert submission.title == draft.title
            assert submission.selftext == draft.selftext
            assert submission.subreddit != draft.subreddit
            remaining_drafts = len(await self.reddit.drafts())
            assert remaining_drafts < total_drafts

            draft = await self.reddit.drafts(
                draft_id="6e9a8e92-3b8e-11ec-8f1e-5291d87604fa"
            )
            submission = await draft.submit(
                subreddit=pytest.placeholders.test_subreddit
            )
            await submission.load()
            assert submission.title == draft.title
            assert submission.selftext == draft.selftext
            assert submission.subreddit != draft.subreddit
            remaining_drafts = len(await self.reddit.drafts())
            assert remaining_drafts < total_drafts

    async def test_submit__different_title(self):
        self.reddit.read_only = False
        with self.use_cassette():
            total_drafts = len(await self.reddit.drafts())

            draft = await self.reddit.drafts(
                draft_id="d3e728f6-3b8d-11ec-a2aa-fa0ad7056e98"
            )
            new_title = "new title"
            submission = await draft.submit(title=new_title)
            await submission.load()
            assert submission.title == new_title != draft.title
            assert submission.selftext == draft.selftext
            assert submission.subreddit == draft.subreddit
            remaining_drafts = len(await self.reddit.drafts())
            assert remaining_drafts < total_drafts

    async def test_update(self):
        self.reddit.read_only = False
        with self.use_cassette():
            draft = await self.reddit.drafts(
                draft_id="98de0118-3b8c-11ec-98a3-764c49cd2e1a"
            )
            assert draft.title == "title"
            await draft.update(
                title="new title", subreddit=pytest.placeholders.test_subreddit
            )
            assert draft.title == "new title"
            assert isinstance(draft.subreddit, Subreddit)
            assert draft.subreddit == pytest.placeholders.test_subreddit
