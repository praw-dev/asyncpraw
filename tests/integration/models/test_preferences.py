from asynctest import mock

from asyncpraw.models import Preferences

from .. import IntegrationTest


class TestPreferences(IntegrationTest):
    def test_creation(self):
        prefs_obj = self.reddit.user.preferences
        assert isinstance(prefs_obj, Preferences)

    async def test_view(self):
        some_known_keys = {
            "allow_clicktracking",
            "default_comment_sort",
            "hide_from_robots",
            "lang",
            "no_profanity",
            "over_18",
            "public_votes",
            "show_link_flair",
        }

        self.reddit.read_only = False
        with self.use_cassette():
            prefs_dict = await self.reddit.user.preferences()
        assert isinstance(prefs_dict, dict)
        assert some_known_keys.issubset(prefs_dict)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update(self, _):
        # boolean params, as many as are reproducible on multiple accounts.
        bool_params = (
            "allow_clicktracking",
            "beta",
            "clickgadget",
            "collapse_read_messages",
            "compress",
            "domain_details",
            "email_digests",
            "email_messages",
            "email_unsubscribe_all",
            "enable_default_themes",
            "hide_downs",
            "hide_from_robots",
            "hide_ups",
            "highlight_controversial",
            "highlight_new_comments",
            "ignore_suggested_sort",
            "legacy_search",
            "live_orangereds",
            "mark_messages_read",
            "monitor_mentions",
            "newwindow",
            "over_18",
            "private_feeds",
            "profile_opt_out",
            "public_votes",
            "research",
            "search_include_over_18",
            "show_flair",
            "show_link_flair",
            "show_stylesheets",
            "show_trending",
            "store_visits",
            "threaded_messages",
            "threaded_modmail",
            "top_karma_subreddits",
            "use_global_defaults",
        )

        int_params = (
            "min_comment_score",
            "min_link_score",
            "num_comments",
            "numsites",
        )
        # parameters that accept string types, and two valid values
        str_params = (
            ("default_comment_sort", ("confidence", "top")),
            ("lang", ("es", "en")),
            ("media", ("on", "off")),
            ("media_preview", ("on", "off")),
        )

        # there are also subreddit-name parameters related to the Gold
        # styling feature. It's impractical to test for that because not every
        # account has Gold, and the test fails on normal accounts.

        self.reddit.read_only = False
        preferences = self.reddit.user.preferences

        with self.use_cassette():

            # test an empty update
            await preferences.update()

            for param in int_params:
                response = await preferences.update(**{param: 1})
                assert response[param] == 1
                response = await preferences.update(**{param: 3})
                assert response[param] == 3
            for param in bool_params:
                response = await preferences.update(**{param: True})
                assert response[param] is True
                response = await preferences.update(**{param: False})
                assert response[param] is False
            for param, values in str_params:
                response = await preferences.update(**{param: values[0]})
                assert response[param] == values[0]
                response = await preferences.update(**{param: values[1]})
                assert response[param] == values[1]
