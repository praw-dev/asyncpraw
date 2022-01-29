"""Provide the BaseListingMixin class."""
from typing import Any, AsyncIterator, Dict, Union
from urllib.parse import urljoin

from ....util import _deprecate_args
from ...base import AsyncPRAWBase
from ..generator import ListingGenerator


class BaseListingMixin(AsyncPRAWBase):
    """Adds minimum set of methods that apply to all listing objects."""

    VALID_TIME_FILTERS = {"all", "day", "hour", "month", "week", "year"}

    @staticmethod
    def _validate_time_filter(time_filter):
        """Validate ``time_filter``.

        :raises: :py:class:`.ValueError` if ``time_filter`` is not valid.

        """
        if time_filter not in BaseListingMixin.VALID_TIME_FILTERS:
            valid_time_filters = ", ".join(BaseListingMixin.VALID_TIME_FILTERS)
            raise ValueError(f"time_filter must be one of: {valid_time_filters}")

    def _prepare(self, *, arguments, sort):
        """Fix for :class:`.Redditor` methods that use a query param rather than subpath."""
        if self.__dict__.get("_listing_use_sort"):
            self._safely_add_arguments(arguments=arguments, key="params", sort=sort)
            return self._path
        return urljoin(self._path, sort)

    @_deprecate_args("time_filter")
    def controversial(
        self,
        *,
        time_filter: str = "all",
        **generator_kwargs: Union[str, int, Dict[str, str]],
    ) -> AsyncIterator[Any]:
        """Return a :class:`.ListingGenerator` for controversial items.

        :param time_filter: Can be one of: ``"all"``, ``"day"``, ``"hour"``,
            ``"month"``, ``"week"``, or ``"year"`` (default: ``"all"``).

        :raises: :py:class:`ValueError` if ``time_filter`` is invalid.

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        This method can be used like:

        .. code-block:: python

            reddit.domain("imgur.com").controversial(time_filter="week")

            multireddit = await reddit.multireddit(redditor="samuraisam", name="programming")
            multireddit.controversial(time_filter="day")

            redditor = await reddit.redditor("spez")
            redditor.controversial(time_filter="month")

            redditor = await reddit.redditor("spez")
            redditor.comments.controversial(time_filter="year")

            redditor = await reddit.redditor("spez")
            redditor.submissions.controversial(time_filter="all")

            subreddit = await reddit.subreddit("all")
            subreddit.controversial(time_filter="hour")

        """
        self._validate_time_filter(time_filter)
        self._safely_add_arguments(
            arguments=generator_kwargs, key="params", t=time_filter
        )
        url = self._prepare(arguments=generator_kwargs, sort="controversial")
        return ListingGenerator(self._reddit, url, **generator_kwargs)

    def hot(
        self, **generator_kwargs: Union[str, int, Dict[str, str]]
    ) -> AsyncIterator[Any]:
        """Return a :class:`.ListingGenerator` for hot items.

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        This method can be used like:

        .. code-block:: python

            reddit.domain("imgur.com").hot()

            multireddit = await reddit.multireddit(redditor="samuraisam", name="programming")
            multireddit.hot()

            redditor = await reddit.redditor("spez")
            redditor.hot()

            redditor = await reddit.redditor("spez")
            redditor.comments.hot()

            redditor = await reddit.redditor("spez")
            redditor.submissions.hot()

            subreddit = await reddit.subreddit("all")
            subreddit.hot()

        """
        generator_kwargs.setdefault("params", {})
        url = self._prepare(arguments=generator_kwargs, sort="hot")
        return ListingGenerator(self._reddit, url, **generator_kwargs)

    def new(
        self, **generator_kwargs: Union[str, int, Dict[str, str]]
    ) -> AsyncIterator[Any]:
        """Return a :class:`.ListingGenerator` for new items.

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        This method can be used like:

        .. code-block:: python

            reddit.domain("imgur.com").new()

            multireddit = await reddit.multireddit(redditor="samuraisam", name="programming")
            multireddit.new()

            redditor = await reddit.redditor("spez")
            redditor.new()

            redditor = await reddit.redditor("spez")
            redditor.comments.new()

            redditor = await reddit.redditor("spez")
            redditor.submissions.new()

            subreddit = await reddit.subreddit("all")
            subreddit.new()

        """
        generator_kwargs.setdefault("params", {})
        url = self._prepare(arguments=generator_kwargs, sort="new")
        return ListingGenerator(self._reddit, url, **generator_kwargs)

    @_deprecate_args("time_filter")
    def top(
        self,
        *,
        time_filter: str = "all",
        **generator_kwargs: Union[str, int, Dict[str, str]],
    ) -> AsyncIterator[Any]:
        """Return a :class:`.ListingGenerator` for top items.

        :param time_filter: Can be one of: ``"all"``, ``"day"``, ``"hour"``,
            ``"month"``, ``"week"``, or ``"year "``(default: ``"all"``).

        :raises: :py:class:`ValueError` if ``time_filter`` is invalid.

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        This method can be used like:

        .. code-block:: python

            reddit.domain("imgur.com").top(time_filter="week")

            multireddit = await reddit.multireddit(redditor="samuraisam", name="programming")
            multireddit.top(time_filter="day")

            redditor = await reddit.redditor("spez")
            redditor.top(time_filter="month")

            redditor = await reddit.redditor("spez")
            redditor.comments.top(time_filter="year")

            redditor = await reddit.redditor("spez")
            redditor.submissions.top(time_filter="all")

            subreddit = await reddit.subreddit("all")
            subreddit.top(time_filter="hour")

        """
        self._validate_time_filter(time_filter)
        self._safely_add_arguments(
            arguments=generator_kwargs, key="params", t=time_filter
        )
        url = self._prepare(arguments=generator_kwargs, sort="top")
        return ListingGenerator(self._reddit, url, **generator_kwargs)
