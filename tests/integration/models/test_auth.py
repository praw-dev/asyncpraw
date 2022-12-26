"""Test asyncpraw.models.auth."""
import pytest
from asyncprawcore import InvalidToken

from asyncpraw import Reddit

from .. import IntegrationTest


class TestAuthImplicit(IntegrationTest):
    @pytest.fixture
    async def reddit(self):
        async with Reddit(
            client_id=pytest.placeholders.client_id,
            client_secret=None,
            user_agent=pytest.placeholders.user_agent,
        ) as reddit:
            yield reddit

    async def test_implicit__with_invalid_token(self, reddit):
        reddit.auth.implicit(access_token="invalid_token", expires_in=10, scope="read")
        with pytest.raises(InvalidToken):
            await reddit.user.me()

    async def test_scopes__read_only(self, reddit):
        assert reddit.read_only is True
        assert await reddit.auth.scopes() == {"*"}


class TestAuthScript(IntegrationTest):
    async def test_scopes(self, reddit):
        assert reddit.read_only is True
        assert await reddit.auth.scopes() == {"*"}


class TestAuthWeb(IntegrationTest):
    @pytest.fixture
    async def reddit(self):
        async with Reddit(
            client_id=pytest.placeholders.client_id,
            client_secret=pytest.placeholders.client_secret,
            redirect_uri=pytest.placeholders.redirect_uri,
            user_agent=pytest.placeholders.user_agent,
            username=None,
        ) as reddit:
            yield reddit

    async def test_authorize(self, reddit):
        token = await reddit.auth.authorize(pytest.placeholders.auth_code)
        assert isinstance(token, str)
        assert reddit.read_only is False
        assert await reddit.auth.scopes() == {"submit"}

    async def test_scopes__read_only(self, reddit):
        assert reddit.read_only is True
        assert await reddit.auth.scopes() == {"*"}
