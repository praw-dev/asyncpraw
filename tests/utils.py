"""Pytest utils for integration tests."""

import json

import pytest

from betamax.serializers import JSONSerializer

from tests.conftest import placeholders as _placeholders


def ensure_environment_variables():
    """Ensure needed environment variables for recording a new cassette are set."""
    for key in (
        "client_id",
        "client_secret",
    ):
        if getattr(pytest.placeholders, key) == f"placeholder_{key}":
            msg = f"Environment variable 'prawtest_{key}' must be set for recording new cassettes."
            raise ValueError(msg)
    auth_set = False
    for auth_keys in [["refresh_token"], ["username", "password"]]:
        if all(
            getattr(pytest.placeholders, key) != f"placeholder_{key}"
            for key in auth_keys
        ):
            auth_set = True
            break
    if not auth_set:
        msg = "Environment variables 'prawtest_refresh_token' or 'prawtest_username' and 'prawtest_password' must be set for new cassette recording."
        raise ValueError(msg)


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


class PrettyJSONSerializer(JSONSerializer):
    name = "prettyjson"

    def serialize(self, cassette_data):
        return f"{json.dumps(cassette_data, sort_keys=True, indent=2)}\n"
