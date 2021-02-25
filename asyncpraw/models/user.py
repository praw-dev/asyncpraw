"""Provides the User class."""
from typing import TYPE_CHECKING, AsyncIterator, Dict, List, Optional, Union
from warnings import warn

from ..const import API_PATH
from ..exceptions import ReadOnlyException
from ..models import Preferences
from ..util.cache import cachedproperty
from .base import AsyncPRAWBase
from .listing.generator import ListingGenerator
from .reddit.redditor import Redditor
from .reddit.subreddit import Subreddit

if TYPE_CHECKING:  # pragma: no cover
    from ... import asyncpraw


class User(AsyncPRAWBase):
    """The user class provides methods for the currently authenticated user."""

    @cachedproperty
    def preferences(self) -> "asyncpraw.models.Preferences":
        """Get an instance of :class:`~.Preferences`.

        The preferences can be accessed as a ``dict`` like so:

        .. code-block:: python

            preferences = await reddit.user.preferences()
            print(preferences["show_link_flair"])

        Preferences can be updated via:

        .. code-block:: python

            await reddit.user.preferences.update(show_link_flair=True)

        The :meth:`.Preferences.update` method returns the new state of the preferences
        as a ``dict``, which can be used to check whether a change went through. Changes
        with invalid types or parameter names fail silently.

        .. code-block:: python

            original_preferences = await reddit.user.preferences()
            new_prefs = await original_preferences.update(invalid_param=123)
            print(original_preferences == new_prefs)  # True, no change

        """
        return Preferences(self._reddit)

    def __init__(self, reddit: "asyncpraw.Reddit"):
        """Initialize a User instance.

        This class is intended to be interfaced with through ``reddit.user``.

        """
        super().__init__(reddit, _data=None)

    async def blocked(self) -> List["asyncpraw.models.Redditor"]:
        """Return a RedditorList of blocked Redditors."""
        return await self._reddit.get(API_PATH["blocked"])

    def contributor_subreddits(
        self, **generator_kwargs: Union[str, int, Dict[str, str]]
    ) -> AsyncIterator["asyncpraw.models.Subreddit"]:
        """Return a :class:`.ListingGenerator` of contributor subreddits.

        These are subreddits that the user is a contributor of.

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        """
        return ListingGenerator(
            self._reddit, API_PATH["my_contributor"], **generator_kwargs
        )

    async def friends(
        self, user: Optional[Union[str, "asyncpraw.models.Redditor"]] = None
    ) -> Union[List["asyncpraw.models.Redditor"], "asyncpraw.models.Redditor"]:
        """Return a RedditorList of friends or a Redditor in the friends list.

        :param user: Checks to see if you are friends with the Redditor. Either an
            instance of :class:`.Redditor` or a string can be given.

        :returns: A list of Redditors, or a Redditor if you are friends with the given
            Redditor. The Redditor also has friend attributes.

        :raises: An instance of ``asyncprawcore.exceptions.BadRequest`` if you are not
            friends with the specified Redditor.

        """
        endpoint = (
            API_PATH["friends"]
            if user is None
            else API_PATH["friend_v1"].format(user=str(user))
        )
        return await self._reddit.get(endpoint)

    async def karma(self) -> Dict["asyncpraw.models.Subreddit", Dict[str, int]]:
        """Return a dictionary mapping subreddits to their karma.

        The returned dict contains subreddits as keys. Each subreddit key contains a
        sub-dict that have keys for ``comment_karma`` and ``link_karma``. The dict is
        sorted in descending karma order.

        .. note::

            Each key of the main dict is an instance of :class:`~.Subreddit`. It is
            recommended to iterate over the dict in order to retrieve the values,
            preferably through ``dict.items()``.

        """
        karma_map = {}
        response = await self._reddit.get(API_PATH["karma"])
        for row in response["data"]:
            subreddit = Subreddit(self._reddit, row["sr"])
            del row["sr"]
            karma_map[subreddit] = row
        return karma_map

    async def me(
        self, use_cache: bool = True
    ) -> Optional["asyncpraw.models.Redditor"]:  # pylint: disable=invalid-name
        """Return a :class:`.Redditor` instance for the authenticated user.

        :param use_cache: When true, and if this function has been previously called,
            returned the cached version (default: True).

        .. note::

            If you change the Reddit instance's authorization, you might want to refresh
            the cached value. Prefer using separate Reddit instances, however, for
            distinct authorizations.

        .. deprecated:: 7.2

            In :attr:`.read_only` mode this method returns ``None``. In Async PRAW 8
            this method will raise :class:`.ReadOnlyException` when called in
            :attr:`.read_only` mode. To operate in Async PRAW 8 mode, set the config
            variable ``praw8_raise_exception_on_me`` to ``True``.

        """
        if self._reddit.read_only:
            if not self._reddit.config.custom.get("praw8_raise_exception_on_me"):
                warn(
                    "The `None` return value is deprecated, and will raise a"
                    " `ReadOnlyException` beginning with Async PRAW 8. See"
                    " documentation for forward compatibility options.",
                    category=DeprecationWarning,
                    stacklevel=2,
                )
                return None
            raise ReadOnlyException("`user.me()` does not work in read_only mode")
        if "_me" not in self.__dict__ or not use_cache:
            user_data = await self._reddit.get(API_PATH["me"])
            self._me = Redditor(self._reddit, _data=user_data)
        return self._me

    async def multireddits(self) -> List["asyncpraw.models.Multireddit"]:
        """Return a list of multireddits belonging to the user."""
        return await self._reddit.get(API_PATH["my_multireddits"])

    def subreddits(
        self, **generator_kwargs: Union[str, int, Dict[str, str]]
    ) -> AsyncIterator["asyncpraw.models.Subreddit"]:
        """Return a :class:`.ListingGenerator` of subreddits the user is subscribed to.

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        """
        return ListingGenerator(
            self._reddit, API_PATH["my_subreddits"], **generator_kwargs
        )
