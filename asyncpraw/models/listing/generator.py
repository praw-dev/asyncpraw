"""Provide the ListingGenerator class."""
from copy import deepcopy
from typing import TYPE_CHECKING, Any, AsyncIterator, Dict, Optional, Union

from ..base import AsyncPRAWBase
from .listing import FlairListing, ModNoteListing

if TYPE_CHECKING:  # pragma: no cover
    import asyncpraw


class ListingGenerator(AsyncPRAWBase, AsyncIterator):
    """Instances of this class generate :class:`.RedditBase` instances.

    .. warning::

        This class should not be directly utilized. Instead, you will find a number of
        methods that return instances of the class here_.

    .. _here: https://asyncpraw.readthedocs.io/en/latest/search.html?q=ListingGenerator

    """

    def __init__(
        self,
        reddit: "asyncpraw.Reddit",
        url: str,
        limit: int = 100,
        params: Optional[Dict[str, Union[str, int]]] = None,
    ):
        """Initialize a :class:`.ListingGenerator` instance.

        :param reddit: An instance of :class:`.Reddit`.
        :param url: A URL returning a Reddit listing.
        :param limit: The number of content entries to fetch. If ``limit`` is ``None``,
            then fetch as many entries as possible. Most of Reddit's listings contain a
            maximum of 1000 items, and are returned 100 at a time. This class will
            automatically issue all necessary requests (default: ``100``).
        :param params: A dictionary containing additional query string parameters to
            send with the request.

        """
        super().__init__(reddit, _data=None)
        self._exhausted = False
        self._listing = None
        self._list_index = None
        self.limit = limit
        self.params = deepcopy(params) if params else {}
        self.params["limit"] = limit or 1024
        self.url = url
        self.yielded = 0

    def __aiter__(self) -> AsyncIterator[Any]:
        """Permit :class:`.ListingGenerator` to operate as an async iterator."""
        return self

    async def __anext__(self) -> Any:
        """Permit :class:`.ListingGenerator` to operate as a async generator."""
        if self.limit is not None and self.yielded >= self.limit:
            raise StopAsyncIteration()

        if self._listing is None or self._list_index >= len(self._listing):
            await self._next_batch()

        self._list_index += 1
        self.yielded += 1
        return self._listing[self._list_index - 1]

    def _extract_sublist(self, listing):
        if isinstance(listing, list):
            return listing[1]  # for submission duplicates
        elif isinstance(listing, dict):
            classes = [FlairListing, ModNoteListing]

            for listing_type in classes:
                if listing_type.CHILD_ATTRIBUTE in listing:
                    return listing_type(self._reddit, listing)
            else:
                raise ValueError(
                    "The generator returned a dictionary Async PRAW didn't"
                    " recognize. File a bug report at Async PRAW."
                )
        return listing

    async def _next_batch(self):
        if self._exhausted:
            raise StopAsyncIteration()

        self._listing = await self._reddit.get(self.url, params=self.params)
        self._listing = self._extract_sublist(self._listing)
        self._list_index = 0

        if not self._listing:
            raise StopAsyncIteration()

        if self._listing.after and self._listing.after != self.params.get(
            self._listing.AFTER_PARAM
        ):
            self.params[self._listing.AFTER_PARAM] = self._listing.after
        else:
            self._exhausted = True
