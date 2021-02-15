"""Provide CommentForest for Submission comments."""
import inspect
from heapq import heappop, heappush
from typing import TYPE_CHECKING, Any, AsyncIterator, Coroutine, List, Optional, Union
from warnings import warn

from ..exceptions import DuplicateReplaceException
from .reddit.more import MoreComments

if TYPE_CHECKING:  # pragma: no cover
    import asyncpraw


class CommentForest:
    """A forest of comments starts with multiple top-level comments.

    Each of these comments can be a tree of replies.

    """

    @staticmethod
    def _gather_more_comments(tree, parent_tree=None):
        """Return a list of :class:`.MoreComments` objects obtained from tree."""
        more_comments = []
        queue = [(None, x) for x in tree]
        while queue:
            parent, comment = queue.pop(0)
            if isinstance(comment, MoreComments):
                heappush(more_comments, comment)
                if parent:
                    comment._remove_from = parent.replies._comments
                else:
                    comment._remove_from = parent_tree or tree
            else:
                for item in comment.replies:
                    queue.append((comment, item))
        return more_comments

    def __getitem__(self, index: int):
        """Return the comment at position ``index`` in the list.

        This method is to be used like an array access, such as:

        .. code-block:: python

            first_comment = submission.comments[0]

        Alternatively, the presence of this method enables one to iterate over all top
        level comments, like so:

        .. code-block:: python

            for comment in submission.comments:
                print(comment.body)

        """
        if not (self._comments is not None or self._submission._fetched):
            raise TypeError(
                "Submission must be fetched before comments are accessible. Call `.load()` to fetch."
            )
        return self._comments[index]

    async def __aiter__(self) -> AsyncIterator["asyncpraw.models.Comment"]:
        """Allow CommentForest to be used as an AsyncIterator.

        This method enables one to iterate over all top_level comments, like so:

        .. code-block:: python

            comments = submission.comments
            async for comment in comments:
                print(comment.body)

        """
        warn(
            "Using CommentForest as an asynchronous iterator has been deprecated and"
            " will be removed in a future version.",
            category=DeprecationWarning,
            stacklevel=3,
        )
        for comment in self:
            yield comment

    async def __call__(self):  # noqa: D102
        warn(
            "`Submission.comments` is now a property and no longer needs to be awaited. This"
            " will raise an error in a future version of Async PRAW.",
            category=DeprecationWarning,
            stacklevel=3,
        )
        if not self._submission._fetched:
            await self._submission._fetch()
        self._comments = self._submission.comments._comments
        return self

    def __init__(
        self,
        submission: "asyncpraw.models.Submission",
        comments: Optional[List["asyncpraw.models.Comment"]] = None,
    ):
        """Initialize a :class:`.CommentForest` instance.

        :param submission: An instance of :class:`.Submission` that is the parent of the
            comments.
        :param comments: Initialize the Forest with a list of comments (default: None).

        """
        self._comments = comments
        self._submission = submission

    def __len__(self) -> int:
        """Return the number of top-level comments in the forest."""
        return len(self._comments or [])

    def _insert_comment(self, comment):
        if comment.name in self._submission._comments_by_id:
            raise DuplicateReplaceException
        comment.submission = self._submission
        if isinstance(comment, MoreComments) or comment.is_root:
            self._comments.append(comment)
        else:
            assert comment.parent_id in self._submission._comments_by_id, (
                "Async PRAW Error occurred. Please file a bug report and include the"
                " code that caused the error."
            )
            parent = self._submission._comments_by_id[comment.parent_id]
            parent.replies._comments.append(comment)

    def _update(self, comments):
        self._comments = comments
        for comment in comments:
            comment.submission = self._submission

    def list(
        self,
    ) -> Union[
        List[Union["asyncpraw.models.Comment", "asyncpraw.models.MoreComments"]],
        Coroutine[
            Any,
            Any,
            List[Union["asyncpraw.models.Comment", "asyncpraw.models.MoreComments"]],
        ],
    ]:
        """Return a flattened list of all Comments.

        This list may contain :class:`.MoreComments` instances if :meth:`.replace_more`
        was not called first.

        """
        comments = []
        queue = list(self)
        while queue:
            comment = queue.pop(0)
            comments.append(comment)
            if not isinstance(comment, MoreComments):
                queue.extend(comment.replies)
        # check if this got called with await
        # I'm so sorry this is really gross
        if any(
            [
                "await" in context
                for context in inspect.getframeinfo(
                    inspect.currentframe().f_back
                ).code_context
            ]
        ):

            async def async_func():
                warn(
                    "`CommentForest.list()` no longer needs to be awaited and this"
                    " will raise an error in a future version of Async PRAW.",
                    category=DeprecationWarning,
                    stacklevel=3,
                )
                return comments

            return async_func()
        return comments

    async def replace_more(
        self, limit: int = 32, threshold: int = 0
    ) -> List["asyncpraw.models.MoreComments"]:
        """Update the comment forest by resolving instances of MoreComments.

        :param limit: The maximum number of :class:`.MoreComments` instances to replace.
            Each replacement requires 1 API request. Set to ``None`` to have no limit,
            or to ``0`` to remove all :class:`.MoreComments` instances without
            additional requests (default: 32).
        :param threshold: The minimum number of children comments a
            :class:`.MoreComments` instance must have in order to be replaced.
            :class:`.MoreComments` instances that represent "continue this thread" links
            unfortunately appear to have 0 children. (default: 0).

        :returns: A list of :class:`.MoreComments` instances that were not replaced.

        :raises: ``asyncprawcore.TooManyRequests`` when used concurrently.

        For example, to replace up to 32 :class:`.MoreComments` instances of a
        submission try:

        .. code-block:: python

            submission = await reddit.submission("3hahrw", fetch=False)
            await submission.comments.replace_more()

        Alternatively, to replace :class:`.MoreComments` instances within the replies of
        a single comment try:

        .. code-block:: python

            comment = await reddit.comment("d8r4im1", fetch=False)
            await comment.refresh()
            await comment.replies.replace_more()

        .. note::

            This method can take a long time as each replacement will discover at most
            100 new :class:`.Comment` instances. As a result, consider looping and
            handling exceptions until the method returns successfully. For example:

            .. code-block:: python

                while True:
                    try:
                        await submission.comments.replace_more()
                        break
                    except PossibleExceptions:
                        print("Handling replace_more exception")
                        await asyncio.sleep(1)

        .. warning::

            If this method is called, and the comments are refreshed, calling this
            method again will result in a :class:`.DuplicateReplaceException`.

        """
        remaining = limit
        more_comments = self._gather_more_comments(self._comments)
        skipped = []

        # Fetch largest more_comments until reaching the limit or the threshold
        while more_comments:
            item = heappop(more_comments)
            if remaining is not None and remaining <= 0 or item.count < threshold:
                skipped.append(item)
                item._remove_from.remove(item)
                continue

            new_comments = await item.comments(update=False)
            if remaining is not None:
                remaining -= 1

            # Add new MoreComment objects to the heap of more_comments
            for more in self._gather_more_comments(new_comments, self._comments):
                more.submission = self._submission
                heappush(more_comments, more)
            # Insert all items into the tree
            for comment in new_comments:
                self._insert_comment(comment)

            # Remove from forest
            item._remove_from.remove(item)

        return more_comments + skipped
