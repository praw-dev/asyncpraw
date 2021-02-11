"""Provide the ReportableMixin class."""
from ....const import API_PATH


class ReportableMixin:
    """Interface for RedditBase classes that can be reported."""

    async def report(self, reason: str):
        """Report this object to the moderators of its subreddit.

        :param reason: The reason for reporting.

        :raises: :class:`.RedditAPIException` if ``reason`` is longer than 100
            characters.

        Example usage:

        .. code-block:: python

            submission = await reddit.submission(id="5or86n", lazy=True)
            await submission.report("report reason")

            comment = await reddit.comment(id="dxolpyc", lazy=True)
            await comment.report("report reason")

        """
        await self._reddit.post(
            API_PATH["report"], data={"id": self.fullname, "reason": reason}
        )
