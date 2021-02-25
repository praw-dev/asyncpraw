"""Provide the SavableMixin class."""
from typing import Optional

from ....const import API_PATH


class SavableMixin:
    """Interface for RedditBase classes that can be saved."""

    async def save(self, category: Optional[str] = None):
        """Save the object.

        :param category: (Premium) The category to save to. If your user does not have
            Reddit Premium this value is ignored by Reddit (default: ``None``).

        Example usage:

        .. code-block:: python

            submission = await reddit.submission(id="5or86n", lazy=True)
            await submission.save(category="view later")

            comment = await reddit.comment(id="dxolpyc", lazy=True, lazy=True)
            await comment.save()

        .. seealso::

            :meth:`~.unsave`

        """
        await self._reddit.post(
            API_PATH["save"], data={"category": category, "id": self.fullname}
        )

    async def unsave(self):
        """Unsave the object.

        Example usage:

        .. code-block:: python

            submission = await reddit.submission(id="5or86n", lazy=True)
            await submission.unsave()

            comment = await reddit.comment(id="dxolpyc", lazy=True)
            await comment.unsave()

        .. seealso::

            :meth:`~.save`

        """
        await self._reddit.post(API_PATH["unsave"], data={"id": self.fullname})
