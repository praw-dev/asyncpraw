"""Provide the SubmissionListingMixin class."""
from typing import TYPE_CHECKING, AsyncIterator, Dict, Union

from ....const import API_PATH
from ...base import AsyncPRAWBase
from ..generator import ListingGenerator

if TYPE_CHECKING:  # pragma: no cover
    from ..... import asyncpraw


class SubmissionListingMixin(AsyncPRAWBase):
    """Adds additional methods pertaining to Submission instances."""

    def duplicates(
        self, **generator_kwargs: Union[str, int, Dict[str, str]]
    ) -> AsyncIterator["asyncpraw.models.Submission"]:
        """Return a :class:`.ListingGenerator` for the submission's duplicates.

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        Example usage:

        .. code-block:: python

            submission = await reddit.submission(id="5or86n", lazy=True)

            async for duplicate in submission.duplicates():
                # process each duplicate
                ...

        .. seealso::

            :meth:`~.upvote`

        """
        url = API_PATH["duplicates"].format(submission_id=self.id)
        return ListingGenerator(self._reddit, url, **generator_kwargs)
