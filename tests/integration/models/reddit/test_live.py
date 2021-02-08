"""Test asyncpraw.models.LiveThread"""
import pytest
from asynctest import mock

from asyncpraw.const import API_PATH
from asyncpraw.exceptions import RedditAPIException
from asyncpraw.models import LiveThread, LiveUpdate, Redditor, Submission

from ... import IntegrationTest


class TestLiveUpdate(IntegrationTest):
    async def test_attributes(self):
        thread = LiveThread(self.reddit, "ukaeu1ik4sw5")
        with self.use_cassette():
            update = await thread.get_update("7827987a-c998-11e4-a0b9-22000b6a88d2")
            assert isinstance(update.author, Redditor)
            assert update.author == "umbrae"
            assert update.name == "LiveUpdate_7827987a-c998-11e4-a0b9-22000b6a88d2"
            assert update.body.startswith("Small change")


class TestLiveThread(IntegrationTest):
    async def test_contributor(self):
        thread = LiveThread(self.reddit, "ukaeu1ik4sw5")
        with self.use_cassette():
            contributors = [contributor async for contributor in thread.contributor()]
        assert isinstance(contributors, list)
        assert len(contributors) > 0
        for contributor in contributors:
            assert "permissions" in contributor.__dict__
            assert isinstance(contributor, Redditor)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_contributor__with_manage_permission(self, _):
        # see issue #710 for more info
        self.reddit.read_only = False
        thread = LiveThread(self.reddit, "xyu8kmjvfrww")
        url = API_PATH["live_contributors"].format(id=thread.id)
        with self.use_cassette():
            data = await thread._reddit.request("GET", url)
            contributors = [contributor async for contributor in thread.contributor()]
        assert isinstance(data, dict)
        assert isinstance(contributors, list)
        assert len(contributors) > 0

    async def test_init(self):
        with self.use_cassette():
            thread = await self.reddit.live("ukaeu1ik4sw5", fetch=True)
            assert thread.title == "reddit updates"

    async def test_discussions(self):
        thread = LiveThread(self.reddit, "1595195m6j9zw")
        with self.use_cassette():
            async for submission in thread.discussions(limit=None):
                assert isinstance(submission, Submission)
                assert submission.title == "reddit updates"

    async def test_report(self):
        self.reddit.read_only = False
        thread = LiveThread(self.reddit, "1595195m6j9zw")
        with self.use_cassette():
            await thread.report("spam")

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_updates(self, _):
        thread = LiveThread(self.reddit, "ukaeu1ik4sw5")
        with self.use_cassette():
            async for update in thread.updates(limit=None):
                assert update.thread == thread
        assert update.body.startswith("Small change:")


class TestLiveThreadStream(IntegrationTest):
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_updates(self, _):
        with self.use_cassette():
            live_thread = await self.reddit.live("ta535s1hq2je")
            generator = live_thread.stream.updates()
            for i in range(101):
                assert isinstance(await self.async_next(generator), LiveUpdate)


class TestLiveContributorRelationship(IntegrationTest):
    async def test_accept_invite(self):
        self.reddit.read_only = False
        thread = LiveThread(self.reddit, "1595195m6j9zw")
        with self.use_cassette():
            await thread.contributor.accept_invite()

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_invite__already_invited(self, _):
        self.reddit.read_only = False
        thread = LiveThread(self.reddit, "1595195m6j9zw")
        with self.use_cassette():
            with pytest.raises(RedditAPIException) as excinfo:
                await thread.contributor.invite(pytest.placeholders.username)
        assert excinfo.value.items[0].error_type == "LIVEUPDATE_ALREADY_CONTRIBUTOR"

    async def test_invite__empty_list(self):
        self.reddit.read_only = False
        thread = LiveThread(self.reddit, "1595195m6j9zw")
        with self.use_cassette():
            await thread.contributor.invite(pytest.placeholders.username, [])

    async def test_invite__limited(self):
        self.reddit.read_only = False
        thread = LiveThread(self.reddit, "1595195m6j9zw")
        with self.use_cassette():
            await thread.contributor.invite(
                pytest.placeholders.username, ["manage", "edit"]
            )

    async def test_invite__none(self):
        self.reddit.read_only = False
        thread = LiveThread(self.reddit, "1595195m6j9zw")
        with self.use_cassette():
            await thread.contributor.invite(pytest.placeholders.username, None)

    async def test_invite__redditor(self):
        self.reddit.read_only = False
        thread = LiveThread(self.reddit, "1595195m6j9zw")
        redditor = Redditor(
            self.reddit, _data={"name": pytest.placeholders.username, "id": "3ebyblla"}
        )
        with self.use_cassette():
            await thread.contributor.invite(redditor)

    async def test_leave(self):
        self.reddit.read_only = False
        thread = LiveThread(self.reddit, "1595195m6j9zw")
        with self.use_cassette():
            await thread.contributor.leave()

    async def test_remove__fullname(self):
        self.reddit.read_only = False
        thread = LiveThread(self.reddit, "1595195m6j9zw")
        with self.use_cassette():
            await thread.contributor.remove("t2_3ebyblla")

    async def test_remove__redditor(self):
        self.reddit.read_only = False
        thread = LiveThread(self.reddit, "1595195m6j9zw")
        redditor = Redditor(
            self.reddit, _data={"name": pytest.placeholders.username, "id": "3ebyblla"}
        )
        with self.use_cassette():
            await thread.contributor.remove(redditor)

    async def test_remove_invite__fullname(self):
        self.reddit.read_only = False
        thread = LiveThread(self.reddit, "1595195m6j9zw")
        with self.use_cassette():
            await thread.contributor.remove_invite("t2_3ebyblla")

    async def test_remove_invite__redditor(self):
        self.reddit.read_only = False
        thread = LiveThread(self.reddit, "1595195m6j9zw")
        redditor = Redditor(
            self.reddit, _data={"name": pytest.placeholders.username, "id": "3ebyblla"}
        )
        with self.use_cassette():
            await thread.contributor.remove_invite(redditor)

    async def test_update__empty_list(self):
        self.reddit.read_only = False
        thread = LiveThread(self.reddit, "1595195m6j9zw")
        with self.use_cassette():
            await thread.contributor.update(pytest.placeholders.username, [])

    async def test_update__limited(self):
        self.reddit.read_only = False
        thread = LiveThread(self.reddit, "1595195m6j9zw")
        with self.use_cassette():
            await thread.contributor.update(
                pytest.placeholders.username, ["manage", "edit"]
            )

    async def test_update__none(self):
        self.reddit.read_only = False
        thread = LiveThread(self.reddit, "1595195m6j9zw")
        with self.use_cassette():
            await thread.contributor.update(pytest.placeholders.username, None)

    async def test_update_invite__empty_list(self):
        self.reddit.read_only = False
        thread = LiveThread(self.reddit, "1595195m6j9zw")
        with self.use_cassette():
            await thread.contributor.update_invite(pytest.placeholders.username, [])

    async def test_update_invite__limited(self):
        self.reddit.read_only = False
        thread = LiveThread(self.reddit, "1595195m6j9zw")
        with self.use_cassette():
            await thread.contributor.update_invite(
                pytest.placeholders.username, ["manage", "edit"]
            )

    async def test_update_invite__none(self):
        self.reddit.read_only = False
        thread = LiveThread(self.reddit, "1595195m6j9zw")
        with self.use_cassette():
            await thread.contributor.update_invite(pytest.placeholders.username, None)


class TestLiveThreadContribution(IntegrationTest):
    async def test_add(self):
        self.reddit.read_only = False
        thread = LiveThread(self.reddit, "1595195m6j9zw")
        with self.use_cassette():
            await thread.contrib.add("* `LiveThreadContribution.add() test`")

    async def test_close(self):
        self.reddit.read_only = False
        thread = LiveThread(self.reddit, "1595195m6j9zw")
        with self.use_cassette():
            await thread.contrib.close()

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update__partial_settings(self, _):
        old_settings = {
            "title": "old title",
            "description": "## old description",
            "nsfw": False,
            "resources": "## old resources",
        }
        new_settings = {"title": "new title", "nsfw": True}
        self.reddit.read_only = False
        thread = LiveThread(self.reddit, "1595195m6j9zw")
        with self.use_cassette():
            await thread.contrib.update(**new_settings)
            thread = await self.reddit.live("1595195m6j9zw", fetch=True)
            assert thread.title == new_settings["title"]
            assert thread.description == old_settings["description"]
            assert thread.nsfw == new_settings["nsfw"]
            assert thread.resources == old_settings["resources"]

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update__full_settings(self, _):
        new_settings = {
            "title": "new title 2",
            "description": "## new description 2",
            "nsfw": True,
            "resources": "## new resources 2",
        }
        self.reddit.read_only = False
        thread = LiveThread(self.reddit, "1595195m6j9zw")
        with self.use_cassette():
            await thread.contrib.update(**new_settings)
            thread = await self.reddit.live("1595195m6j9zw", fetch=True)
            assert thread.title == new_settings["title"]
            assert thread.description == new_settings["description"]
            assert thread.nsfw == new_settings["nsfw"]
            assert thread.resources == new_settings["resources"]

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update__other_settings(self, _):
        new_settings = {
            "title": "new title",
            "other1": "other 1",
            "other2": "other 2",
        }
        self.reddit.read_only = False
        thread = LiveThread(self.reddit, "1595195m6j9zw")
        with self.use_cassette():
            await thread.contrib.update(**new_settings)


class TestLiveUpdateContribution(IntegrationTest):
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_remove(self, _):
        self.reddit.read_only = False
        update = LiveUpdate(
            self.reddit, "1595195m6j9zw", "ec5ead40-bf2a-11ea-a3be-0e0d584e0b0b"
        )
        with self.use_cassette():
            await update.contrib.remove()

    async def test_strike(self):
        self.reddit.read_only = False
        update = LiveUpdate(
            self.reddit, "1595195m6j9zw", "3e95636e-bf2c-11ea-9488-0e29bbfe5f37"
        )
        with self.use_cassette():
            await update.contrib.strike()
