"""Provide the RisingListingMixin class."""
from typing import TYPE_CHECKING, Dict, AsyncGenerator, Union
from urllib.parse import urljoin

from ...base import PRAWBase
from ..generator import ListingGenerator

if TYPE_CHECKING:  # pragma: no cover
    from ...reddit.submission import Submission  # noqa: F401


class RisingListingMixin(PRAWBase):
    """Mixes in the rising methods."""

    def random_rising(
        self, **generator_kwargs: Union[str, int, Dict[str, str]]
    ) -> AsyncGenerator["Submission", None]:
        """Return a :class:`.ListingGenerator` for random rising submissions.

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        For example, to get random rising submissions for subreddit ``r/test``:

        .. code-block:: python

            subreddit = await reddit.subreddit('test')
            async for submission in subreddit.random_rising():
                print(submission.title)

        """
        return ListingGenerator(
            self._reddit, urljoin(self._path, "randomrising"), **generator_kwargs
        )

    def rising(
        self, **generator_kwargs: Union[str, int, Dict[str, str]]
    ) -> AsyncGenerator["Submission", None]:
        """Return a :class:`.ListingGenerator` for rising submissions.

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        For example, to get rising submissions for subreddit ``r/test``:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            async for submission in subreddit.rising():
                print(submission.title)

        """
        return ListingGenerator(
            self._reddit, urljoin(self._path, "rising"), **generator_kwargs
        )
