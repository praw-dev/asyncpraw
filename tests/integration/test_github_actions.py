"""A test that is run only by GitHub Actions

This test makes real network requests, so environment variables should be specified in
GitHub Actions.

"""
import os

import pytest

from asyncpraw import Reddit
from asyncpraw.models import Submission


@pytest.mark.skipif(
    not os.getenv("NETWORK_TEST_CLIENT_ID"),
    reason="Not running from the NETWORK_TEST ci task on praw-dev/asyncpraw",
)
async def test_github_actions():
    async with Reddit(
        client_id=os.getenv("NETWORK_TEST_CLIENT_ID"),
        client_secret=os.getenv("NETWORK_TEST_CLIENT_SECRET"),
        user_agent="GitHub Actions CI Testing",
    ) as reddit:
        subreddit = await reddit.subreddit("all")
        async for submission in subreddit.hot():
            assert isinstance(submission, Submission)
            break
