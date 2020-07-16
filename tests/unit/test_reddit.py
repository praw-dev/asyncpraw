import configparser
import types
from asynctest import mock
from mock import AsyncMock

import pytest
from asyncprawcore import Requestor
from asyncprawcore.exceptions import BadRequest

from asyncpraw import Reddit, __version__
from asyncpraw.config import Config
from asyncpraw.exceptions import ClientException, RedditAPIException
from asyncpraw.models import Comment

from . import UnitTest


class TestReddit(UnitTest):
    REQUIRED_DUMMY_SETTINGS = {
        x: "dummy" for x in ["client_id", "client_secret", "user_agent"]
    }

    @mock.patch("asyncpraw.reddit.update_check", create=True)
    @mock.patch("asyncpraw.reddit.UPDATE_CHECKER_MISSING", False)
    @mock.patch("asyncpraw.reddit.Reddit.update_checked", False)
    def test_check_for_updates(self, mock_update_check):
        Reddit(check_for_updates="1", **self.REQUIRED_DUMMY_SETTINGS)
        assert Reddit.update_checked
        mock_update_check.assert_called_with("asyncpraw", __version__)

    @mock.patch("asyncpraw.reddit.update_check", create=True)
    @mock.patch("asyncpraw.reddit.UPDATE_CHECKER_MISSING", True)
    @mock.patch("asyncpraw.reddit.Reddit.update_checked", False)
    def test_check_for_updates_update_checker_missing(self, mock_update_check):
        Reddit(check_for_updates="1", **self.REQUIRED_DUMMY_SETTINGS)
        assert not Reddit.update_checked
        assert not mock_update_check.called

    def test_comment(self):
        assert Comment(self.reddit, id="cklfmye").id == "cklfmye"

    def test_context_manager(self):
        with Reddit(**self.REQUIRED_DUMMY_SETTINGS) as reddit:
            assert not reddit.config.check_for_updates

    def test_info__invalid_param(self):
        with pytest.raises(TypeError) as excinfo:
            self.reddit.info(None)

        err_str = "Either `fullnames` or `url` must be provided."
        assert str(excinfo.value) == err_str

        with pytest.raises(TypeError) as excinfo:
            self.reddit.info([], "")

        assert excinfo.match("(?i)mutually exclusive")

    def test_invalid_config(self):
        with pytest.raises(ValueError) as excinfo:
            Reddit(timeout="test", **self.REQUIRED_DUMMY_SETTINGS)
        assert (
            excinfo.value.args[0]
            == "An incorrect config type was given for option timeout. The "
            "expected type is int, but the given value is test."
        )
        with pytest.raises(ValueError) as excinfo:
            Reddit(ratelimit_seconds="test", **self.REQUIRED_DUMMY_SETTINGS)
        assert (
            excinfo.value.args[0] == "An incorrect config type was given for option "
            "ratelimit_seconds. The expected type is int, but the given value "
            "is test."
        )

    def test_info__not_list(self):
        with pytest.raises(TypeError) as excinfo:
            self.reddit.info("Let's try a string")

        assert "must be a non-str iterable" in str(excinfo.value)

    def test_live_info__valid_param(self):
        gen = self.reddit.live.info(["dummy", "dummy2"])
        assert isinstance(gen, types.AsyncGeneratorType)

    def test_live_info__invalid_param(self):
        with pytest.raises(TypeError) as excinfo:
            self.reddit.live.info(None)
        assert str(excinfo.value) == "ids must be a list"

    @mock.patch(
        "asyncpraw.Reddit.request",
        side_effect=[
            {"kind": "t2", "data": {"name": "bboe"}},
            {
                "kind": "LabeledMulti",
                "data": {"path": "/user/bboe/m/aa", "name": "aa"},
            },
        ],
    )
    async def test_multireddit(self, _):
        multireddit = await self.reddit.multireddit("bboe", "aa")
        assert multireddit.path == "/user/bboe/m/aa"

    @mock.patch(
        "asyncpraw.Reddit.request",
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
                            "You are doing that too much. Try again in 10 minutes.",
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
                            "APRIL FOOLS FROM REDDIT, TRY AGAIN",
                            "ratelimit",
                        ]
                    ]
                }
            },
            {},
        ],
    )
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_post_ratelimit(self, __, _):
        with pytest.raises(RedditAPIException) as exc:
            await self.reddit.post("test")
        assert (
            exc.value.message == "You are doing that too much. Try again in 5 seconds."
        )
        with pytest.raises(RedditAPIException) as exc2:
            await self.reddit.post("test")
        assert (
            exc2.value.message
            == "You are doing that too much. Try again in 10 minutes."
        )
        with pytest.raises(RedditAPIException) as exc3:
            await self.reddit.post("test")
        assert exc3.value.message == "APRIL FOOLS FROM REDDIT, TRY AGAIN"
        response = await self.reddit.post("test")
        assert response == {}

    def test_read_only__with_authenticated_core(self):
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

    def test_read_only__with_authenticated_core__non_confidential(self):
        with Reddit(
            client_id="dummy",
            client_secret=None,
            redirect_uri="dummy",
            user_agent="dummy",
            refresh_token="dummy",
        ) as reddit:
            assert not reddit.read_only
            reddit.read_only = True
            assert reddit.read_only
            reddit.read_only = False
            assert not reddit.read_only

    def test_read_only__with_script_authenticated_core(self):
        with Reddit(
            password="dummy", username="dummy", **self.REQUIRED_DUMMY_SETTINGS
        ) as reddit:
            assert not reddit.read_only
            reddit.read_only = True
            assert reddit.read_only
            reddit.read_only = False
            assert not reddit.read_only

    def test_read_only__without_trusted_authenticated_core(self):
        with Reddit(
            password=None, username=None, **self.REQUIRED_DUMMY_SETTINGS
        ) as reddit:
            assert reddit.read_only
            with pytest.raises(ClientException):
                reddit.read_only = False
            assert reddit.read_only
            reddit.read_only = True
            assert reddit.read_only

    def test_read_only__without_untrusted_authenticated_core(self):
        required_settings = self.REQUIRED_DUMMY_SETTINGS.copy()
        required_settings["client_secret"] = None
        with Reddit(password=None, username=None, **required_settings) as reddit:
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
                "Required configuration setting '{}' missing.".format(setting)
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
                "Required configuration setting '{}' missing.".format(setting)
            )

    def test_reddit__site_name_no_section(self):
        with pytest.raises(configparser.NoSectionError) as excinfo:
            Reddit("bad_site_name")
        assert "asyncpraw.readthedocs.io" in excinfo.value.message

    @mock.patch("asyncprawcore.sessions.Session")
    async def test_request__badrequest_with_no_json_body(self, mock_session):
        response = mock.Mock(status_code=400)
        response.json.side_effect = ValueError
        mock_session.return_value.request = mock.Mock(
            side_effect=BadRequest(response=response)
        )

        reddit = Reddit(client_id="dummy", client_secret="dummy", user_agent="dummy")
        with pytest.raises(Exception) as excinfo:
            await reddit.request("POST", "/")
        assert str(excinfo.value).startswith("Unexpected BadRequest without json body.")

    async def test_request__json_and_body(self):
        reddit = Reddit(client_id="dummy", client_secret="dummy", user_agent="dummy")
        with pytest.raises(ClientException) as excinfo:
            await reddit.request(
                method="POST", path="/", data={"key": "value"}, json={"key": "value"},
            )
        assert str(excinfo.value).startswith(
            "At most one of `data` and `json` is supported."
        )

    @mock.patch(
        "asyncpraw.Reddit.request",
        side_effect=[
            [
                {
                    "kind": "Listing",
                    "data": {
                        "children": [
                            {"kind": "t3", "data": {"name": "t3_2gmzqe", "url": "url"}}
                        ],
                        "after": None,
                        "before": None,
                    },
                },
                {
                    "kind": "Listing",
                    "data": {"children": [], "after": None, "before": None},
                },
            ]
        ],
    )
    async def test_submission(self, _):
        submission = await self.reddit.submission("2gmzqe")
        assert submission.id == "2gmzqe"

    @mock.patch(
        "asyncpraw.Reddit.request",
        side_effect=[
            {
                "kind": "t5",
                "data": {
                    "isSubscribed": True,
                    "name": "t5_2qizd",
                    "subscribers": 33817,
                    "display_name": "redditdev",
                },
            },
        ],
    )
    async def test_subreddit(self, _):
        subreddit = await self.reddit.subreddit("redditdev")
        assert subreddit.display_name == "redditdev"


class TestRedditCustomRequestor(UnitTest):
    def test_requestor_class(self):
        class CustomRequestor(Requestor):
            pass

        reddit = Reddit(
            client_id="dummy",
            client_secret="dummy",
            password="dummy",
            user_agent="dummy",
            username="dummy",
            requestor_class=CustomRequestor,
        )
        assert isinstance(reddit._core._requestor, CustomRequestor)
        assert not isinstance(self.reddit._core._requestor, CustomRequestor)

        reddit = Reddit(
            client_id="dummy",
            client_secret="dummy",
            user_agent="dummy",
            requestor_class=CustomRequestor,
        )
        assert isinstance(reddit._core._requestor, CustomRequestor)
        assert not isinstance(self.reddit._core._requestor, CustomRequestor)

    async def test_requestor_kwargs(self):
        session = AsyncMock(headers={})
        reddit = Reddit(
            client_id="dummy",
            client_secret="dummy",
            user_agent="dummy",
            requestor_kwargs={"session": session},
        )

        assert reddit._core._requestor._http is session
