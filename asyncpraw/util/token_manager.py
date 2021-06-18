"""Token Manager classes.

There should be a 1-to-1 mapping between an instance of a subclass of
:class:`.BaseTokenManager` and a :class:`.Reddit` instance.

A few proof of concept token manager classes are provided here, but it is expected that
Async PRAW users will create their own token manager classes suitable for their needs.

See :ref:`using_refresh_tokens` for examples on how to leverage these classes.

"""
from abc import ABC, abstractmethod

import aiofiles
import aiosqlite
from asyncio_extras import async_contextmanager


class BaseTokenManager(ABC):
    """An abstract class for all token managers."""

    def __init__(self):
        """Prepare attributes needed by all token manager classes."""
        self._reddit = None

    @property
    def reddit(self):
        """Return the :class:`.Reddit` instance bound to the token manager."""
        return self._reddit

    @reddit.setter
    def reddit(self, value):
        if self._reddit is not None:
            raise RuntimeError(
                "``reddit`` can only be set once and is done automatically"
            )
        self._reddit = value

    @abstractmethod
    def post_refresh_callback(self, authorizer):
        """Handle callback that is invoked after a refresh token is used.

        :param authorizer: The ``asyncprawcore.Authorizer`` instance used containing
            ``access_token`` and ``refresh_token`` attributes.

        This function will be called after refreshing the access and refresh tokens.
        This callback can be used for saving the updated ``refresh_token``.

        """

    @abstractmethod
    def pre_refresh_callback(self, authorizer):
        """Handle callback that is invoked before refreshing PRAW's authorization.

        :param authorizer: The ``asyncprawcore.Authorizer`` instance used containing
            ``access_token`` and ``refresh_token`` attributes.

        This callback can be used to inspect and modify the attributes of the
        ``asyncprawcore.Authorizer`` instance, such as setting the ``refresh_token``.

        """


class FileTokenManager(BaseTokenManager):
    """Provides a single-file based token manager.

    It is expected that the file with the initial ``refresh_token`` is created prior to
    use.

    .. warning::

        The same ``file`` should not be used by more than one instance of this class
        concurrently. Doing so may result in data corruption. Consider using
        :class:`.SQLiteTokenManager` if you want more than one instance of PRAW to
        concurrently manage a specific ``refresh_token`` chain.

    """

    def __init__(self, filename):
        """Load and save refresh tokens from a file.

        :param filename: The file the contains the refresh token.

        """
        super().__init__()
        self._filename = filename

    async def post_refresh_callback(self, authorizer):
        """Update the saved copy of the refresh token."""
        async with aiofiles.open(self._filename, "w") as fp:
            await fp.write(authorizer.refresh_token)

    async def pre_refresh_callback(self, authorizer):
        """Load the refresh token from the file."""
        if authorizer.refresh_token is None:
            async with aiofiles.open(self._filename) as fp:
                authorizer.refresh_token = (await fp.read()).strip()


class SQLiteTokenManager(BaseTokenManager):
    """Provides a SQLite3 based token manager.

    Unlike, :class:`.FileTokenManager`, the initial database need not be created ahead
    of time, as it'll automatically be created on first use. However, initial
    ``refresh_tokens`` will need to be registered via :meth:`.register` prior to use.
    See :ref:`sqlite_token_manager` for an example of use.

    .. warning::

        This class is untested on Windows because we encountered file locking issues in
        the test environment.

    """

    def __init__(self, database, key):
        """Load and save refresh tokens from a SQLite database.

        :param database: The path to the SQLite database.
        :param key: The key used to locate the ``refresh_token``. This ``key`` can be
            anything. You might use the ``client_id`` if you expect to have unique
            ``refresh_tokens`` for each ``client_id``, or you might use a Redditor's
            ``username`` if you're manage multiple users' authentications.

        """
        super().__init__()
        self._connection = None
        self._database = database
        self._setup_ran = False
        self.key = key

    @async_contextmanager
    async def connection(self):
        """Asynchronously setup and provide the sqlite3 connection."""
        if self._connection is None:
            self._connection = await aiosqlite.connect(self._database)
        if not self._setup_ran:
            await self._connection.execute(
                "CREATE TABLE IF NOT EXISTS tokens (id, refresh_token, updated_at)"
            )
            await self._connection.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS ux_tokens_id on tokens(id)"
            )
            await self._connection.commit()
            self._setup_ran = True
        yield self._connection

    async def _get(self):
        async with self.connection() as conn:
            cursor = await conn.execute(
                "SELECT refresh_token FROM tokens WHERE id=?", (self.key,)
            )
            result = await cursor.fetchone()
            if result is None:
                raise KeyError
        return result[0]

    async def _set(self, refresh_token):
        """Set the refresh token in the database.

        This function will overwrite an existing value if the corresponding ``key``
        already exists.

        """
        async with self.connection() as conn:
            await conn.execute(
                "REPLACE INTO tokens VALUES (?, ?, datetime('now'))",
                (self.key, refresh_token),
            )
            await conn.commit()

    async def close(self):
        """Close the sqlite3 connection."""
        await self._connection.close()

    async def is_registered(self):
        """Return whether ``key`` already has a ``refresh_token``."""
        async with self.connection() as conn:
            cursor = await conn.execute(
                "SELECT refresh_token FROM tokens WHERE id=?", (self.key,)
            )
            result = await cursor.fetchone()
        return result is not None

    async def post_refresh_callback(self, authorizer):
        """Update the refresh token in the database."""
        await self._set(authorizer.refresh_token)

        # While the following line is not strictly necessary, it ensures that the
        # refresh token is not used elsewhere. And also forces the pre_refresh_callback
        # to always load the latest refresh_token from the database.
        authorizer.refresh_token = None

    async def pre_refresh_callback(self, authorizer):
        """Load the refresh token from the database."""
        assert authorizer.refresh_token is None
        authorizer.refresh_token = await self._get()

    async def register(self, refresh_token):
        """Register the initial refresh token in the database.

        :returns: ``True`` if ``refresh_token`` is saved to the database, otherwise,
            ``False`` if there is already a ``refresh_token`` for the associated
            ``key``.

        """
        async with self.connection() as conn:
            cursor = await conn.execute(
                "INSERT OR IGNORE INTO tokens VALUES (?, ?, datetime('now'))",
                (self.key, refresh_token),
            )
            await conn.commit()
            row_count = cursor.rowcount
        return row_count == 1
