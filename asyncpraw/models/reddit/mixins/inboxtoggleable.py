"""Provide the InboxToggleableMixin class."""

from __future__ import annotations

from typing import TYPE_CHECKING

from asyncpraw.const import API_PATH

if TYPE_CHECKING:
    import asyncpraw


class InboxToggleableMixin:
    """Interface for classes that can optionally receive inbox replies."""

    if TYPE_CHECKING:
        # Provided by the host class (:class:`.RedditBase`).
        _reddit: asyncpraw.Reddit

        @property
        def fullname(self) -> str: ...  # noqa: D102

    async def disable_inbox_replies(self) -> None:
        """Disable inbox replies for the item.

        .. note::

            This can only apply to items created by the authenticated user.

        Example usage:

        .. code-block:: python

            comment = await reddit.comment("dkk4qjd", fetch=False)
            await comment.disable_inbox_replies()

            submission = await reddit.submission("8dmv8z", fetch=False)
            await submission.disable_inbox_replies()

        .. seealso::

            :meth:`.enable_inbox_replies`

        """
        await self._reddit.post(API_PATH["sendreplies"], data={"id": self.fullname, "state": False})

    async def enable_inbox_replies(self) -> None:
        """Enable inbox replies for the item.

        .. note::

            This can only apply to items created by the authenticated user.

        Example usage:

        .. code-block:: python

            comment = await reddit.comment("dkk4qjd", fetch=False)
            await comment.enable_inbox_replies()

            submission = await reddit.submission("8dmv8z", fetch=False)
            await submission.enable_inbox_replies()

        .. seealso::

            :meth:`.disable_inbox_replies`

        """
        await self._reddit.post(API_PATH["sendreplies"], data={"id": self.fullname, "state": True})
