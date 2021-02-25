"""Provide the Removal Reason class."""
from typing import TYPE_CHECKING, Any, AsyncIterator, Dict, List, Optional, Union
from warnings import warn

from ...const import API_PATH
from ...exceptions import ClientException
from .base import RedditBase

if TYPE_CHECKING:  # pragma: no cover
    from .... import asyncpraw


class RemovalReason(RedditBase):
    """An individual Removal Reason object.

    **Typical Attributes**

    This table describes attributes that typically belong to objects of this class.
    Since attributes are dynamically provided (see
    :ref:`determine-available-attributes-of-an-object`), there is not a guarantee that
    these attributes will always be present, nor is this list necessarily complete.

    =========== ==================================
    Attribute   Description
    =========== ==================================
    ``id``      The id of the removal reason.
    ``message`` The message of the removal reason.
    ``title``   The title of the removal reason.
    =========== ==================================

    """

    STR_FIELD = "id"

    @staticmethod
    def _warn_reason_id(reason_id_value: Optional[str], id_value: Optional[str]):
        """Reason id param is deprecated. Warns if it's used.

        :param reason_id_value: The value passed as parameter ``reason_id``.
        :param id_value: Returns the actual value of parameter ``id`` is parameter
            ``reason_id`` is not used.

        """
        if reason_id_value is not None:
            warn(
                "Parameter ``reason_id`` is deprecated. Either use positional"
                ' arguments (reason_id="x" -> "x") or change the parameter '
                'name to ``id`` (reason_id="x" -> id="x"). The parameter will'
                " be removed in Async PRAW 8.",
                category=DeprecationWarning,
                stacklevel=3,
            )
            return reason_id_value
        return id_value

    def __eq__(self, other: Union[str, "RemovalReason"]) -> bool:
        """Return whether the other instance equals the current."""
        if isinstance(other, str):
            return other == str(self)
        return isinstance(other, self.__class__) and str(self) == str(other)

    def __hash__(self) -> int:
        """Return the hash of the current instance."""
        return hash(self.__class__.__name__) ^ hash(str(self))

    def __init__(
        self,
        reddit: "asyncpraw.Reddit",
        subreddit: "asyncpraw.models.Subreddit",
        id: Optional[str] = None,  # pylint: disable=redefined-builtin
        reason_id: Optional[str] = None,
        _data: Optional[Dict[str, Any]] = None,
    ):
        """Construct an instance of the Removal Reason object.

        :param reddit: An instance of :class:`.Reddit`.
        :param subreddit: An instance of :class:`.Subreddit`.
        :param id: The id of the removal reason.
        :param reason_id: (Deprecated) The original name of the ``id`` parameter. Used
            for backwards compatibility. This parameter should not be used.

        """
        id = self._warn_reason_id(reason_id, id)
        if (id, _data).count(None) != 1:
            raise ValueError("Either id or _data needs to be given.")

        if id:
            self.id = id
        self.subreddit = subreddit
        super().__init__(reddit, _data=_data)

    async def _fetch(self):
        async for removal_reason in self.subreddit.mod.removal_reasons:
            if removal_reason.id == self.id:
                self.__dict__.update(removal_reason.__dict__)
                self._fetched = True
                return
        raise ClientException(
            f"Subreddit {self.subreddit} does not have the removal reason {self.id}"
        )

    async def delete(self):
        """Delete a removal reason from this subreddit.

        To delete ``"141vv5c16py7d"`` from the subreddit ``"NAME"`` try:

        .. code-block:: python

            subreddit = await reddit.subreddit("NAME")
            reason = await subreddit.mod.removal_reasons.get_reason("141vv5c16py7d")
            await reason.delete()

        """
        url = API_PATH["removal_reason"].format(subreddit=self.subreddit, id=self.id)
        await self._reddit.delete(url)

    async def update(self, message: Optional[str] = None, title: Optional[str] = None):
        """Update the removal reason from this subreddit.

        .. note::

            Existing values will be used for any unspecified arguments.

        :param message: The removal reason's new message.
        :param title: The removal reason's new title.

        To update ``"141vv5c16py7d"`` from the subreddit ``"NAME"`` try:

        .. code-block:: python

            subreddit = await reddit.subreddit("NAME")
            reason = await subreddit.mod.removal_reasons.get_reason("141vv5c16py7d")
            await reason.update(message="New message", title="New title")

        """
        url = API_PATH["removal_reason"].format(subreddit=self.subreddit, id=self.id)
        data = {
            name: getattr(self, name) if value is None else value
            for name, value in {"message": message, "title": title}.items()
        }
        await self._reddit.put(url, data=data)


class SubredditRemovalReasons:
    """Provide a set of functions to a Subreddit's removal reasons."""

    async def get_reason(
        self, reason_id: Union[str, int, slice], lazy: bool = False
    ) -> RemovalReason:
        """Return the Removal Reason with the ID/number/slice ``reason_id``.

        :param reason_id: The ID or index of the removal reason
        :param lazy: If True, object is loaded lazily (default: False).

        This method is to be used to fetch a specific removal reason, like so:

        .. code-block:: python

            reason_id = "141vv5c16py7d"
            subreddit = await reddit.subreddit("NAME")
            reason = await subreddit.mod.removal_reasons.get_reason(reason_id)
            print(reason)

        You can also use indices to get a numbered removal reason. Since Python uses
        0-indexing, the first removal reason is index 0, and so on.

        .. note::

            Both negative indices and slices can be used to interact with the removal
            reasons.

        :raises: :py:class:`IndexError` if a removal reason of a specific number does
            not exist.

        For example, to get the second removal reason of the subreddit ``"NAME"``:

        .. code-block:: python

            subreddit = await reddit.subreddit("NAME")
            await subreddit.mod.removal_reasons.get_reason(1)

        To get the last three removal reasons in a subreddit:

        .. code-block:: python

            subreddit = await reddit.subreddit("NAME")
            reasons = await subreddit.mod.removal_reasons.get_reason(slice(-3, None))
            for reason in reasons:
                print(reason)

        If you don't need the object fetched right away (e.g., to utilize a class
        method) you can do:

        .. code-block:: python

            reason_id = "141vv5c16py7d"
            subreddit = await reddit.subreddit("NAME")
            reason = await subreddit.mod.removal_reasons.get_reason(reason_id, lazy=True)
            await reason.delete()

        """
        if not isinstance(reason_id, str):
            reasons = await self._removal_reason_list()
            return reasons[reason_id]
        else:
            reason = RemovalReason(self._reddit, self.subreddit, reason_id)
        if not lazy:
            await reason._fetch()
        return reason

    def __init__(self, subreddit: "asyncpraw.models.Subreddit"):
        """Create a SubredditRemovalReasons instance.

        :param subreddit: The subreddit whose removal reasons to work with.

        """
        self.subreddit = subreddit
        self._reddit = subreddit._reddit

    async def __aiter__(self) -> AsyncIterator[RemovalReason]:
        """Return a list of Removal Reasons for the subreddit.

        This method is used to discover all removal reasons for a subreddit:

        .. code-block:: python

            subreddit = await reddit.subreddit("NAME")
            async for removal_reason in subreddit.mod.removal_reasons:
                print(removal_reason)

        """
        for reason in await self._removal_reason_list():
            yield reason

    async def _removal_reason_list(self) -> List[RemovalReason]:
        """Get a list of Removal Reason objects.

        :returns: A list of instances of :class:`.RemovalReason`.

        """
        response = await self._reddit.get(
            API_PATH["removal_reasons_list"].format(subreddit=self.subreddit)
        )
        return [
            RemovalReason(self._reddit, self.subreddit, _data=reason_data)
            for id, reason_data in response["data"].items()
        ]

    async def add(self, message: str, title: str) -> RemovalReason:
        """Add a removal reason to this subreddit.

        :param message: The message associated with the removal reason.
        :param title: The title of the removal reason

        :returns: The RemovalReason added.

        The message will be prepended with `Hi u/username,` automatically.

        To add ``"Test"`` to the subreddit ``"NAME"`` try:

        .. code-block:: python

            subreddit = await reddit.subreddit("NAME")
            await subreddit.mod.removal_reasons.add(message="Foobar", title="Test")

        """
        data = {"message": message, "title": title}
        url = API_PATH["removal_reasons_list"].format(subreddit=self.subreddit)
        id = await self._reddit.post(url, data=data)
        return RemovalReason(self._reddit, self.subreddit, id["id"])
