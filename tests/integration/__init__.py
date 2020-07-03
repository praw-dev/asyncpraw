"""PRAW Integration test suite."""
import aiohttp
import pytest

from asyncpraw import Reddit

from tests.conftest import VCR


class IntegrationTest:
    """Base class for PRAW integration tests."""

    def setup(self):
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
        http.headers["Accept-Encoding"] = "identity"

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
