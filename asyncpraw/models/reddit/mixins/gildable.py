"""Provide the GildableMixin class."""
from ....const import API_PATH


class GildableMixin:
    """Interface for classes that can be gilded."""

    async def gild(self):
        """Gild the author of the item.

        .. note:: Requires the authenticated user to own Reddit Coins.
                  Calling this method will consume Reddit Coins.

        Example usage:

        .. code-block:: python

            comment = await reddit.comment("dkk4qjd"), lazy=True
            await comment.gild()

            submission = await reddit.submission("8dmv8z", lazy=True)
            await submission.gild()

        """
        await self._reddit.post(API_PATH["gild_thing"].format(fullname=self.fullname))
