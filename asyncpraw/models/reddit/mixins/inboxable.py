"""Provide the InboxableMixin class."""

from ....const import API_PATH


class InboxableMixin:
    """Interface for RedditBase classes that originate from the inbox."""

    async def block(self):
        """Block the user who sent the item.

        .. note::

            This method pertains only to objects which were retrieved via the inbox.

        Example usage:

        .. code-block:: python

            comment = await reddit.comment("dkk4qjd")
            await comment.block()

            # or, identically:
            comment = await reddit.comment("dkk4qjd")
            await comment.author.block()

        """
        await self._reddit.post(API_PATH["block"], data={"id": self.fullname})

    async def collapse(self):
        """Mark the item as collapsed.

        .. note::

            This method pertains only to objects which were retrieved via the inbox.

        Example usage:

        .. code-block:: python

            inbox = reddit.inbox()

            # select first inbox item and collapse it
            async for message in inbox:
                await message.collapse()
                break

        .. seealso::

            :meth:`~.uncollapse`

        """
        await self._reddit.inbox.collapse([self])

    async def mark_read(self):
        """Mark a single inbox item as read.

        .. note::

            This method pertains only to objects which were retrieved via the inbox.

        Example usage:

        .. code-block:: python

            inbox = reddit.inbox.unread()

            async for message in inbox:
                # process unread messages
                ...

        .. seealso::

            :meth:`~.mark_unread`

        To mark the whole inbox as read with a single network request, use
        :meth:`asyncpraw.models.Inbox.mark_read`

        """
        await self._reddit.inbox.mark_read([self])

    async def mark_unread(self):
        """Mark the item as unread.

        .. note::

            This method pertains only to objects which were retrieved via the inbox.

        Example usage:

        .. code-block:: python

            inbox = reddit.inbox(limit=10)

            async for message in inbox:
                # process messages
                ...

        .. seealso::

            :meth:`~.mark_read`

        """
        await self._reddit.inbox.mark_unread([self])

    async def uncollapse(self):
        """Mark the item as uncollapsed.

        .. note::

            This method pertains only to objects which were retrieved via the inbox.

        Example usage:

        .. code-block:: python

            inbox = reddit.inbox()

            # select first inbox item and uncollapse it
            async for message in inbox:
                await message.uncollapse()
                break

        .. seealso::

            :meth:`~.collapse`

        """
        await self._reddit.inbox.uncollapse([self])
