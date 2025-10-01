"""Provide the SubredditListingMixin class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

from asyncpraw.models.base import AsyncPRAWBase
from asyncpraw.models.listing.generator import ListingGenerator
from asyncpraw.models.listing.mixins.base import BaseListingMixin
from asyncpraw.models.listing.mixins.rising import RisingListingMixin
from asyncpraw.util.cache import cachedproperty

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import AsyncIterator

    import asyncpraw.models


class CommentHelper(AsyncPRAWBase):
    """Provide a set of functions to interact with a :class:`.Subreddit`'s comments."""

    @property
    def _path(self) -> str:
        return urljoin(self.subreddit._path, "comments/")

    def __call__(self, **generator_kwargs: str | int | dict[str, str]) -> AsyncIterator[asyncpraw.models.Comment]:
        """Return a :class:`.ListingGenerator` for the :class:`.Subreddit`'s comments.

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        This method should be used in a way similar to the example below:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            async for comment in subreddit.comments(limit=25):
                print(comment.author)

        """
        return ListingGenerator(self._reddit, self._path, **generator_kwargs)

    def __init__(self, subreddit: asyncpraw.models.Subreddit | SubredditListingMixin) -> None:
        """Initialize a :class:`.CommentHelper` instance."""
        super().__init__(subreddit._reddit, _data=None)
        self.subreddit = subreddit


class SubredditListingMixin(BaseListingMixin, RisingListingMixin):
    """Adds additional methods pertaining to subreddit-like instances."""

    @cachedproperty
    def comments(self) -> CommentHelper:
        """Provide an instance of :class:`.CommentHelper`.

        For example, to output the author of the 25 most recent comments of r/test
        execute:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            async for comment in subreddit.comments(limit=25):
                print(comment.author)

        """
        return CommentHelper(self)

    def __init__(self, reddit: asyncpraw.Reddit, _data: dict[str, Any] | None) -> None:
        """Initialize a :class:`.SubredditListingMixin` instance.

        :param reddit: An instance of :class:`.Reddit`.

        """
        super().__init__(reddit, _data=_data)
