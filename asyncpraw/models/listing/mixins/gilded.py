"""Provide the GildedListingMixin class."""
from typing import Any, AsyncIterator, Dict, Union
from urllib.parse import urljoin

from ...base import AsyncPRAWBase
from ..generator import ListingGenerator


class GildedListingMixin(AsyncPRAWBase):
    """Mixes in the gilded method."""

    def gilded(
        self, **generator_kwargs: Union[str, int, Dict[str, str]]
    ) -> AsyncIterator[Any]:
        """Return a :class:`.ListingGenerator` for gilded items.

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        For example, to get gilded items in subreddit ``r/test``:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            async for item in subreddit.gilded():
                print(item.id)

        """
        return ListingGenerator(
            self._reddit, urljoin(self._path, "gilded"), **generator_kwargs
        )
