from base64 import urlsafe_b64encode

import pytest
from asyncprawcore import Forbidden, NotFound

from asyncpraw.exceptions import RedditAPIException
from asyncpraw.models import Redditor, WikiPage

from ... import IntegrationTest


def large_content():
    with open("tests/integration/files/too_large.jpg", "rb") as fp:
        return urlsafe_b64encode(fp.read()).decode()


class TestWikiPage(IntegrationTest):
    async def test_content_md(self, reddit):
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        page = await subreddit.wiki.get_page("test")
        assert page.content_md

    async def test_content_md__invalid_name(self, reddit):
        subreddit = await reddit.subreddit("reddit.com")
        page = WikiPage(reddit, subreddit, "\\A")
        with pytest.raises(RedditAPIException) as excinfo:
            await page._fetch()
        assert str(excinfo.value) == "INVALID_PAGE_NAME"

    async def test_discussions(self, reddit):
        subreddit = await reddit.subreddit("reddit.com")
        page = await subreddit.wiki.get_page("search")
        assert await self.async_list(page.discussions())

    async def test_edit(self, reddit):
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)

        reddit.read_only = False
        page = await subreddit.wiki.get_page("test")
        await page.edit(content="PRAW updated")

    @pytest.mark.add_placeholder(content=large_content())
    async def test_edit__usernotes(self, reddit):
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        page = WikiPage(reddit, subreddit, "usernotes")

        reddit.read_only = False
        await page.edit(content=large_content())

    async def test_edit__with_reason(self, reddit):
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)

        reddit.read_only = False
        page = await subreddit.wiki.get_page("test")
        await page.edit(content="PRAW updated with reason", reason="PRAW testing")

    async def test_init__with_revision(self, reddit):
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        page = WikiPage(
            reddit,
            subreddit,
            "index",
            revision="08a4ddfa-c000-11ea-999f-0e1fd5dedea1",
        )
        await page.load()
        assert isinstance(page.revision_by, Redditor)
        assert page.revision_date == 1594091696

    async def test_init__with_revision__author_deleted(self, reddit):
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        page = WikiPage(
            reddit,
            subreddit,
            "config/stylesheet",
            revision="75390fec-8b8f-11e8-8a49-0edb077d29ac",
        )
        await page.load()
        assert page.revision_by is None

    async def test_invalid_page(self, reddit):
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        with pytest.raises(NotFound):
            await subreddit.wiki.get_page("invalid")

    async def test_revision_by(self, reddit):
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        page = await subreddit.wiki.get_page("index")
        assert isinstance(page.revision_by, Redditor)

    async def test_revision(self, reddit):
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        revision_id = "08a4ddfa-c000-11ea-999f-0e1fd5dedea1"
        page = await subreddit.wiki.get_page("index")
        revision = await page.revision(revision_id)
        assert len(revision.content_md) > 0

    async def test_revisions(self, reddit):
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        count = 0
        page = await subreddit.wiki.get_page("index")
        async for revision in page.revisions(limit=None):
            count += 1
            assert isinstance(revision["author"], Redditor)
            assert isinstance(revision["page"], WikiPage)
        assert count > 0

    async def test_revisions__author_deleted(self, reddit):
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        page = await subreddit.wiki.get_page("config/submit_text")
        assert any(
            [revision["author"] is None async for revision in page.revisions(limit=10)]
        )


class TestWikiPageModeration(IntegrationTest):
    async def test_add(self, reddit):
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)

        reddit.read_only = False
        page = await subreddit.wiki.get_page("index")
        await page.mod.add("Lil_SpazTest")

    async def test_remove(self, reddit):
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)

        reddit.read_only = False
        page = await subreddit.wiki.get_page("index")
        await page.mod.remove("Lil_SpazTest")

    async def test_revert(self, reddit):
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        page = WikiPage(reddit, subreddit, "test")

        reddit.read_only = False
        revision_id = (await self.async_next(page.revisions(limit=1)))["id"]
        revision = await page.revision(revision_id)
        await revision.mod.revert()

    async def test_revert_css_fail(self, reddit):
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)

        reddit.read_only = False
        page = await subreddit.wiki.get_page("config/stylesheet")
        await subreddit.stylesheet.upload(
            name="css-revert-fail",
            image_path="tests/integration/files/icon.jpg",
        )
        await page.edit(content="div {background: url(%%css-revert-fail%%)}")
        revision_id = (await self.async_next(page.revisions(limit=1)))["id"]
        await subreddit.stylesheet.delete_image("css-revert-fail")
        with pytest.raises(Forbidden) as exc:
            revision = await page.revision(revision_id)
            await revision.mod.revert()
        assert await exc.value.response.json() == {
            "reason": "INVALID_CSS",
            "message": "Forbidden",
            "explanation": "%(css_error)s",
        }

    async def test_settings(self, reddit):
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)

        reddit.read_only = False
        page = await subreddit.wiki.get_page("index")
        settings = await page.mod.settings()
        assert {"editors": [], "listed": True, "permlevel": 0} == settings

    async def test_update(self, reddit):
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)

        reddit.read_only = False
        page = await subreddit.wiki.get_page("index")
        updated = await page.mod.update(listed=False, permlevel=1)
        assert {"editors": [], "listed": False, "permlevel": 1} == updated
