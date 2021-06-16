from unittest import mock

import pytest

from asyncpraw.exceptions import RedditAPIException
from tests.integration import IntegrationTest


class TestUserSubredditModeration(IntegrationTest):
    async def test_accept_invite__no_invite(self):
        self.reddit.read_only = False
        with self.use_cassette():
            with pytest.raises(RedditAPIException) as excinfo:
                user = await self.reddit.redditor("Lil_SpazJoekp", fetch=True)
                await user.subreddit.mod.accept_invite()
            assert excinfo.value.items[0].error_type == "NO_INVITE_FOUND"

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            authenticated_user = await self.reddit.user.me()
            before_settings = await authenticated_user.subreddit.mod.settings()
            new_title = f"{before_settings['title']}x"
            new_title = (
                "x"
                if (len(new_title) >= 20 and "placeholder" not in new_title)
                else new_title
            )
            await authenticated_user.subreddit.mod.update(title=new_title)
            authenticated_user = await self.reddit.user.me(use_cache=False)
            assert authenticated_user.subreddit.title == new_title
            after_settings = await authenticated_user.subreddit.mod.settings()

            # Ensure that nothing has changed besides what was specified.
            before_settings["title"] = new_title
            assert before_settings == after_settings
