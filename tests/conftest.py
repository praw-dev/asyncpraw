"""Prepare pytest."""

import asyncio
import os
from base64 import b64encode
from sys import modules

import requests
import niquests
import urllib3
from prawcore import Requestor

# betamax is tied to Requests
# and Niquests is almost entirely compatible with it.
# we can fool it without effort.
modules["requests"] = niquests
modules["requests.adapters"] = niquests.adapters
modules["requests.models"] = niquests.models
modules["requests.exceptions"] = niquests.exceptions
modules["requests.packages.urllib3"] = urllib3

# niquests no longer have a compat submodule
# but betamax need it. no worries, as betamax
# explicitly need requests, we'll give it to him.
modules["requests.compat"] = requests.compat

# doing the import now will make betamax working with Niquests!
# no extra effort.
import betamax

# the base mock does not implement close(), which is required
# for our HTTP client. No biggy.
betamax.mock_response.MockHTTPResponse.close = lambda _: None

import pytest


@pytest.fixture
def requestor():
    """Return path to image."""
    return Requestor("prawcore:test (by /u/bboe)")


@pytest.fixture(autouse=True)
def patch_sleep(monkeypatch):
    """Auto patch sleep to speed up tests."""

    async def _sleep(*_, **__):
        """Dud sleep function."""
        return

    monkeypatch.setattr(asyncio, "sleep", value=_sleep)


@pytest.fixture
def image_path():
    """Return path to image."""

    def _get_path(name):
        """Return path to image."""
        return os.path.join(os.path.dirname(__file__), "integration", "files", name)

    return _get_path


def pytest_configure(config):
    pytest.placeholders = Placeholders(placeholders)
    config.addinivalue_line(
        "markers", "add_placeholder: Define an additional placeholder for the cassette."
    )
    config.addinivalue_line(
        "markers", "cassette_name: Name of cassette to use for test."
    )
    config.addinivalue_line(
        "markers", "recorder_kwargs: Arguments to pass to the recorder."
    )


os.environ["praw_check_for_updates"] = "False"

placeholders = {
    x: os.environ.get(f"prawtest_{x}", f"placeholder_{x}")
    for x in (
        "auth_code client_id client_secret password redirect_uri refresh_token"
        " test_subreddit user_agent username"
    ).split()
}

placeholders["basic_auth"] = b64encode(
    f"{placeholders['client_id']}:{placeholders['client_secret']}".encode("utf-8")
).decode("utf-8")


class Placeholders:
    def __init__(self, _dict):
        self.__dict__ = _dict
