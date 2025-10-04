"""Provide the SubmissionListingMixin class."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

from asyncpraw.const import API_PATH
from asyncpraw.models.base import AsyncPRAWBase
from asyncpraw.models.listing.generator import ListingGenerator

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import AsyncIterator

    import asyncpraw.models


class SubmissionListingMixin(AsyncPRAWBase):
    """Adds additional methods pertaining to :class:`.Submission` instances."""

    def duplicates(self, **generator_kwargs: str | int | dict[str, str]) -> AsyncIterator[asyncpraw.models.Submission]:
        """Return a :class:`.ListingGenerator` for the submission's duplicates.

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        Example usage:

        .. code-block:: python

            submission = await reddit.submission("5or86n", fetch=False)

            async for duplicate in submission.duplicates():
                # process each duplicate
                ...

        .. seealso::

            :meth:`.upvote`

        """
        url = API_PATH["duplicates"].format(submission_id=self.id)
        return ListingGenerator(self._reddit, url, **generator_kwargs)
