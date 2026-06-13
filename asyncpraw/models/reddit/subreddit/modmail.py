"""Provide the Modmail class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from asyncpraw.const import API_PATH
from asyncpraw.models.listing.generator import ListingGenerator
from asyncpraw.models.reddit.base import RedditBase
from asyncpraw.models.reddit.modmail import ModmailConversation

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, AsyncIterator

    import asyncpraw.models


class Modmail:
    """Provides modmail functions for a :class:`.Subreddit`.

    For example, to send a new modmail from r/test to u/spez with the subject ``"test"``
    along with a message body of ``"hello"``:

    .. code-block:: python

        subreddit = await reddit.subreddit("test")
        await subreddit.modmail.create(subject="test", body="hello", recipient="spez")

    """

    async def __call__(
        self, id: str | None = None, *, mark_read: bool = False, fetch: bool = True
    ) -> ModmailConversation:
        """Return an individual conversation.

        :param id: A reddit base36 conversation ID, e.g., ``"2gmz"``.
        :param mark_read: If ``True``, conversation is marked as read (default:
            ``False``).
        :param fetch: Determines if Async PRAW will fetch the object (default:
            ``False``).

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            await subreddit.modmail("2gmz", mark_read=True)

        If you don't need the object fetched right away (e.g., to utilize a class
        method) you can do:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            message = await subreddit.modmail("2gmz", fetch=False)
            await message.archive()

        To print all messages from a conversation as Markdown source:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            conversation = await subreddit.modmail("2gmz", mark_read=True)
            for message in conversation.messages:
                print(message.body_markdown)

        ``ModmailConversation.user`` is a special instance of :class:`.Redditor` with
        extra attributes describing the non-moderator user's recent posts, comments, and
        modmail messages within the subreddit, as well as information on active bans and
        mutes. This attribute does not exist on internal moderator discussions.

        For example, to print the user's ban status:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            conversation = await subreddit.modmail("2gmz", mark_read=True)
            print(conversation.user.ban_status)

        To print a list of recent submissions by the user:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            conversation = await subreddit.modmail("2gmz", mark_read=True)
            print(conversation.user.recent_posts)

        """
        modmail_conversation = ModmailConversation(self.subreddit._reddit, id=id, mark_read=mark_read)
        if fetch:
            await modmail_conversation._fetch()
        return modmail_conversation

    def __init__(self, subreddit: asyncpraw.models.Subreddit) -> None:
        """Initialize a :class:`.Modmail` instance."""
        self.subreddit = subreddit

    def _build_subreddit_list(self, other_subreddits: list[asyncpraw.models.Subreddit | str] | None) -> str:
        """Return a comma-separated list of subreddit display names."""
        subreddits = [self.subreddit] + (other_subreddits or [])
        return ",".join(str(subreddit) for subreddit in subreddits)

    async def bulk_read(
        self,
        *,
        other_subreddits: list[asyncpraw.models.Subreddit | str] | None = None,
        state: str | None = None,
    ) -> list[ModmailConversation]:
        """Mark conversations for subreddit(s) as read.

        .. note::

            Due to server-side restrictions, r/all is not a valid subreddit for this
            method. Instead, use :meth:`~.Modmail.subreddits` to get a list of
            subreddits using the new modmail.

        :param other_subreddits: A list of :class:`.Subreddit` instances for which to
            mark conversations (default: ``None``).
        :param state: Can be one of: ``"all"``, ``"archived"``, or ``"highlighted"``,
            ``"inprogress"``, ``"join_requests"``, ``"mod"``, ``"new"``,
            ``"notifications"``, or ``"appeals"`` (default: ``"all"``). ``"all"`` does
            not include internal, archived, or appeals conversations.

        :returns: A list of lazy :class:`.ModmailConversation` instances that were
            marked read.

        For example, to mark all notifications for a subreddit as read:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            await subreddit.modmail.bulk_read(state="notifications")

        """
        params: dict[str, str | int] = {"entity": self._build_subreddit_list(other_subreddits)}
        if state:
            params["state"] = state
        response = await self.subreddit._reddit.post(API_PATH["modmail_bulk_read"], params=params)
        return [await self(conversation_id, fetch=False) for conversation_id in response["conversation_ids"]]

    def conversations(
        self,
        *,
        other_subreddits: list[asyncpraw.models.Subreddit | str] | None = None,
        sort: str | None = None,
        state: str | None = None,
        **generator_kwargs: Any,
    ) -> AsyncIterator[ModmailConversation]:
        """Generate :class:`.ModmailConversation` objects for subreddit(s).

        :param other_subreddits: A list of :class:`.Subreddit` instances for which to
            fetch conversations (default: ``None``).
        :param sort: Can be one of: ``"mod"``, ``"recent"``, ``"unread"``, or ``"user"``
            (default: ``"recent"``).
        :param state: Can be one of: ``"all"``, ``"archived"``, ``"highlighted"``,
            ``"inprogress"``, ``"join_requests"``, ``"mod"``, ``"new"``,
            ``"notifications"``, or ``"appeals"`` (default: ``"all"``). ``"all"`` does
            not include internal, archived, or appeals conversations.

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        For example:

        .. code-block:: python

            sub = await reddit.subreddit("all")
            async for conversation in sub.modmail.conversations(state="mod"):
                # do stuff with conversations
                ...

        """
        params = {}
        if self.subreddit != "all":
            params["entity"] = self._build_subreddit_list(other_subreddits)
        RedditBase._safely_add_arguments(arguments=generator_kwargs, key="params", sort=sort, state=state, **params)
        return ListingGenerator(
            self.subreddit._reddit,
            API_PATH["modmail_conversations"],
            **generator_kwargs,
        )

    async def create(
        self,
        *,
        author_hidden: bool = False,
        body: str,
        recipient: str | asyncpraw.models.Redditor,
        subject: str,
    ) -> ModmailConversation:
        """Create a new :class:`.ModmailConversation`.

        :param author_hidden: When ``True``, author is hidden from non-moderators
            (default: ``False``).
        :param body: The message body. Cannot be empty.
        :param recipient: The recipient; a username or an instance of
            :class:`.Redditor`.
        :param subject: The message subject. Cannot be empty.

        :returns: A :class:`.ModmailConversation` object for the newly created
            conversation.

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            redditor = await reddit.redditor("bboe")
            await subreddit.modmail.create(subject="Subject", body="Body", recipient=redditor)

        """
        data = {
            "body": body,
            "isAuthorHidden": author_hidden,
            "srName": self.subreddit,
            "subject": subject,
            "to": recipient,
        }
        return await self.subreddit._reddit.post(API_PATH["modmail_conversations"], data=data)

    async def subreddits(
        self,
    ) -> AsyncGenerator[asyncpraw.models.Subreddit]:
        """Yield subreddits using the new modmail that the user moderates.

        For example:

        .. code-block:: python

            sub = await reddit.subreddit("all")
            async for subreddit in sub.modmail.subreddits():
                # do stuff with subreddit
                ...

        """
        response = await self.subreddit._reddit.get(API_PATH["modmail_subreddits"])
        for value in response["subreddits"].values():
            subreddit = type(self.subreddit)(self.subreddit._reddit, value["display_name"])
            subreddit.last_updated = value["lastUpdated"]
            yield subreddit

    async def unread_count(self) -> dict[str, int]:
        """Return unread conversation count by conversation state.

        At time of writing, possible states are: ``"archived"``, ``"highlighted"``,
        ``"inprogress"``, ``"join_requests"``, ``"mod"``, ``"new"``,
        ``"notifications"``, or ``"appeals"``.

        :returns: A dict mapping conversation states to unread counts.

        For example, to print the count of unread moderator discussions:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            unread_counts = await subreddit.modmail.unread_count()
            print(unread_counts["mod"])

        """
        return await self.subreddit._reddit.get(API_PATH["modmail_unread_count"])
