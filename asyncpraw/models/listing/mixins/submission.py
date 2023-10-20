"""Provide the SubmissionListingMixin class."""
from __future__ import annotations

from typing import TYPE_CHECKING, AsyncIterator

from ....const import API_PATH
from ...base import AsyncPRAWBase
from ..generator import ListingGenerator

if TYPE_CHECKING:  # pragma: no cover
    import asyncpraw


class SubmissionListingMixin(AsyncPRAWBase):
    """Adds additional methods pertaining to :class:`.Submission` instances."""

    def duplicates(
        self, **generator_kwargs: str | int | dict[str, str]
    ) -> AsyncIterator[asyncpraw.models.Submission]:
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
