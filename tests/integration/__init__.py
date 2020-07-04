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

    def setup_vcr(self):
        """Configure vcr instance based off of the reddit instance."""
        http = self.reddit._core._requestor._http
        self.recorder = VCR

        # Disable response compression in order to see the response bodies in
        # the vcr cassettes.
        http._default_headers["Accept-Encoding"] = "identity"

        # Require tests to explicitly disable read_only mode.
        self.reddit.read_only = True

        pytest.set_up_record = self.set_up_record  # used in conftest.py

    def setup_reddit(self):
        self._overrode_reddit_setup = False

        self._session = aiohttp.ClientSession()

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
        return [item async for item in async_generator]

    @staticmethod
    async def async_next(async_generator):
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
                "Static cassette name provided by {}. The following "
                "name was provided: {}".format(dynamic_name, cassette_name)
            )
            if cassette_name != dynamic_name:
                self.logger.warning(
                    "Dynamic cassette name for function {} does not "
                    "match the provided cassette name: {}".format(
                        dynamic_name, cassette_name
                    )
                )
        return self.recorder.use_cassette(cassette_name or dynamic_name, **kwargs)

    def get_cassette_name(self) -> str:
        function_name = inspect.currentframe().f_back.f_back.f_code.co_name
        return "{}.{}".format(type(self).__name__, function_name)
