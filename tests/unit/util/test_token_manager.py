"""Test asyncpraw.util.refresh_token_manager."""
import sys
from tempfile import NamedTemporaryFile

import aiofiles
import pytest
from asynctest import mock

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
            == "``reddit`` can only be set once and is done automatically"
        )


class TestFileTokenManager(UnitTest):
    async def setUp(self):
        aiofiles.threadpool.wrap.register(mock.MagicMock)(
            lambda *args, **kwargs: aiofiles.threadpool.AsyncBufferedIOBase(
                *args, **kwargs
            )
        )
        await super(TestFileTokenManager, self).setUp()

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
    def setUp(self):
        self.manager = SQLiteTokenManager(":memory:", "dummy_key")

    async def test_is_registered(self):
        assert not await self.manager.is_registered()
        await self.manager.close()

    @pytest.mark.skipif(
        sys.platform.startswith("win"), reason="this test fails on windows"
    )
    async def test_multiple_instances(self):
        with NamedTemporaryFile() as fp:
            manager1 = SQLiteTokenManager(fp.name, "dummy_key1")
            manager2 = SQLiteTokenManager(fp.name, "dummy_key1")
            manager3 = SQLiteTokenManager(fp.name, "dummy_key2")

            await manager1.register("dummy_value1")
            assert await manager2.is_registered()
            assert not await manager3.is_registered()
            await manager1.close()
            await manager2.close()
            await manager3.close()

    async def test_post_refresh_token_callback__sets_value(self):
        authorizer = DummyAuthorizer("dummy_value")

        await self.manager.post_refresh_callback(authorizer)
        assert authorizer.refresh_token is None
        assert await self.manager._get() == "dummy_value"
        await self.manager.close()

    async def test_post_refresh_token_callback__updates_value(self):
        authorizer = DummyAuthorizer("dummy_value_updated")
        await self.manager.register("dummy_value")

        await self.manager.post_refresh_callback(authorizer)
        assert authorizer.refresh_token is None
        assert await self.manager._get() == "dummy_value_updated"
        await self.manager.close()

    async def test_pre_refresh_token_callback(self):
        authorizer = DummyAuthorizer(None)
        await self.manager.register("dummy_value")

        await self.manager.pre_refresh_callback(authorizer)
        assert authorizer.refresh_token == "dummy_value"
        await self.manager.close()

    async def test_pre_refresh_token_callback__raises_key_error(self):
        authorizer = DummyAuthorizer(None)

        with pytest.raises(KeyError):
            await self.manager.pre_refresh_callback(authorizer)
        await self.manager.close()

    async def test_register(self):
        assert await self.manager.register("dummy_value")
        assert await self.manager.is_registered()
        assert not await self.manager.register("dummy_value2")
        assert await self.manager._get() == "dummy_value"
        await self.manager.close()
