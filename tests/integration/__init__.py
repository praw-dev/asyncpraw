"""PRAW Integration test suite."""
import inspect
import logging

import aiohttp
import asynctest
import pytest

from asyncpraw import Reddit

from tests.conftest import VCR


class IntegrationTest(asynctest.TestCase):
    """Base class for PRAW integration tests."""

    logger = logging.getLogger(__name__)

    def setUp(self):
        """Setup runs before all test cases."""
        self._overrode_reddit_setup = True
        self.setup_reddit()
        self.setup_vcr()

    async def tearDown(self) -> None:
        await self.reddit._core._requestor._http.close()

    def setup_vcr(self):
        """Configure VCR instance."""
        self.recorder = VCR

        # Disable response compression in order to see the response bodies in
        # the VCR cassettes.
        self.reddit._core._requestor._http._default_headers[
            "Accept-Encoding"
        ] = "identity"

        # Require tests to explicitly disable read_only mode.
        self.reddit.read_only = True

        pytest.set_up_record = self.set_up_record  # used in conftest.py

    def setup_reddit(self):
        self._overrode_reddit_setup = False

        self._session = aiohttp.ClientSession()
        if pytest.placeholders.refresh_token != "placeholder_refresh_token":
            self.reddit = Reddit(
                requestor_kwargs={"session": self._session},
                client_id=pytest.placeholders.client_id,
                client_secret=pytest.placeholders.client_secret,
                user_agent=pytest.placeholders.user_agent,
                refresh_token=pytest.placeholders.refresh_token,
            )
        else:
            self.reddit = Reddit(
                requestor_kwargs={"session": self._session},
                client_id=pytest.placeholders.client_id,
                client_secret=pytest.placeholders.client_secret,
                password=pytest.placeholders.password,
                user_agent=pytest.placeholders.user_agent,
                username=pytest.placeholders.username,
            )

    def set_up_record(self):
        if not self._overrode_reddit_setup:
            if pytest.placeholders.refresh_token != "placeholder_refresh_token":
                self.reddit = Reddit(
                    requestor_kwargs={"session": self._session},
                    client_id=pytest.placeholders.client_id,
                    client_secret=pytest.placeholders.client_secret,
                    user_agent=pytest.placeholders.user_agent,
                    refresh_token=pytest.placeholders.refresh_token,
                )

    @staticmethod
    async def async_list(async_generator):
        """Return a list from an async iterator."""
        return [item async for item in async_generator]

    @staticmethod
    async def async_next(async_generator):
        """Return the next item from an async iterator."""
        async for item in async_generator:
            return item

    def use_cassette(self, cassette_name=None, **kwargs):
        """Use a cassette. The cassette name is dynamically generated.

        :param cassette_name: (Deprecated) The name to use for the cassette. All names
            that are not equal to the dynamically generated name will be logged.
        :param kwargs: All keyword arguments for the main function
            (``VCR.use_cassette``).
        """
        dynamic_name = self.get_cassette_name()
        if cassette_name:
            self.logger.debug(
                f"Static cassette name provided by {dynamic_name}. The following name "
                f"was provided: {cassette_name}"
            )
            if cassette_name != dynamic_name:
                self.logger.warning(
                    f"Dynamic cassette name for function {dynamic_name} does not "
                    f"match the provided cassette name: {cassette_name}"
                )
        return self.recorder.use_cassette(cassette_name or dynamic_name, **kwargs)

    def get_cassette_name(self) -> str:
        function_name = inspect.currentframe().f_back.f_back.f_code.co_name
        return f"{type(self).__name__}.{function_name}"
