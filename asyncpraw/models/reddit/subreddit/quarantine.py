"""Provide the SubredditQuarantine class."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from asyncprawcore import Redirect

from asyncpraw.const import API_PATH

if TYPE_CHECKING:
    import asyncpraw.models


class SubredditQuarantine:
    """Provides subreddit quarantine related methods.

    To opt-in into a quarantined subreddit:

    .. code-block:: python

        subreddit = await reddit.subreddit("test")
        await subreddit.quaran.opt_in()

    """

    def __init__(self, subreddit: asyncpraw.models.Subreddit) -> None:
        """Initialize a :class:`.SubredditQuarantine` instance.

        :param subreddit: The :class:`.Subreddit` associated with the quarantine.

        """
        self.subreddit = subreddit

    async def opt_in(self) -> None:
        """Permit your user access to the quarantined subreddit.

        Usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("QUESTIONABLE")
            async for submission in subreddit.hot():  # Raises asyncprawcore.Forbidden
                print(submission)

            await subreddit.quaran.opt_in()
            async for submission in subreddit.hot():
                print(submission)  # Returns Submission

        """
        data = {"sr_name": self.subreddit}
        with contextlib.suppress(Redirect):
            await self.subreddit._reddit.post(API_PATH["quarantine_opt_in"], data=data)

    async def opt_out(self) -> None:
        """Remove access to the quarantined subreddit.

        Usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("QUESTIONABLE")
            async for submission in subreddit.hot():
                print(submission)  # Returns Submission

            await subreddit.quaran.opt_out()
            async for submission in subreddit.hot():  # Raises asyncprawcore.Forbidden
                print(submission)

        """
        data = {"sr_name": self.subreddit}
        with contextlib.suppress(Redirect):
            await self.subreddit._reddit.post(API_PATH["quarantine_opt_out"], data=data)
