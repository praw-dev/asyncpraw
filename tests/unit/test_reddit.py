import configparser
import sys
import types

import pytest
from asyncprawcore import Requestor
from asyncprawcore.exceptions import BadRequest

from unittest import mock
from unittest.mock import AsyncMock, MagicMock

from asyncpraw import Reddit, __version__
from asyncpraw.config import Config
from asyncpraw.exceptions import ClientException, RedditAPIException
from asyncpraw.models import Comment
from asyncpraw.util.token_manager import BaseTokenManager

from . import UnitTest


class DummyTokenManager(BaseTokenManager):
    def post_refresh_callback(self, authorizer):
        pass

    def pre_refresh_callback(self, authorizer):
        pass


class TestReddit(UnitTest):
    REQUIRED_DUMMY_SETTINGS = {
        x: "dummy" for x in ["client_id", "client_secret", "user_agent"]
    }

    @mock.patch("asyncpraw.reddit.update_check", create=True)
    async def test_check_for_updates(self, mock_update_check):
        Reddit(check_for_updates="1", **self.REQUIRED_DUMMY_SETTINGS)
        assert Reddit.update_checked
        mock_update_check.assert_called_with("asyncpraw", __version__)

    @mock.patch("asyncpraw.reddit.Reddit.update_checked", False)
    @mock.patch("asyncpraw.reddit.UPDATE_CHECKER_MISSING", True)
    @mock.patch("asyncpraw.reddit.update_check", create=True)
    async def test_check_for_updates_update_checker_missing(self, mock_update_check):
        Reddit(check_for_updates="1", **self.REQUIRED_DUMMY_SETTINGS)
        assert not Reddit.update_checked
        assert not mock_update_check.called

    async def test_close_session(self):
        temp_reddit = Reddit(**self.REQUIRED_DUMMY_SETTINGS)
        assert not temp_reddit.requestor._http.closed
        async with temp_reddit as reddit:
            pass
        assert reddit.requestor._http.closed and temp_reddit.requestor._http.closed

    def test_comment(self, reddit):
        assert Comment(reddit, id="cklfmye").id == "cklfmye"

    def test_conflicting_settings(self):
        with pytest.raises(TypeError) as excinfo:
            Reddit(
                token_manager="dummy",
                refresh_token="dummy",
                **self.REQUIRED_DUMMY_SETTINGS,
            )
        assert (
            str(excinfo.value)
            == "'refresh_token' setting cannot be provided when providing"
            " 'token_manager'"
        )

    async def test_context_manager(self):
        async with Reddit(**self.REQUIRED_DUMMY_SETTINGS) as reddit:
            assert not reddit._validate_on_submit
            assert not reddit.requestor._http.closed
        assert reddit.requestor._http.closed

    def test_info__invalid_param(self, reddit):
        with pytest.raises(TypeError) as excinfo:
            reddit.info(fullnames=None)

        err_str = "Either 'fullnames', 'url', or 'subreddits' must be provided."
        assert str(excinfo.value) == err_str

        with pytest.raises(TypeError) as excinfo:
            reddit.info(fullnames=[], url="")

        assert str(excinfo.value) == err_str

    def test_info__not_list(self, reddit):
        with pytest.raises(TypeError) as excinfo:
            reddit.info(fullnames="Let's try a string")

        assert "must be a non-str iterable" in str(excinfo.value)

    def test_invalid_config(self):
        with pytest.raises(ValueError) as excinfo:
            Reddit(timeout="test", **self.REQUIRED_DUMMY_SETTINGS)
        assert (
            excinfo.value.args[0]
            == "An incorrect config type was given for option timeout. The expected"
            " type is int, but the given value is test."
        )
        with pytest.raises(ValueError) as excinfo:
            Reddit(ratelimit_seconds="test", **self.REQUIRED_DUMMY_SETTINGS)
        assert (
            excinfo.value.args[0]
            == "An incorrect config type was given for option ratelimit_seconds. The"
            " expected type is int, but the given value is test."
        )

    def test_live_info__invalid_param(self, reddit):
        with pytest.raises(TypeError) as excinfo:
            reddit.live.info(None)
        assert str(excinfo.value) == "ids must be a list"

    def test_live_info__valid_param(self, reddit):
        gen = reddit.live.info(["dummy", "dummy2"])
        assert isinstance(gen, types.AsyncGeneratorType)

    async def test_multireddit(self, reddit):
        multireddit = await reddit.multireddit(redditor="bboe", name="aa")
        assert multireddit.path == "/user/bboe/m/aa"

    @mock.patch(
        "asyncpraw.Reddit.request",
        new=AsyncMock(
            side_effect=[
                {
                    "json": {
                        "errors": [
                            [
                                "RATELIMIT",
                                "Some unexpected error message",
                                "ratelimit",
                            ]
                        ]
                    }
                },
            ],
        ),
    )
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_post_ratelimit__invalid_rate_limit_message(self, mock_sleep, reddit):
        with pytest.raises(RedditAPIException) as exception:
            await reddit.post("test")
        assert exception.value.message == "Some unexpected error message"
        mock_sleep.assert_not_called()

    @mock.patch(
        "asyncpraw.Reddit.request",
        new=AsyncMock(
            side_effect=[
                {
                    "json": {
                        "errors": [
                            [
                                "RATELIMIT",
                                "You are doing that too much. Try again in 1 minute.",
                                "ratelimit",
                            ]
                        ]
                    }
                },
            ],
        ),
    )
    async def test_post_ratelimit__over_threshold__minutes(self, reddit):
        with pytest.raises(RedditAPIException) as exception:
            await reddit.post("test")
        assert (
            exception.value.message
            == "You are doing that too much. Try again in 1 minute."
        )

    @mock.patch(
        "asyncpraw.Reddit.request",
        new=AsyncMock(
            side_effect=[
                {
                    "json": {
                        "errors": [
                            [
                                "RATELIMIT",
                                "You are doing that too much. Try again in 6 seconds.",
                                "ratelimit",
                            ]
                        ]
                    }
                },
            ],
        ),
    )
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_post_ratelimit__over_threshold__seconds(self, mock_sleep, reddit):
        with pytest.raises(RedditAPIException) as exception:
            await reddit.post("test")
        assert (
            exception.value.message
            == "You are doing that too much. Try again in 6 seconds."
        )
        mock_sleep.assert_not_called()

    @mock.patch(
        "asyncpraw.Reddit.request",
        new=AsyncMock(
            side_effect=[
                {
                    "json": {
                        "errors": [
                            [
                                "RATELIMIT",
                                "You are doing that too much. Try again in 2 milliseconds.",
                                "ratelimit",
                            ]
                        ]
                    }
                },
                {
                    "json": {
                        "errors": [
                            [
                                "RATELIMIT",
                                "You are doing that too much. Try again in 1 millisecond.",
                                "ratelimit",
                            ]
                        ]
                    }
                },
                {},
            ],
        ),
    )
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_post_ratelimit__under_threshold__milliseconds(
        self, mock_sleep, reddit
    ):
        await reddit.post("test")
        mock_sleep.assert_has_calls([mock.call(1), mock.call(1)])

    @mock.patch(
        "asyncpraw.Reddit.request",
        new=AsyncMock(
            side_effect=[
                {
                    "json": {
                        "errors": [
                            [
                                "RATELIMIT",
                                "You are doing that too much. Try again in 1 minute.",
                                "ratelimit",
                            ]
                        ]
                    }
                },
                {},
            ],
        ),
    )
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_post_ratelimit__under_threshold__minutes(self, mock_sleep, reddit):
        reddit.config.ratelimit_seconds = 60
        await reddit.post("test")
        mock_sleep.assert_has_calls([mock.call(61)])

    @mock.patch(
        "asyncpraw.Reddit.request",
        new=AsyncMock(
            side_effect=[
                {
                    "json": {
                        "errors": [
                            [
                                "RATELIMIT",
                                "You are doing that too much. Try again in 5 seconds.",
                                "ratelimit",
                            ]
                        ]
                    }
                },
                {},
            ],
        ),
    )
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_post_ratelimit__under_threshold__seconds(self, mock_sleep, reddit):
        await reddit.post("test")
        mock_sleep.assert_has_calls([mock.call(6)])

    @mock.patch(
        "asyncpraw.Reddit.request",
        new=AsyncMock(
            side_effect=[
                {
                    "json": {
                        "errors": [
                            [
                                "RATELIMIT",
                                "You are doing that too much. Try again in 5 seconds.",
                                "ratelimit",
                            ]
                        ]
                    }
                },
                {
                    "json": {
                        "errors": [
                            [
                                "RATELIMIT",
                                "You are doing that too much. Try again in 3 seconds.",
                                "ratelimit",
                            ]
                        ]
                    }
                },
                {
                    "json": {
                        "errors": [
                            [
                                "RATELIMIT",
                                "You are doing that too much. Try again in 1 second.",
                                "ratelimit",
                            ]
                        ]
                    }
                },
            ],
        ),
    )
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_post_ratelimit__under_threshold__seconds_failure(
        self, mock_sleep, reddit
    ):
        with pytest.raises(RedditAPIException) as exception:
            await reddit.post("test")
        assert (
            exception.value.message
            == "You are doing that too much. Try again in 1 second."
        )
        mock_sleep.assert_has_calls([mock.call(6), mock.call(4), mock.call(2)])

    async def test_read_only__with_authenticated_core(self):
        async with Reddit(
            token_manager=DummyTokenManager(),
            password=None,
            username=None,
            **self.REQUIRED_DUMMY_SETTINGS,
        ) as reddit:
            assert not reddit.read_only
            reddit.read_only = True
            assert reddit.read_only
            reddit.read_only = False
            assert not reddit.read_only

    def test_read_only__with_authenticated_core__legacy_refresh_token(self):
        with Reddit(
            password=None,
            refresh_token="refresh",
            username=None,
            **self.REQUIRED_DUMMY_SETTINGS,
        ) as reddit:
            assert not reddit.read_only
            reddit.read_only = True
            assert reddit.read_only
            reddit.read_only = False
            assert not reddit.read_only

    async def test_read_only__with_authenticated_core__non_confidential(self):
        async with Reddit(
            token_manager=DummyTokenManager(),
            client_id="dummy",
            client_secret=None,
            redirect_uri="dummy",
            user_agent="dummy",
        ) as reddit:
            assert not reddit.read_only
            reddit.read_only = True
            assert reddit.read_only
            reddit.read_only = False
            assert not reddit.read_only

    def test_read_only__with_authenticated_core__non_confidential__legacy_refresh_token(
        self,
    ):
        with Reddit(
            client_id="dummy",
            client_secret=None,
            redirect_uri="dummy",
            refresh_token="dummy",
            user_agent="dummy",
        ) as reddit:
            assert not reddit.read_only
            reddit.read_only = True
            assert reddit.read_only
            reddit.read_only = False
            assert not reddit.read_only

    async def test_read_only__with_script_authenticated_core(self):
        async with Reddit(
            password="dummy", username="dummy", **self.REQUIRED_DUMMY_SETTINGS
        ) as reddit:
            assert not reddit.read_only
            reddit.read_only = True
            assert reddit.read_only
            reddit.read_only = False
            assert not reddit.read_only

    async def test_read_only__without_trusted_authenticated_core(self):
        async with Reddit(
            password=None, username=None, **self.REQUIRED_DUMMY_SETTINGS
        ) as reddit:
            assert reddit.read_only
            with pytest.raises(ClientException):
                reddit.read_only = False
            assert reddit.read_only
            reddit.read_only = True
            assert reddit.read_only

    async def test_read_only__without_untrusted_authenticated_core(self):
        required_settings = self.REQUIRED_DUMMY_SETTINGS.copy()
        required_settings["client_secret"] = None
        async with Reddit(password=None, username=None, **required_settings) as reddit:
            assert reddit.read_only
            with pytest.raises(ClientException):
                reddit.read_only = False
            assert reddit.read_only
            reddit.read_only = True
            assert reddit.read_only

    def test_reddit__missing_required_settings(self):
        for setting in self.REQUIRED_DUMMY_SETTINGS:
            with pytest.raises(ClientException) as excinfo:
                settings = self.REQUIRED_DUMMY_SETTINGS.copy()
                settings[setting] = Config.CONFIG_NOT_SET
                Reddit(**settings)
            assert str(excinfo.value).startswith(
                f"Required configuration setting {setting!r} missing."
            )
            if setting == "client_secret":
                assert "set to None" in str(excinfo.value)

    def test_reddit__required_settings_set_to_none(self):
        required_settings = self.REQUIRED_DUMMY_SETTINGS.copy()
        del required_settings["client_secret"]
        for setting in required_settings:
            with pytest.raises(ClientException) as excinfo:
                settings = self.REQUIRED_DUMMY_SETTINGS.copy()
                settings[setting] = None
                Reddit(**settings)
            assert str(excinfo.value).startswith(
                f"Required configuration setting {setting!r} missing."
            )

    def test_reddit__site_name_no_section(self):
        with pytest.raises(configparser.NoSectionError) as excinfo:
            Reddit("bad_site_name")
        assert "asyncpraw.readthedocs.io" in excinfo.value.message

    @mock.patch("asyncprawcore.sessions.Session")
    async def test_request__badrequest_with_no_json_body(self, mock_session):
        response = MagicMock(status=400, text=AsyncMock(return_value=""))
        response.json.side_effect = ValueError
        mock_session.return_value.request = MagicMock(
            side_effect=BadRequest(response=response)
        )

        async with Reddit(
            client_id="dummy", client_secret="dummy", user_agent="dummy"
        ) as reddit:
            with pytest.raises(Exception) as excinfo:
                await reddit.request(method="POST", path="/")
        assert str(excinfo.value) == "received 400 HTTP response"

    async def test_request__json_and_body(self):
        async with Reddit(
            client_id="dummy", client_secret="dummy", user_agent="dummy"
        ) as reddit:
            with pytest.raises(ClientException) as excinfo:
                await reddit.request(
                    data={"key": "value"},
                    json={"key": "value"},
                    method="POST",
                    path="/",
                )
            assert str(excinfo.value).startswith(
                "At most one of 'data' or 'json' is supported."
            )

    async def test_submission(self, reddit):
        submission = await reddit.submission("2gmzqe", fetch=False)
        assert submission.id == "2gmzqe"

    async def test_subreddit(self, reddit):
        subreddit = await reddit.subreddit("redditdev")
        assert subreddit.display_name == "redditdev"


class TestRedditCustomRequestor(UnitTest):
    async def test_requestor_class(self, reddit):
        class CustomRequestor(Requestor):
            pass

        async with Reddit(
            requestor_class=CustomRequestor,
            client_id="dummy",
            client_secret="dummy",
            password="dummy",
            user_agent="dummy",
            username="dummy",
        ) as temp_reddit:
            assert isinstance(temp_reddit._core._requestor, CustomRequestor)
        assert not isinstance(reddit._core._requestor, CustomRequestor)

        async with Reddit(
            requestor_class=CustomRequestor,
            client_id="dummy",
            client_secret="dummy",
            user_agent="dummy",
        ) as temp_reddit:
            assert isinstance(temp_reddit._core._requestor, CustomRequestor)
        assert not isinstance(reddit._core._requestor, CustomRequestor)

    def test_requestor_kwargs(self):
        session = AsyncMock(headers={})
        assert (
            Reddit(
                requestor_kwargs={"session": session},
                client_id="dummy",
                client_secret="dummy",
                user_agent="dummy",
            )._core._requestor._http
            is session
        )
