"""Provide the GildedListingMixin class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, AsyncIterator
from urllib.parse import urljoin

from ...base import AsyncPRAWBase
from ..generator import ListingGenerator

if TYPE_CHECKING:
    from collections.abc import Iterator


class GildedListingMixin(AsyncPRAWBase):
    """Mixes in the gilded method."""

    def gilded(
        self, **generator_kwargs: str | int | dict[str, str]
    ) -> AsyncIterator[Any]:
        """Return a :class:`.ListingGenerator` for gilded items.

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        For example, to get gilded items in r/test:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            async for item in subreddit.gilded():
                print(item.id)

        """
        return ListingGenerator(
            self._reddit, urljoin(self._path, "gilded"), **generator_kwargs
        )
