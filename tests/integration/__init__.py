"""Async PRAW Integration test suite."""

from __future__ import annotations

import asyncio
import base64
import io
import os
from urllib.parse import quote_plus

import niquests

import betamax
import pytest
from betamax.cassette import Cassette, Interaction
from betamax.util import body_io

from niquests import PreparedRequest, Response

from niquests.adapters import AsyncHTTPAdapter
from niquests.utils import _swap_context

try:
    from urllib3 import AsyncHTTPResponse, HTTPHeaderDict
    from urllib3.backend._async import AsyncLowLevelResponse
except ImportError:
    from urllib3_future import AsyncHTTPResponse, HTTPHeaderDict
    from urllib3_future.backend._async import AsyncLowLevelResponse

from asyncpraw import Reddit
from tests import HelperMethodMixin

from ..utils import (
    PrettyJSONSerializer,
    ensure_environment_variables,
    ensure_integration_test,
    filter_access_token,
)

CASSETTES_PATH = "tests/integration/cassettes"
existing_cassettes = set()
used_cassettes = set()


class IntegrationTest(HelperMethodMixin):
    """Base class for Async PRAW integration tests."""

    @pytest.fixture(autouse=True)
    def inject_fake_async_response(self, cassette_name, monkeypatch):
        """betamax does not support Niquests async capabilities. This fixture is made to compensate for this missing feature."""
        cassette_base_dir = os.path.join(os.path.dirname(__file__), "cassettes")
        cassette = Cassette(
            cassette_name,
            serialization_format="json",
            cassette_library_dir=cassette_base_dir,
        )
        cassette.match_options.update({"method", "path"})

        def patch_add_urllib3_response(serialized, response, headers):
            """This function is patched so that we can construct a proper async dummy response."""
            if "base64_string" in serialized["body"]:
                body = io.BytesIO(
                    base64.b64decode(serialized["body"]["base64_string"].encode())
                )
            else:
                body = body_io(**serialized["body"])

            async def fake_inner_read(
                *args,
            ) -> tuple[bytes, bool, HTTPHeaderDict | None]:
                """Fake the async iter socket read from AsyncHTTPConnection down in urllib3-future."""
                nonlocal body
                return body.getvalue(), True, None

            # just to get case-insensitive keys
            headers = HTTPHeaderDict(headers)

            # kill recorded "content-encoding" as we store the body already decoded in cassettes.
            # otherwise the http client will try to decode the content.
            if "content-encoding" in headers:
                del headers["content-encoding"]

            fake_llr = AsyncLowLevelResponse(
                method="GET",  # hardcoded, but we don't really care. It does not impact the tests.
                status=response.status_code,
                reason=response.reason,
                headers=headers,
                body=fake_inner_read,
                version=11,
            )

            h = AsyncHTTPResponse(
                body,
                status=response.status_code,
                reason=response.reason,
                headers=headers,
                original_response=fake_llr,
                enforce_content_length=False,
            )

            response.raw = h

        monkeypatch.setattr(
            betamax.util, "add_urllib3_response", patch_add_urllib3_response
        )

        async def fake_send(_, *args, **kwargs) -> Response:
            nonlocal cassette

            prep_request: PreparedRequest = args[0]
            print(prep_request.method, prep_request.url)
            interaction: Interaction | None = cassette.find_match(prep_request)

            if interaction:
                # betamax can generate a requests.Response
                # from a matched interaction.
                # three caveats:
                #   first: not async compatible
                #   second: we need to output niquests.AsyncResponse first
                #   third: the underlying HTTPResponse is sync bound

                resp = interaction.as_response()
                # Niquests have two kind of responses in async mode.
                #   A) Response (in case stream=False)
                #   B) AsyncResponse (in case stream=True)
                _swap_context(resp)

                return resp

            raise Exception("no match in cassettes for this request.")

        AsyncHTTPAdapter.send = fake_send

    @pytest.fixture(autouse=True, scope="session")
    def cassette_tracker(self):
        """Track cassettes to ensure unused cassettes are not uploaded."""
        global existing_cassettes
        for cassette in os.listdir(CASSETTES_PATH):
            existing_cassettes.add(cassette[: cassette.rindex(".")])
        yield
        unused_cassettes = existing_cassettes - used_cassettes
        if unused_cassettes and os.getenv("ENSURE_NO_UNUSED_CASSETTES", "0") == "1":
            raise AssertionError(
                f"The following cassettes are unused: {', '.join(unused_cassettes)}."
            )

    @pytest.fixture(autouse=True)
    def cassette(self, request, recorder, cassette_name):
        """Wrap a test in a Betamax cassette."""
        global used_cassettes
        kwargs = {}
        for marker in request.node.iter_markers("add_placeholder"):
            for key, value in marker.kwargs.items():
                recorder.config.default_cassette_options["placeholders"].append(
                    {"placeholder": f"<{key.upper()}>", "replace": value}
                )
        for marker in request.node.iter_markers("recorder_kwargs"):
            for key, value in marker.kwargs.items():
                #  Don't overwrite existing values since function markers are provided
                #  before class markers.
                kwargs.setdefault(key, value)
        with recorder.use_cassette(cassette_name, **kwargs) as recorder:
            cassette = recorder.current_cassette

            # mimick vrcpy property "write_protected"
            cassette.write_protected = (
                cassette.record_mode == "once" or cassette.record_mode == "none"
            )

            yield recorder

            # ensure_integration_test(cassette)
            used_cassettes.add(cassette_name)

    @pytest.fixture(autouse=True)
    def recorder(self, requestor):
        """Configure Betamax."""
        recorder = betamax.Betamax(requestor)
        recorder.register_serializer(PrettyJSONSerializer)
        with betamax.Betamax.configure() as config:
            config.cassette_library_dir = CASSETTES_PATH
            config.default_cassette_options["serialize_with"] = "prettyjson"
            config.before_record(callback=filter_access_token)
            for key, value in pytest.placeholders.__dict__.items():
                if key == "password":
                    value = quote_plus(value)
                config.define_cassette_placeholder(f"<{key.upper()}>", value)
            yield recorder
            # since placeholders persist between tests
            Cassette.default_cassette_options["placeholders"] = []

    @pytest.fixture
    def cassette_name(self, request):
        """Return the name of the cassette to use."""
        marker = request.node.get_closest_marker("cassette_name")
        if marker is None:
            return (
                f"{request.cls.__name__}.{request.node.name}"
                if request.cls
                else request.node.name
            )
        return marker.args[0]

    @pytest.fixture(autouse=True)
    def read_only(self, reddit):
        """Make the Reddit instance read-only."""
        # Require tests to explicitly disable read_only mode.
        reddit.read_only = True

    @pytest.fixture
    async def reddit(self):
        """Configure Reddit."""
        reddit_kwargs = {
            "client_id": pytest.placeholders.client_id,
            "client_secret": pytest.placeholders.client_secret,
            "requestor_kwargs": {"session": niquests.AsyncSession()},
            "user_agent": pytest.placeholders.user_agent,
        }

        if pytest.placeholders.refresh_token != "placeholder_refresh_token":
            reddit_kwargs["refresh_token"] = pytest.placeholders.refresh_token
        else:
            reddit_kwargs["username"] = pytest.placeholders.username
            reddit_kwargs["password"] = pytest.placeholders.password

        async with Reddit(**reddit_kwargs) as reddit_instance:
            yield reddit_instance
