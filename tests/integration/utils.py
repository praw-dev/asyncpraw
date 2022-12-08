"""Pytest utils for integration tests."""

import json
import os
from datetime import datetime

import pytest
from vcr.persisters.filesystem import FilesystemPersister
from vcr.serialize import deserialize, serialize

from tests.conftest import placeholders


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
        cassette_dict["recorded_at"] = datetime.now().isoformat()[:-7]
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


class CustomSerializer:
    @staticmethod
    def _serialize_file(file_name):
        with open(file_name, "rb") as f:
            return f.read().decode("utf-8", "replace")

    @classmethod
    def _serialize_dict(cls, data: dict):
        """This is to filter out buffered readers."""
        new_dict = {}
        for key, value in data.items():
            if key == "file":
                new_dict[key] = cls._serialize_file(value.name)
            elif isinstance(value, dict):
                new_dict[key] = cls._serialize_dict(value)
            elif isinstance(value, list):
                new_dict[key] = cls._serialize_list(value)
            else:
                new_dict[key] = value
        return new_dict

    @classmethod
    def _serialize_list(cls, data: list):
        new_list = []
        for item in data:
            if isinstance(item, dict):
                new_list.append(cls._serialize_dict(item))
            elif isinstance(item, list):
                new_list.append(cls._serialize_list(item))
            elif isinstance(item, tuple):
                if item[0] == "file":
                    item = (item[0], cls._serialize_file(item[1].name))
                new_list.append(item)
            else:
                new_list.append(item)
        return new_list

    @classmethod
    def serialize(cls, cassette_dict):
        return f"{json.dumps(cls._serialize_dict(cassette_dict), sort_keys=True, indent=2)}\n"

    @staticmethod
    def deserialize(cassette_string):
        return json.loads(cassette_string)


def ensure_environment_variables():
    """Ensure needed environment variables for recording a new cassette are set."""
    for key in (
        "client_id",
        "client_secret",
    ):
        if getattr(pytest.placeholders, key) == f"placeholder_{key}":
            raise ValueError(
                f"Environment variable 'prawtest_{key}' must be set for recording new "
                " cassettes."
            )
    auth_set = False
    for auth_keys in [["refresh_token"], ["username", "password"]]:
        if all(
            getattr(pytest.placeholders, key) != f"placeholder_{key}"
            for key in auth_keys
        ):
            auth_set = True
            break
    if not auth_set:
        raise ValueError(
            "Environment variables 'prawtest_refresh_token' or 'prawtest_username'"
            " and 'prawtest_password' must be set for new cassette recording."
        )


def ensure_integration_test(cassette):
    if cassette.write_protected:
        is_integration_test = cassette.play_count > 0
        action = "play back"
    else:
        is_integration_test = cassette.dirty
        action = "record"
    message = f"Cassette did not {action} any requests. This test can be a unit test."
    assert is_integration_test, message


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
