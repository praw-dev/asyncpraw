from base64 import urlsafe_b64encode

import pytest
from asyncprawcore import NotFound
from asynctest import mock

from asyncpraw.exceptions import RedditAPIException
from asyncpraw.models import Redditor, WikiPage

from ... import IntegrationTest


class TestWikiPage(IntegrationTest):
    async def test_content_md(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)

        with self.use_cassette():
            page = await subreddit.wiki.get_page("test")
            assert page.content_md

    async def test_content_md__invalid_name(self):
        subreddit = await self.reddit.subreddit("reddit.com")
        page = WikiPage(self.reddit, subreddit, "\\A")

        with self.use_cassette():
            with pytest.raises(RedditAPIException) as excinfo:
                await page._fetch()
            assert str(excinfo.value) == "INVALID_PAGE_NAME"

    async def test_edit(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)

        self.reddit.read_only = False
        with self.use_cassette():
            page = await subreddit.wiki.get_page("test")
            await page.edit("PRAW updated")

    async def test_edit__usernotes(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        page = WikiPage(self.reddit, subreddit, "usernotes")
        with open("tests/integration/files/too_large.jpg", "rb") as fp:
            large_content = urlsafe_b64encode(fp.read()).decode()

        self.reddit.read_only = False
        with self.use_cassette():
            await page.edit(large_content)

    async def test_edit__with_reason(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)

        self.reddit.read_only = False
        with self.use_cassette():
            page = await subreddit.wiki.get_page("test")
            await page.edit("PRAW updated with reason", reason="PRAW testing")

    async def test_init__with_revision(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            page = WikiPage(
                self.reddit,
                subreddit,
                "index",
                revision="08a4ddfa-c000-11ea-999f-0e1fd5dedea1",
            )
            await page.load()
            assert isinstance(page.revision_by, Redditor)
            assert page.revision_date == 1594091696

    async def test_init__with_revision__author_deleted(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        page = WikiPage(
            self.reddit,
            subreddit,
            "config/stylesheet",
            revision="75390fec-8b8f-11e8-8a49-0edb077d29ac",
        )
        with self.use_cassette():
            await page.load()
            assert page.revision_by is None

    async def test_invalid_page(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            with pytest.raises(NotFound):
                await subreddit.wiki.get_page("invalid")

    async def test_revision_by(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)

        with self.use_cassette():
            page = await subreddit.wiki.get_page("index")
            assert isinstance(page.revision_by, Redditor)

    async def test_revision(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        revision_id = "08a4ddfa-c000-11ea-999f-0e1fd5dedea1"

        with self.use_cassette():
            page = await subreddit.wiki.get_page("index")
            revision = await page.revision(revision_id)
            assert len(revision.content_md) > 0

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_revisions(self, _):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)

        with self.use_cassette():
            count = 0
            page = await subreddit.wiki.get_page("index")
            async for revision in page.revisions(limit=None):
                count += 1
                assert isinstance(revision["author"], Redditor)
                assert isinstance(revision["page"], WikiPage)
            assert count > 0

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_revisions__author_deleted(self, _):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)

        with self.use_cassette():
            page = await subreddit.wiki.get_page("config/submit_text")
            assert any(
                [
                    revision["author"] is None
                    async for revision in page.revisions(limit=10)
                ]
            )


class TestWikiPageModeration(IntegrationTest):
    async def test_add(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)

        self.reddit.read_only = False
        with self.use_cassette():
            page = await subreddit.wiki.get_page("index")
            await page.mod.add("Lil_SpazTest")

    async def test_remove(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)

        self.reddit.read_only = False
        with self.use_cassette():
            page = await subreddit.wiki.get_page("index")
            await page.mod.remove("Lil_SpazTest")

    async def test_settings(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)

        self.reddit.read_only = False
        with self.use_cassette():
            page = await subreddit.wiki.get_page("index")
            settings = await page.mod.settings()
        assert {"editors": [], "listed": True, "permlevel": 0} == settings

    async def test_update(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)

        self.reddit.read_only = False
        with self.use_cassette():
            page = await subreddit.wiki.get_page("index")
            updated = await page.mod.update(listed=False, permlevel=1)
        assert {"editors": [], "listed": False, "permlevel": 1} == updated
