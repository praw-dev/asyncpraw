"""Prepare py.test."""
import json
import os
import socket
import asyncio
from base64 import b64encode
from functools import wraps
from sys import platform

import pytest
from vcr import VCR
from vcr.cassette import Cassette


# Prevent calls to sleep
async def _sleep(*args):
    raise Exception("Call to sleep")


asyncio.sleep = _sleep


def b64_string(input_string):
    """Return a base64 encoded string (not bytes) from input_string."""
    return b64encode(input_string.encode("utf-8")).decode("utf-8")


def env_default(key):
    """Return environment variable or placeholder string."""
    return os.environ.get("prawtest_{}".format(key), "placeholder_{}".format(key))


def filter_access_token(response):
    """Add VCR callback to filter access token."""
    request_uri = response.data["request"]["uri"]
    response = response.data["response"]
    if "api/v1/access_token" not in request_uri or response["status"]["code"] != 200:
        return
    body = response["body"]["string"]
    try:
        json.loads(body)["access_token"]
    except (KeyError, TypeError, ValueError):
        return


os.environ["praw_check_for_updates"] = "False"


placeholders = {
    x: env_default(x)
    for x in (
        "auth_code client_id client_secret password redirect_uri "
        "test_subreddit user_agent username refresh_token"
    ).split()
}

placeholders["basic_auth"] = b64_string(
    "{}:{}".format(placeholders["client_id"], placeholders["client_secret"])
)


class PrettyJSONSerializer(object):
    def serialize(self, cassette_dict):
        return json.dumps(cassette_dict, sort_keys=True, indent=2) + "\n"

    def deserialize(self, cassette_string):
        return json.loads(cassette_string)


class CustomVCR(VCR):
    """Derived from VCR to make setting paths easier."""

    def use_cassette(self, path="", **kwargs):
        """Use a cassette."""
        path += ".json"
        return super().use_cassette(path, **kwargs)


class AsyncMock:
    """Class to assist making asynchronous mocks simpler to write."""

    def __init__(self, status, response_dict, headers):
        """Initialize the class with return status, response-dict and headers."""
        self.status = status
        self.response_dict = response_dict
        self.headers = headers

    async def json(self):
        """Mock the json of ClientSession.request."""
        return self.response_dict


VCR = CustomVCR(
    serializer="prettyjson",
    cassette_library_dir="tests/cassettes",
    match_on=["uri", "method"],
    filter_headers=list(placeholders),
    filter_post_data_parameters=list(placeholders),
    filter_query_parameters=list(placeholders),
    before_record_response=filter_access_token,
)
VCR.register_serializer("prettyjson", PrettyJSONSerializer)


def after_init(func, *args):
    func(*args)


def add_init_hook(original_init):
    """Wrap an __init__ method to also call some hooks."""

    @wraps(original_init)
    def wrapper(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        after_init(init_hook, self)

    return wrapper


Cassette.__init__ = add_init_hook(Cassette.__init__)


def init_hook(cassette):
    if not cassette.requsets:
        pytest.set_up_record()  # dynamically defined in __init__.py


class Placeholders:
    def __init__(self, _dict):
        self.__dict__ = _dict


def pytest_configure():
    pytest.placeholders = Placeholders(placeholders)


if platform == "darwin":
    socket.gethostbyname = lambda x: "127.0.0.1"
