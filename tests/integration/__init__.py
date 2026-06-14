"""Async PRAW Integration test suite."""

import asyncio
import copy
import io
import os

import aiohttp
import pytest
from vcr import VCR

from asyncpraw import Reddit
from tests import HelperMethodMixin

from ..utils import (
    CustomPersister,
    CustomSerializer,
    ensure_environment_variables,
    ensure_integration_test,
    filter_access_token,
)

# vcrpy 8 deep-copies each request before matching/recording (vcr.config.before_record_request).
# File-upload tests pass open file handles in the request body, which cannot be deep-copied
# ("cannot pickle 'BufferedReader' instances"). A file handle wraps an OS resource, so copying it
# by reference is the only sane behavior; register that for the file types the tests use.
for _file_type in (io.BufferedReader, io.BufferedRandom, io.FileIO, io.TextIOWrapper):
    copy._deepcopy_dispatch[_file_type] = lambda value, _memo: value

CASSETTES_PATH = "tests/integration/cassettes"
# VCR's ``uri`` matcher compares the full URI as a string, which is sensitive to query
# parameter order. Betamax compared query parameters order-independently, so expand
# ``uri`` into components that use VCR's order-independent ``query`` matcher.
URI_MATCHERS = ["scheme", "host", "port", "path", "query"]
existing_cassettes = set()

used_cassettes = set()


class IntegrationTest(HelperMethodMixin):
    """Base class for Async PRAW integration tests."""

    @pytest.fixture(autouse=True, scope="session")
    def cassette_tracker(self):
        """Track cassettes to ensure unused cassettes are not uploaded."""
        global existing_cassettes
        for cassette in os.listdir(CASSETTES_PATH):
            name = cassette[: cassette.rindex(".")]
            if name:
                existing_cassettes.add(name)
        yield
        unused_cassettes = existing_cassettes - used_cassettes
        if unused_cassettes and os.getenv("ENSURE_NO_UNUSED_CASSETTES", "0") == "1":
            raise AssertionError(f"The following cassettes are unused: {', '.join(unused_cassettes)}.")

    @pytest.fixture(autouse=True)
    def cassette(self, request, recorder, cassette_name):
        """Wrap a test in a VCR cassette."""
        global used_cassettes
        kwargs = {}
        for marker in request.node.iter_markers("add_placeholder"):
            recorder.persister.add_additional_placeholders(marker.kwargs)
        for marker in request.node.iter_markers("recorder_kwargs"):
            for key, value in marker.kwargs.items():
                #  Don't overwrite existing values since function markers are provided
                #  before class markers.
                kwargs.setdefault(key, value)
        if "match_on" in kwargs:
            kwargs["match_on"] = _expand_uri_matcher(kwargs["match_on"])
        with recorder.use_cassette(cassette_name, **kwargs) as cassette:
            if not cassette.write_protected:
                ensure_environment_variables()
            yield cassette
            ensure_integration_test(cassette)
            used_cassettes.add(cassette_name)

    @pytest.fixture(autouse=True)
    def read_only(self, reddit):
        """Make the Reddit instance read-only."""
        # Require tests to explicitly disable read_only mode.
        reddit.read_only = True

    @pytest.fixture(autouse=True)
    def recorder(self):
        """Configure VCR."""
        vcr = VCR()
        vcr.before_record_response = filter_access_token
        vcr.cassette_library_dir = CASSETTES_PATH
        vcr.decode_compressed_response = True
        vcr.match_on = ["method", *URI_MATCHERS]
        vcr.path_transformer = VCR.ensure_suffix(".json")
        vcr.register_persister(CustomPersister)
        vcr.register_serializer("custom_serializer", CustomSerializer)
        vcr.serializer = "custom_serializer"
        yield vcr
        CustomPersister.additional_placeholders = {}

    @pytest.fixture
    def cassette_name(self, request, vcr_cassette_name):
        """Return the name of the cassette to use."""
        marker = request.node.get_closest_marker("cassette_name")
        if marker is None:
            return vcr_cassette_name
        return marker.args[0]

    @pytest.fixture
    async def reddit(self, vcr):
        """Configure Reddit."""
        reddit_kwargs = {
            "client_id": pytest.placeholders.client_id,
            "client_secret": pytest.placeholders.client_secret,
            "requestor_kwargs": {"session": aiohttp.ClientSession(headers={"Accept-Encoding": "identity"})},
            "user_agent": pytest.placeholders.user_agent,
        }

        if pytest.placeholders.refresh_token != "placeholder_refresh_token":
            reddit_kwargs["refresh_token"] = pytest.placeholders.refresh_token
        else:
            reddit_kwargs["username"] = pytest.placeholders.username
            reddit_kwargs["password"] = pytest.placeholders.password

        async with Reddit(**reddit_kwargs) as reddit_instance:
            yield reddit_instance


def _expand_uri_matcher(matchers):
    """Replace the ``uri`` matcher with order-independent component matchers."""
    expanded = []
    for matcher in matchers:
        expanded.extend(URI_MATCHERS if matcher == "uri" else [matcher])
    return expanded
