"""Prepare py.test."""
import json
import os
import asyncio
from base64 import b64encode
from datetime import datetime
from functools import wraps

import pytest
from _pytest.tmpdir import _mk_tmp
from vcr import VCR
from vcr.cassette import Cassette
from vcr.persisters.filesystem import FilesystemPersister
from vcr.serialize import deserialize, serialize


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
    request_uri = response["url"]
    if "api/v1/access_token" not in request_uri or response["status"]["code"] != 200:
        return response
    body = response["body"]["string"].decode()
    try:
        token = json.loads(body)["access_token"]
        response["body"]["string"] = response["body"]["string"].replace(
            token.encode("utf-8"), b"<ACCESS_TOKEN>"
        )
        placeholders["access_token"] = token
    except (KeyError, TypeError, ValueError):
        pass
    return response


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


class CustomVCR(VCR):
    """Derived from VCR to make setting paths easier."""

    def use_cassette(self, path="", **kwargs):
        """Use a cassette."""
        path += ".json"
        return super().use_cassette(path, **kwargs)


def serialize_list(data: list):
    new_list = []
    for item in data:
        if isinstance(item, dict):
            new_list.append(serialize_dict(item))
        elif isinstance(item, list):
            new_list.append(serialize_list(item))
        else:
            new_list.append(item)
    return new_list


def serialize_dict(data: dict):
    """this is to filter out buffered readers"""
    new_dict = {}
    for key, value in data.items():
        if key == "file":
            continue  # skip files
        elif isinstance(value, dict):
            new_dict[key] = serialize_dict(value)
        elif isinstance(value, list):
            new_dict[key] = serialize_list(value)
        else:
            new_dict[key] = value
    return new_dict


class CustomSerializer(object):
    @staticmethod
    def serialize(cassette_dict):
        cassette_dict["recorded_at"] = datetime.now().isoformat()[:-7]
        return (
            json.dumps(serialize_dict(cassette_dict), sort_keys=True, indent=2) + "\n"
        )

    @staticmethod
    def deserialize(cassette_string):
        return json.loads(cassette_string)


class CustomPersister(FilesystemPersister):
    @classmethod
    def load_cassette(cls, cassette_path, serializer):
        try:
            with open(cassette_path) as f:
                cassette_content = f.read()
        except OSError:
            raise ValueError("Cassette not found.")
        for replacement, value in [
            (v, f"<{k.upper()}>") for k, v in placeholders.items()
        ]:
            cassette_content = cassette_content.replace(value, replacement)
        cassette = deserialize(cassette_content, serializer)
        return cassette

    @staticmethod
    def save_cassette(cassette_path, cassette_dict, serializer):
        data = serialize(cassette_dict, serializer)
        for replacement, value in [
            (f"<{k.upper()}>", v) for k, v in placeholders.items()
        ]:
            data = data.replace(value, replacement)
        dirname, filename = os.path.split(cassette_path)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(cassette_path, "w") as f:
            f.write(data)


VCR = CustomVCR(
    serializer="custom_serializer",
    cassette_library_dir="tests/integration/cassettes",
    match_on=["uri", "method"],
    before_record_response=filter_access_token,
)
VCR.register_serializer("custom_serializer", CustomSerializer)
VCR.register_persister(CustomPersister)


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
    if not cassette.requests:
        pytest.set_up_record()  # dynamically defined in __init__.py


class Placeholders:
    def __init__(self, _dict):
        self.__dict__ = _dict


def pytest_configure():
    pytest.placeholders = Placeholders(placeholders)


@pytest.fixture
def tmp_path(request, tmp_path_factory):
    """Manually create tmp_path fixture since asynctest does not play nicely with fixtures as args"""
    request.cls.tmp_path = _mk_tmp(request, tmp_path_factory)
