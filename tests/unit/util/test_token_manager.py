"""Test asyncpraw.util.refresh_token_manager."""
import sys
from tempfile import NamedTemporaryFile

import aiofiles
import pytest

if sys.version_info < (3, 8):
    from asynctest import mock
else:
    from unittest import mock

from asyncpraw.util.token_manager import (
    BaseTokenManager,
    FileTokenManager,
    SQLiteTokenManager,
)

from .. import UnitTest
from ..test_reddit import DummyTokenManager


class DummyAuthorizer:
    def __init__(self, refresh_token):
        self.refresh_token = refresh_token


class TestBaseTokenManager(UnitTest):
    def test_init_base_fail(self):
        with pytest.raises(TypeError):
            BaseTokenManager()

    def test_reddit(self):
        manager = DummyTokenManager()
        manager.reddit = "dummy"
        assert manager.reddit == "dummy"

    def test_reddit__must_only_be_set_once(self):
        manager = DummyTokenManager()
        manager.reddit = "dummy"
        with pytest.raises(RuntimeError) as excinfo:
            manager.reddit = None
        assert (
            str(excinfo.value)
            == "'reddit' can only be set once and is done automatically"
        )


class TestFileTokenManager(UnitTest):
    @pytest.fixture(autouse=True)
    def _patch_aiofiles(self):
        aiofiles.threadpool.wrap.register(mock.MagicMock)(
            lambda *args, **kwargs: aiofiles.threadpool.AsyncBufferedIOBase(
                *args, **kwargs
            )
        )

    async def test_post_refresh_token_callback__writes_to_file(self):
        authorizer = DummyAuthorizer("token_value")
        manager = FileTokenManager("mock/dummy_path")
        mock_file = mock.MagicMock()

        with mock.patch(
            "aiofiles.threadpool.sync_open", return_value=mock_file
        ) as mock_open:
            await manager.post_refresh_callback(authorizer)

            assert authorizer.refresh_token == "token_value"
            mock_open.assert_called_once_with(
                "mock/dummy_path",
                mode="w",
                buffering=-1,
                encoding=None,
                errors=None,
                newline=None,
                closefd=True,
                opener=None,
            )
            mock_open().write.assert_called_once_with("token_value")

    async def test_pre_refresh_token_callback__reads_from_file(self):
        authorizer = DummyAuthorizer(None)
        manager = FileTokenManager("mock/dummy_path")
        mock_file = mock.MagicMock()
        mock_file.read = mock.MagicMock(return_value="token_value\n")

        with mock.patch(
            "aiofiles.threadpool.sync_open", return_value=mock_file
        ) as mock_open:
            await manager.pre_refresh_callback(authorizer)

            assert authorizer.refresh_token == "token_value"
            mock_open.assert_called_once_with(
                "mock/dummy_path",
                mode="r",
                buffering=-1,
                encoding=None,
                errors=None,
                newline=None,
                closefd=True,
                opener=None,
            )


class TestSQLiteTokenManager(UnitTest):
    @pytest.fixture
    def manager(self):
        return SQLiteTokenManager(database=":memory:", key="dummy_key")

    async def test_is_registered(self, manager):
        assert not await manager.is_registered()
        await manager.close()

    @pytest.mark.skipif(
        sys.platform.startswith("win"), reason="this test fails on windows"
    )
    async def test_multiple_instances(self, manager):
        with NamedTemporaryFile() as fp:
            manager1 = SQLiteTokenManager(database=fp.name, key="dummy_key1")
            manager2 = SQLiteTokenManager(database=fp.name, key="dummy_key1")
            manager3 = SQLiteTokenManager(database=fp.name, key="dummy_key2")

            await manager1.register("dummy_value1")
            assert await manager2.is_registered()
            assert not await manager3.is_registered()
            await manager1.close()
            await manager2.close()
            await manager3.close()

    async def test_post_refresh_token_callback__sets_value(self, manager):
        authorizer = DummyAuthorizer("dummy_value")

        await manager.post_refresh_callback(authorizer)
        assert authorizer.refresh_token is None
        assert await manager._get() == "dummy_value"
        await manager.close()

    async def test_post_refresh_token_callback__updates_value(self, manager):
        authorizer = DummyAuthorizer("dummy_value_updated")
        await manager.register("dummy_value")

        await manager.post_refresh_callback(authorizer)
        assert authorizer.refresh_token is None
        assert await manager._get() == "dummy_value_updated"
        await manager.close()

    async def test_pre_refresh_token_callback(self, manager):
        authorizer = DummyAuthorizer(None)
        await manager.register("dummy_value")

        await manager.pre_refresh_callback(authorizer)
        assert authorizer.refresh_token == "dummy_value"
        await manager.close()

    async def test_pre_refresh_token_callback__raises_key_error(self, manager):
        authorizer = DummyAuthorizer(None)

        with pytest.raises(KeyError):
            await manager.pre_refresh_callback(authorizer)
        await manager.close()

    async def test_register(self, manager):
        assert await manager.register("dummy_value")
        assert await manager.is_registered()
        assert not await manager.register("dummy_value2")
        assert await manager._get() == "dummy_value"
        await manager.close()
