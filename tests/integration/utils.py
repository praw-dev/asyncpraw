"""Pytest utils for integration tests."""

import json
import os
from datetime import datetime
from typing import Dict

import pytest
from vcr.persisters.filesystem import FilesystemPersister
from vcr.serialize import deserialize, serialize

from tests.conftest import placeholders as _placeholders


def ensure_environment_variables():
    """Ensure needed environment variables for recording a new cassette are set."""
    for key in (
        "client_id",
        "client_secret",
    ):
        if getattr(pytest.placeholders, key) == f"placeholder_{key}":
            raise ValueError(
                f"Environment variable 'prawtest_{key}' must be set for recording new"
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
            "Environment variables 'prawtest_refresh_token' or 'prawtest_username' and"
            " 'prawtest_password' must be set for new cassette recording."
        )


def ensure_integration_test(cassette):
    """Ensure test is being run is actually an integration test and error if not."""
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
        _placeholders["access_token"] = token
    except (KeyError, TypeError, ValueError):
        pass
    return response


class CustomPersister(FilesystemPersister):
    """Custom persister to handle placeholders."""

    additional_placeholders = {}

    @classmethod
    def add_additional_placeholders(cls, placeholders: Dict[str, str]):
        """Add additional placeholders."""
        cls.additional_placeholders.update(placeholders)

    @classmethod
    def clear_additional_placeholders(cls):
        """Clear additional placeholders."""
        cls.additional_placeholders = {}

    @classmethod
    def load_cassette(cls, cassette_path, serializer):
        """Load cassette."""
        try:
            with open(cassette_path) as f:
                cassette_content = f.read()
        except OSError:
            raise ValueError("Cassette not found.")
        for replacement, value in [
            (v, f"<{k.upper()}>")
            for k, v in {**cls.additional_placeholders, **_placeholders}.items()
        ]:
            cassette_content = cassette_content.replace(value, replacement)
        cassette = deserialize(cassette_content, serializer)
        return cassette

    @classmethod
    def save_cassette(cls, cassette_path, cassette_dict, serializer):
        """Save cassette."""
        data = serialize(cassette_dict, serializer)
        for replacement, value in [
            (f"<{k.upper()}>", v)
            for k, v in {**cls.additional_placeholders, **_placeholders}.items()
        ]:
            data = data.replace(value, replacement)
        dirname, filename = os.path.split(cassette_path)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(cassette_path, "w") as f:
            f.write(data)


class CustomSerializer:
    """Custom serializer to handle binary objects in dict."""

    @staticmethod
    def _serialize_file(file_name):
        with open(file_name, "rb") as f:
            return f.read().decode("utf-8", "replace")

    @staticmethod
    def deserialize(cassette_string):
        return json.loads(cassette_string)

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
        """Serialize cassette."""
        timestamp = datetime.utcnow().isoformat()
        try:
            i = timestamp.rindex(".")
        except ValueError:
            pass
        else:
            timestamp = timestamp[:i]
        cassette_dict["recorded_at"] = timestamp
        return f"{json.dumps(cls._serialize_dict(cassette_dict), sort_keys=True, indent=2)}\n"
