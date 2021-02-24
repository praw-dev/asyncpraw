"""Test asyncpraw.util.refresh_token_manager."""
import aiofiles
import pytest
from asynctest import mock

from asyncpraw.util.token_manager import BaseTokenManager, FileTokenManager

from .. import UnitTest


class DummyAuthorizer:
    def __init__(self, refresh_token):
        self.refresh_token = refresh_token


class TestBaseTokenManager(UnitTest):
    def test_post_refresh_token_callback__raises_not_implemented(self):
        manager = BaseTokenManager()
        with pytest.raises(NotImplementedError) as excinfo:
            manager.post_refresh_callback(None)
        assert str(excinfo.value) == "``post_refresh_callback`` must be extended."

    def test_pre_refresh_token_callback__raises_not_implemented(self):
        manager = BaseTokenManager()
        with pytest.raises(NotImplementedError) as excinfo:
            manager.pre_refresh_callback(None)
        assert str(excinfo.value) == "``pre_refresh_callback`` must be extended."

    def test_reddit(self):
        manager = BaseTokenManager()
        manager.reddit = "dummy"
        assert manager.reddit == "dummy"

    def test_reddit__must_only_be_set_once(self):
        manager = BaseTokenManager()
        manager.reddit = "dummy"
        with pytest.raises(RuntimeError) as excinfo:
            manager.reddit = None
        assert (
            str(excinfo.value)
            == "``reddit`` can only be set once and is done automatically"
        )


class TestFileTokenManager(UnitTest):
    def setUp(self):
        aiofiles.threadpool.wrap.register(mock.MagicMock)(
            lambda *args, **kwargs: aiofiles.threadpool.AsyncBufferedIOBase(
                *args, **kwargs
            )
        )
        super(TestFileTokenManager, self).setUp()

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
