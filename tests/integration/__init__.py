"""Async PRAW Integration test suite."""
import asyncio
import os

import aiohttp
import pytest
from vcr import VCR

from asyncpraw import Reddit
from tests import HelperMethodMixin

from .utils import (
    CustomPersister,
    CustomSerializer,
    ensure_environment_variables,
    ensure_integration_test,
    filter_access_token,
)

CASSETTES_PATH = "tests/integration/cassettes"
existing_cassettes = set()
used_cassettes = set()


class IntegrationTest(HelperMethodMixin):
    """Base class for Async PRAW integration tests."""

    @pytest.fixture
    def cassette_name(self, request, vcr_cassette_name):
        """Return the name of the cassette to use."""
        marker = request.node.get_closest_marker("cassette_name")
        if marker is None:
            return vcr_cassette_name
        return marker.args[0]

    @pytest.fixture(scope="session", autouse=True)
    def cassette_tracker(self):
        """Return a dictionary to track cassettes."""
        global existing_cassettes
        for cassette in os.listdir(CASSETTES_PATH):
            if cassette.endswith(".json"):
                existing_cassettes.add(cassette.replace(".json", ""))
        yield
        unused_cassettes = existing_cassettes - used_cassettes
        if unused_cassettes and os.getenv("ENSURE_NO_UNUSED_CASSETTES", "0") == "1":
            raise AssertionError(
                f"The following cassettes are unused: {', '.join(unused_cassettes)}."
            )

    @pytest.fixture(autouse=True)
    def read_only(self, reddit):
        """Make reddit instance read-only."""
        # Require tests to explicitly disable read_only mode.
        reddit.read_only = True

    @pytest.fixture
    async def reddit(self, vcr, event_loop: asyncio.AbstractEventLoop):
        """Configure Reddit."""
        reddit_kwargs = {
            "client_id": pytest.placeholders.client_id,
            "client_secret": pytest.placeholders.client_secret,
            "requestor_kwargs": {
                "session": aiohttp.ClientSession(
                    loop=event_loop, headers={"Accept-Encoding": "identity"}
                )
            },
            "user_agent": pytest.placeholders.user_agent,
        }

        if pytest.placeholders.refresh_token != "placeholder_refresh_token":
            reddit_kwargs["refresh_token"] = pytest.placeholders.refresh_token
        else:
            reddit_kwargs["username"] = pytest.placeholders.username
            reddit_kwargs["password"] = pytest.placeholders.password

        async with Reddit(**reddit_kwargs) as reddit_instance:
            yield reddit_instance

    @pytest.fixture(autouse=True)
    def vcr(self):
        """Configure VCR instance."""
        vcr = VCR()
        vcr.before_record_response = filter_access_token
        vcr.cassette_library_dir = CASSETTES_PATH
        vcr.decode_compressed_response = True
        vcr.match_on = ["uri", "method"]
        vcr.path_transformer = VCR.ensure_suffix(".json")
        vcr.register_persister(CustomPersister)
        vcr.register_serializer("custom_serializer", CustomSerializer)
        vcr.serializer = "custom_serializer"
        yield vcr

    @pytest.fixture(autouse=True)
    def vcr_cassette(self, request, vcr, cassette_name):
        """Wrap a test in a VCR.py cassette"""
        global used_cassettes
        kwargs = {}
        marker = request.node.get_closest_marker("recorder_kwargs")
        if marker is not None:
            kwargs.update(kwargs)
        with vcr.use_cassette(cassette_name, **kwargs) as cassette:
            if not cassette.write_protected:
                ensure_environment_variables()
            yield cassette
            ensure_integration_test(cassette)
            used_cassettes.add(cassette_name)
