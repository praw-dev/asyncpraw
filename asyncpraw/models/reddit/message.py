"""Provide the Message class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from asyncpraw.const import API_PATH

from .base import RedditBase
from .mixins import FullnameMixin, InboxableMixin, ReplyableMixin
from .redditor import Redditor
from .subreddit import Subreddit

if TYPE_CHECKING:  # pragma: no cover
    import asyncpraw.models


class Message(InboxableMixin, ReplyableMixin, FullnameMixin, RedditBase):
    """A class for private messages.

    .. include:: ../../typical_attributes.rst

    =============== ================================================================
    Attribute       Description
    =============== ================================================================
    ``author``      Provides an instance of :class:`.Redditor`.
    ``body``        The body of the message, as Markdown.
    ``body_html``   The body of the message, as HTML.
    ``created_utc`` Time the message was created, represented in `Unix Time`_.
    ``dest``        Provides an instance of :class:`.Redditor`. The recipient of the
                    message.
    ``id``          The ID of the message.
    ``name``        The full ID of the message, prefixed with ``t4_``.
    ``subject``     The subject of the message.
    ``was_comment`` Whether or not the message was a comment reply.
    =============== ================================================================

    .. _unix time: https://en.wikipedia.org/wiki/Unix_time

    """

    STR_FIELD = "id"

    @classmethod
    def parse(cls, data: dict[str, Any], reddit: asyncpraw.Reddit) -> Message | SubredditMessage:
        """Return an instance of :class:`.Message` or :class:`.SubredditMessage` from ``data``.

        :param data: The structured data.
        :param reddit: An instance of :class:`.Reddit`.

        """
        if data["author"]:
            data["author"] = Redditor(reddit, data["author"])

        if data["dest"].startswith("#"):
            data["dest"] = Subreddit(reddit, data["dest"][1:])
        else:
            data["dest"] = Redditor(reddit, data["dest"])

        if data["replies"]:
            replies = data["replies"]
            data["replies"] = reddit._objector.objectify(replies["data"]["children"])
        else:
            data["replies"] = []

        if data["subreddit"]:
            data["subreddit"] = Subreddit(reddit, data["subreddit"])
            return SubredditMessage(reddit, _data=data)

        return cls(reddit, _data=data)

    @property
    def _kind(self) -> str:
        """Return the class's kind."""
        return self._reddit.config.kinds["message"]

    @property
    def parent(self) -> asyncpraw.models.Message | None:
        """Return the parent of the message if it exists.

        .. note::

            If the message is from an inbox listing, the returned parent will be lazy
            and must be fetched manually. For example:

            .. code-block:: python

                async for message in reddit.inbox.all(limit=1):
                    parent = message.parent
                    await parent.load()
                    print(parent.body)

        """
        if not self._parent:
            if not self._fetched:
                msg = "Message must be fetched with `.load()` before accessing the parent."
                raise AttributeError(msg)
            if self.parent_id:
                self._parent = Message(self._reddit, {"id": self.parent_id.split("_")[1]})
                self._parent._fetched = False
        return self._parent

    @parent.setter
    def parent(self, value: asyncpraw.models.Message | None) -> None:
        self._parent = value

    def __init__(self, reddit: asyncpraw.Reddit, _data: dict[str, Any]) -> None:
        """Initialize a :class:`.Message` instance."""
        super().__init__(reddit, _data=_data, _fetched=True)
        self._parent = None
        for reply in _data.get("replies", []):
            if reply.parent_id == self.fullname:
                reply.parent = self

    async def _fetch(self) -> None:
        message = await self._reddit.inbox.message(self.id)
        self.__dict__.update(message.__dict__)
        await super()._fetch()

    async def delete(self) -> None:
        """Delete the message.

        .. note::

            Reddit does not return an indication of whether or not the message was
            successfully deleted.

        For example, to delete the most recent message in your inbox:

        .. code-block:: python

            async for message in reddit.inbox.all():
                await message.delete()
                break

        """
        await self._reddit.post(API_PATH["delete_message"], data={"id": self.fullname})


class SubredditMessage(Message):
    """A class for messages to a subreddit.

    .. include:: ../../typical_attributes.rst

    =============== =================================================================
    Attribute       Description
    =============== =================================================================
    ``author``      Provides an instance of :class:`.Redditor`.
    ``body``        The body of the message, as Markdown.
    ``body_html``   The body of the message, as HTML.
    ``created_utc`` Time the message was created, represented in `Unix Time`_.
    ``dest``        Provides an instance of :class:`.Redditor`. The recipient of the
                    message.
    ``id``          The ID of the message.
    ``name``        The full ID of the message, prefixed with ``t4_``.
    ``subject``     The subject of the message.
    ``subreddit``   If the message was sent from a subreddit, provides an instance of
                    :class:`.Subreddit`.
    ``was_comment`` Whether or not the message was a comment reply.
    =============== =================================================================

    .. _unix time: https://en.wikipedia.org/wiki/Unix_time

    """

    async def mute(self) -> None:
        """Mute the sender of this :class:`.SubredditMessage`.

        For example, to mute the sender of the first :class:`.SubredditMessage` in the
        authenticated users' inbox:

        .. code-block:: python

            from asyncpraw.models import SubredditMessage

            async for message in reddit.inbox.all():
                if isinstance(message, SubredditMessage):
                    await msg.mute()
                    break

        """
        await self._reddit.post(API_PATH["mute_sender"], data={"id": self.fullname})

    async def unmute(self) -> None:
        """Unmute the sender of this :class:`.SubredditMessage`.

        For example, to unmute the sender of the first :class:`.SubredditMessage` in the
        authenticated users' inbox:

        .. code-block:: python

            from asyncpraw.models import SubredditMessage

            async for message in reddit.inbox.all():
                if isinstance(message, SubredditMessage):
                    await msg.unmute()
                    break

        """
        await self._reddit.post(API_PATH["unmute_sender"], data={"id": self.fullname})
