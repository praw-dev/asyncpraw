"""Provide the SubredditStream class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from asyncpraw.models.util import stream_generator

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    import asyncpraw.models


class SubredditStream:
    """Provides submission and comment streams."""

    def __init__(self, subreddit: asyncpraw.models.Subreddit) -> None:
        """Initialize a :class:`.SubredditStream` instance.

        :param subreddit: The subreddit associated with the streams.

        """
        self.subreddit = subreddit

    def comments(self, **stream_options: Any) -> AsyncIterator[asyncpraw.models.Comment]:
        """Yield new comments as they become available.

        Comments are yielded oldest first. Up to 100 historical comments will initially
        be returned.

        Keyword arguments are passed to :func:`.stream_generator`.

        .. note::

            While Async PRAW tries to catch all new comments, some high-volume streams,
            especially the r/all stream, may drop some comments.

        For example, to retrieve all new comments made to r/test, try:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            async for comment in subreddit.stream.comments():
                print(comment)

        To only retrieve new submissions starting when the stream is created, pass
        ``skip_existing=True``:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            async for comment in subreddit.stream.comments(skip_existing=True):
                print(comment)

        """
        return stream_generator(self.subreddit.comments, **stream_options)

    def submissions(self, **stream_options: Any) -> AsyncIterator[asyncpraw.models.Submission]:
        r"""Yield new :class:`.Submission`\ s as they become available.

        Submissions are yielded oldest first. Up to 100 historical submissions will
        initially be returned.

        Keyword arguments are passed to :func:`.stream_generator`.

        .. note::

            While Async PRAW tries to catch all new submissions, some high-volume
            streams, especially the r/all stream, may drop some submissions.

        For example, to retrieve all new submissions made to all of Reddit, try:

        .. code-block:: python

            subreddit = await reddit.subreddit("all")
            async for submission in subreddit.stream.submissions():
                print(submission)

        """
        return stream_generator(self.subreddit.new, **stream_options)
