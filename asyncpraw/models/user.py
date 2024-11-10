"""Provides the User class."""

from __future__ import annotations

from typing import TYPE_CHECKING, AsyncIterator
from warnings import warn

from prawcore import Conflict

from ..const import API_PATH
from ..exceptions import ReadOnlyException
from ..models import Preferences
from ..util import _deprecate_args
from ..util.cache import cachedproperty
from .base import AsyncPRAWBase
from .listing.generator import ListingGenerator
from .reddit.redditor import Redditor
from .reddit.subreddit import Subreddit

if TYPE_CHECKING:  # pragma: no cover
    import asyncpraw.models


class User(AsyncPRAWBase):
    """The :class:`.User` class provides methods for the currently authenticated user."""

    @cachedproperty
    def preferences(self) -> asyncpraw.models.Preferences:
        """Get an instance of :class:`.Preferences`.

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

    def __init__(self, reddit: asyncpraw.Reddit):
        """Initialize an :class:`.User` instance.

        This class is intended to be interfaced with through ``reddit.user``.

        """
        super().__init__(reddit, _data=None)

    async def blocked(self) -> list[asyncpraw.models.Redditor]:
        r"""Return a :class:`.RedditorList` of blocked :class:`.Redditor`\ s."""
        return await self._reddit.get(API_PATH["blocked"])

    def contributor_subreddits(
        self, **generator_kwargs: str | int | dict[str, str]
    ) -> AsyncIterator[asyncpraw.models.Subreddit]:
        r"""Return a :class:`.ListingGenerator` of contributor :class:`.Subreddit`\ s.

        These are subreddits in which the user is an approved user.

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        To print a list of the subreddits that you are an approved user in, try:

        .. code-block:: python

            async for subreddit in reddit.user.contributor_subreddits(limit=None):
                print(str(subreddit))

        """
        return ListingGenerator(
            self._reddit, API_PATH["my_contributor"], **generator_kwargs
        )

    @_deprecate_args("user")
    async def friends(
        self, *, user: str | asyncpraw.models.Redditor | None = None
    ) -> list[asyncpraw.models.Redditor] | asyncpraw.models.Redditor:
        r"""Return a :class:`.RedditorList` of friends or a :class:`.Redditor` in the friends list.

        :param user: Checks to see if you are friends with the redditor. Either an
            instance of :class:`.Redditor` or a string can be given.

        :returns: A list of :class:`.Redditor`\ s, or a single :class:`.Redditor` if
            ``user`` is specified. The :class:`.Redditor` instance(s) returned also has
            friend attributes.

        :raises: An instance of :class:`.RedditAPIException` if you are not friends with
            the specified :class:`.Redditor`.

        """
        endpoint = (
            API_PATH["friends"]
            if user is None
            else API_PATH["friend_v1"].format(user=str(user))
        )
        return await self._reddit.get(endpoint)

    async def karma(self) -> dict[asyncpraw.models.Subreddit, dict[str, int]]:
        r"""Return a dictionary mapping :class:`.Subreddit`\ s to their karma.

        The returned dict contains subreddits as keys. Each subreddit key contains a
        sub-dict that have keys for ``comment_karma`` and ``link_karma``. The dict is
        sorted in descending karma order.

        .. note::

            Each key of the main dict is an instance of :class:`.Subreddit`. It is
            recommended to iterate over the dict in order to retrieve the values,
            preferably through :py:meth:`dict.items`.

        """
        karma_map = {}
        response = await self._reddit.get(API_PATH["karma"])
        for row in response["data"]:
            subreddit = Subreddit(self._reddit, row["sr"])
            del row["sr"]
            karma_map[subreddit] = row
        return karma_map

    @_deprecate_args("use_cache")
    async def me(self, *, use_cache: bool = True) -> asyncpraw.models.Redditor | None:
        """Return a :class:`.Redditor` instance for the authenticated user.

        :param use_cache: When ``True``, and if this function has been previously
            called, returned the cached version (default: ``True``).

        .. note::

            If you change the :class:`.Reddit` instance's authorization, you might want
            to refresh the cached value. Prefer using separate :class:`.Reddit`
            instances, however, for distinct authorizations.

        .. deprecated:: 7.2

            In :attr:`.read_only` mode this method returns ``None``. In Async PRAW 8
            this method will raise :class:`.ReadOnlyException` when called in
            :attr:`.read_only` mode. To operate in Async PRAW 8 mode, set the config
            variable ``praw8_raise_exception_on_me`` to ``True``.

        """
        if self._reddit.read_only:
            if not self._reddit.config.custom.get("praw8_raise_exception_on_me"):
                warn(
                    "The 'None' return value is deprecated, and will raise a"
                    " ReadOnlyException beginning with Async PRAW 8. See"
                    " documentation for forward compatibility options.",
                    category=DeprecationWarning,
                    stacklevel=2,
                )
                return None
            msg = "`user.me()` does not work in read_only mode"
            raise ReadOnlyException(msg)
        if "_me" not in self.__dict__ or not use_cache:
            user_data = await self._reddit.get(API_PATH["me"])
            self._me = Redditor(self._reddit, _data=user_data)
        return self._me

    def moderator_subreddits(
        self, **generator_kwargs: str | int | dict[str, str]
    ) -> AsyncIterator[asyncpraw.models.Subreddit]:
        """Return a :class:`.ListingGenerator` subreddits that the user moderates.

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        To print a list of the names of the subreddits you moderate, try:

        .. code-block:: python

            async for subreddit in reddit.user.moderator_subreddits(limit=None):
                print(str(subreddit))

        .. seealso::

            :meth:`.Redditor.moderated`

        """
        return ListingGenerator(
            self._reddit, API_PATH["my_moderator"], **generator_kwargs
        )

    async def multireddits(self) -> list[asyncpraw.models.Multireddit]:
        r"""Return a list of :class:`.Multireddit`\ s belonging to the user."""
        return await self._reddit.get(API_PATH["my_multireddits"])

    async def pin(
        self,
        submission: asyncpraw.models.Submission,
        *,
        num: int = None,
        state: bool = True,
    ) -> asyncpraw.models.Submission:
        """Set the pin state of a submission on the authenticated user's profile.

        :param submission: An instance of :class:`.Submission` that will be
            pinned/unpinned.
        :param num: If specified, the slot in which the submission will be pinned into.
            If there is a submission already in the specified slot, it will be replaced.
            If ``None`` or there is not a submission in the specified slot, the first
            available slot will be used (default: ``None``). If all slots are used the
            following will occur:

            - Old Reddit:

              1. The submission in the last slot will be unpinned.
              2. The remaining pinned submissions will be shifted down a slot.
              3. The new submission will be pinned in the first slot.

            - New Reddit:

              1. The submission in the first slot will be unpinned.
              2. The remaining pinned submissions will be shifted up a slot.
              3. The new submission will be pinned in the last slot.

            .. note::

                At the time of writing (10/22/2021), there are 4 pin slots available and
                pins are in reverse order on old Reddit. If ``num`` is an invalid value,
                Reddit will ignore it and the same behavior will occur as if ``num`` is
                ``None``.

        :param state: ``True`` pins the submission, ``False`` unpins (default:
            ``True``).

        :returns: The pinned submission.

        :raises: ``prawcore.BadRequest`` when pinning a removed or deleted submission.
        :raises: ``prawcore.Forbidden`` when pinning a submission the authenticated user
            is not the author of.

        .. code-block:: python

            me = await reddit.user.me()
            async for submission in me.submissions.new():
                await reddit.user.pin(submission)
                break

        """
        data = {
            "id": submission.fullname,
            "num": num,
            "state": state,
            "to_profile": True,
        }
        try:
            return await self._reddit.post(API_PATH["sticky_submission"], data=data)
        except Conflict:
            pass

    def subreddits(
        self, **generator_kwargs: str | int | dict[str, str]
    ) -> AsyncIterator[asyncpraw.models.Subreddit]:
        r"""Return a :class:`.ListingGenerator` of :class:`.Subreddit`\ s the user is subscribed to.

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        To print a list of the subreddits that you are subscribed to, try:

        .. code-block:: python

            async for subreddit in reddit.user.subreddits(limit=None):
                print(str(subreddit))

        """
        return ListingGenerator(
            self._reddit, API_PATH["my_subreddits"], **generator_kwargs
        )

    async def trusted(self) -> list[asyncpraw.models.Redditor]:
        r"""Return a :class:`.RedditorList` of trusted :class:`.Redditor`\ s.

        To display the usernames of your trusted users and the times at which you
        decided to trust them, try:

        .. code-block:: python

            trusted_users = await reddit.user.trusted()
            for user in trusted_users:
                print(f"User: {user.name}, time: {user.date}")

        """
        return await self._reddit.get(API_PATH["trusted"])
