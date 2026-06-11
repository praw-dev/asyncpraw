"""Provide the ReportableMixin class."""

from __future__ import annotations

from typing import TYPE_CHECKING

from asyncpraw.const import API_PATH

if TYPE_CHECKING:
    import asyncpraw


class ReportableMixin:
    """Interface for :class:`.RedditBase` classes that can be reported."""

    if TYPE_CHECKING:
        # Provided by the host class (:class:`.RedditBase`).
        _reddit: asyncpraw.Reddit

        @property
        def fullname(self) -> str: ...  # noqa: D102

    async def report(self, reason: str) -> None:
        """Report this object to the moderators of its subreddit.

        :param reason: The reason for reporting.

        :raises: :class:`.RedditAPIException` if ``reason`` is longer than 100
            characters.

        Example usage:

        .. code-block:: python

            submission = await reddit.submission("5or86n", fetch=False)
            await submission.report("report reason")

            comment = await reddit.comment("dxolpyc", fetch=False)
            await comment.report("report reason")

        """
        await self._reddit.post(API_PATH["report"], data={"id": self.fullname, "reason": reason})
