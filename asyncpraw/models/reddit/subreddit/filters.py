"""Provide the SubredditFilters class."""

from __future__ import annotations

from json import dumps
from typing import TYPE_CHECKING

from asyncpraw.const import API_PATH

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    import asyncpraw.models


class SubredditFilters:
    """Provide functions to interact with the special :class:`.Subreddit`'s filters.

    Members of this class should be utilized via :meth:`.Subreddit.filters`. For
    example, to add a filter, run:

    .. code-block:: python

        subreddit = await reddit.subreddit("all")
        await subreddit.filters.add("test")

    """

    async def __aiter__(
        self,
    ) -> AsyncIterator[asyncpraw.models.Subreddit]:
        """Iterate through the special :class:`.Subreddit`'s filters.

        This method should be invoked as:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            async for subreddit in subreddit.filters:
                ...

        """
        user = await self.subreddit._reddit.user.me()
        url = API_PATH["subreddit_filter_list"].format(special=self.subreddit, user=user)
        params: dict[str, str | int] = {"unique": self.subreddit._reddit._next_unique}
        response_data = await self.subreddit._reddit.get(url, params=params)
        for subreddit in response_data.subreddits:
            yield subreddit

    def __init__(self, subreddit: asyncpraw.models.Subreddit) -> None:
        """Initialize a :class:`.SubredditFilters` instance.

        :param subreddit: The special subreddit whose filters to work with.

        As of this writing filters can only be used with the special subreddits ``all``
        and ``mod``.

        """
        self.subreddit = subreddit

    async def add(self, subreddit: asyncpraw.models.Subreddit | str) -> None:
        """Add ``subreddit`` to the list of filtered subreddits.

        :param subreddit: The subreddit to add to the filter list.

        Items from subreddits added to the filtered list will no longer be included when
        obtaining listings for r/all.

        Alternatively, you can filter a subreddit temporarily from a special listing in
        a manner like so:

        .. code-block:: python

            await reddit.subreddit("all-redditdev-learnpython")

        :raises: ``asyncprawcore.NotFound`` when calling on a non-special subreddit.

        """
        user = await self.subreddit._reddit.user.me()
        url = API_PATH["subreddit_filter"].format(
            special=self.subreddit,
            user=user,
            subreddit=subreddit,
        )
        await self.subreddit._reddit.put(url, data={"model": dumps({"name": str(subreddit)})})

    async def remove(self, subreddit: asyncpraw.models.Subreddit | str) -> None:
        """Remove ``subreddit`` from the list of filtered subreddits.

        :param subreddit: The subreddit to remove from the filter list.

        :raises: ``asyncprawcore.NotFound`` when calling on a non-special subreddit.

        """
        user = await self.subreddit._reddit.user.me()
        url = API_PATH["subreddit_filter"].format(
            special=self.subreddit,
            user=user,
            subreddit=subreddit,
        )
        await self.subreddit._reddit.delete(url)
