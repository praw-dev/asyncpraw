"""Provide the SavableMixin class."""

from __future__ import annotations

from typing import TYPE_CHECKING

from asyncpraw.const import API_PATH

if TYPE_CHECKING:
    import asyncpraw


class SavableMixin:
    """Interface for :class:`.RedditBase` classes that can be saved."""

    if TYPE_CHECKING:
        # Provided by the host class (:class:`.RedditBase`).
        _reddit: asyncpraw.Reddit

        @property
        def fullname(self) -> str: ...  # noqa: D102

    async def save(self, *, category: str | None = None) -> None:
        """Save the object.

        :param category: The category to save to. If the authenticated user does not
            have Reddit Premium this value is ignored by Reddit (default: ``None``).

        Example usage:

        .. code-block:: python

            submission = await reddit.submission("5or86n", fetch=False)
            await submission.save(category="view later")

            comment = await reddit.comment("dxolpyc", fetch=False)
            await comment.save()

        .. seealso::

            :meth:`.unsave`

        """
        await self._reddit.post(API_PATH["save"], data={"category": category, "id": self.fullname})

    async def unsave(self) -> None:
        """Unsave the object.

        Example usage:

        .. code-block:: python

            submission = await reddit.submission("5or86n", fetch=False)
            await submission.unsave()

            comment = await reddit.comment("dxolpyc", fetch=False)
            await comment.unsave()

        .. seealso::

            :meth:`.save`

        """
        await self._reddit.post(API_PATH["unsave"], data={"id": self.fullname})
