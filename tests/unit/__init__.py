"""PRAW Unit test suite."""
import asynctest

from asyncpraw import Reddit


class UnitTest(asynctest.TestCase):
    """Base class for PRAW unit tests."""

    async def setUp(self):
        """Setup runs before all test cases."""
        self.reddit = Reddit(
            client_id="dummy", client_secret="dummy", user_agent="dummy"
        )
        # Unit tests should never issue requests
        await self.reddit._core.close()
        self.reddit._core._requestor._http = None
