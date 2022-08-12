"""Provide Collections functionality."""
from typing import TYPE_CHECKING, Any, Dict, Generator, List, Optional, Union

from ...const import API_PATH
from ...exceptions import ClientException
from ...util import _deprecate_args
from ...util.cache import cachedproperty
from ..base import AsyncPRAWBase
from ..util import deprecate_lazy
from .base import RedditBase
from .redditor import Redditor
from .submission import Submission
from .subreddit import Subreddit

if TYPE_CHECKING:  # pragma: no cover
    import asyncpraw


class CollectionModeration(AsyncPRAWBase):
    """Class to support moderation actions on a :class:`.Collection`.

    Obtain an instance via:

    .. code-block:: python

        subreddit = await reddit.subreddit("test")
        collection = await subreddit.collections("some_uuid")
        collection.mod

    """

    def _post_fullname(self, post):
        """Get a post's fullname.

        :param post: A fullname, a :class:`.Submission`, a permalink, or an ID.

        :returns: The fullname of the post.

        """
        if isinstance(post, Submission):
            return post.fullname
        elif not isinstance(post, str):
            raise TypeError(f"Cannot get fullname from object of type {type(post)}.")
        if post.startswith(f"{self._reddit.config.kinds['submission']}_"):
            return post
        try:
            return Submission(self._reddit, url=post).fullname
        except ClientException:
            return Submission(self._reddit, id=post).fullname

    def __init__(self, reddit: "asyncpraw.Reddit", collection_id: str):
        """Initialize a :class:`.CollectionModeration` instance.

        :param collection_id: The ID of a :class:`.Collection`.

        """
        super().__init__(reddit, _data=None)
        self.collection_id = collection_id

    async def add_post(self, submission: "asyncpraw.models.Submission"):
        """Add a post to the collection.

        :param submission: The post to add, a :class:`.Submission`, its permalink as a
            ``str``, its fullname as a ``str``, or its ID as a ``str``.

        Example usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            collection = await subreddit.collections("some_uuid")
            await collection.mod.add_post("bgibu9")

        .. seealso::

            :meth:`.remove_post`

        """
        link_fullname = self._post_fullname(submission)

        await self._reddit.post(
            API_PATH["collection_add_post"],
            data={"collection_id": self.collection_id, "link_fullname": link_fullname},
        )

    async def delete(self):
        """Delete this collection.

        Example usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            collection = await subreddit.collections("some_uuid")
            await collection.mod.delete()

        .. seealso::

            :meth:`~.SubredditCollectionsModeration.create`

        """
        await self._reddit.post(
            API_PATH["collection_delete"], data={"collection_id": self.collection_id}
        )

    async def remove_post(self, submission: "asyncpraw.models.Submission"):
        """Remove a post from the collection.

        :param submission: The post to remove, a :class:`.Submission`, its permalink as
            a ``str``, its fullname as a ``str``, or its ID as a ``str``.

        Example usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            collection = await subreddit.collections("some_uuid")
            await collection.mod.remove_post("bgibu9")

        .. seealso::

            :meth:`.add_post`

        """
        link_fullname = self._post_fullname(submission)

        await self._reddit.post(
            API_PATH["collection_remove_post"],
            data={"collection_id": self.collection_id, "link_fullname": link_fullname},
        )

    async def reorder(self, links: List[Union[str, "asyncpraw.models.Submission"]]):
        r"""Reorder posts in the collection.

        :param links: A list of :class:`.Submission`\ s or a ``str`` that is either a
            fullname or an ID.

        Example usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            collection = await subreddit.collections("some_uuid")
            current_order = collection.link_ids
            new_order = reversed(current_order)
            await collection.mod.reorder(new_order)

        """
        link_ids = ",".join([self._post_fullname(post) for post in links])
        await self._reddit.post(
            API_PATH["collection_reorder"],
            data={"collection_id": self.collection_id, "link_ids": link_ids},
        )

    async def update_description(self, description: str):
        """Update the collection's description.

        :param description: The new description.

        Example usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            collection = await subreddit.collections("some_uuid")
            await collection.mod.update_description("Please enjoy these links")

        .. seealso::

            :meth:`.update_title`

        """
        await self._reddit.post(
            API_PATH["collection_desc"],
            data={"collection_id": self.collection_id, "description": description},
        )

    async def update_display_layout(self, display_layout: str):
        """Update the collection's display layout.

        :param display_layout: Either ``"TIMELINE"`` for events or discussions or
            ``"GALLERY"`` for images or memes. Passing ``None`` will clear the set
            layout and ``collection.display_layout`` will be ``None``, however, the
            collection will appear on Reddit as if ``display_layout`` is set to
            ``"TIMELINE"``.

        Example usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            collection = await subreddit.collections("some_uuid")
            await collection.mod.update_display_layout("GALLERY")

        """
        await self._reddit.post(
            API_PATH["collection_layout"],
            data={
                "collection_id": self.collection_id,
                "display_layout": display_layout,
            },
        )

    async def update_title(self, title: str):
        """Update the collection's title.

        :param title: The new title.

        Example usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            collection = await subreddit.collections("some_uuid")
            await collection.mod.update_title("Titley McTitleface")

        .. seealso::

            :meth:`.update_description`

        """
        await self._reddit.post(
            API_PATH["collection_title"],
            data={"collection_id": self.collection_id, "title": title},
        )


class Collection(RedditBase):
    """Class to represent a :class:`.Collection`.

    Obtain an instance via:

    .. code-block:: python

        subreddit = await reddit.subreddit("test")
        collection = await subreddit.collections("some_uuid")

    or

    .. code-block:: python

        subreddit = await reddit.subreddit("test")
        collection = await subreddit.collections(
            permalink="https://reddit.com/r/test/collection/some_uuid"
        )

    .. include:: ../../typical_attributes.rst

    =================== =============================================================
    Attribute           Description
    =================== =============================================================
    ``author``          The :class:`.Redditor` who created the collection.
    ``collection_id``   The UUID of the collection.
    ``created_at_utc``  Time the collection was created, represented in `Unix Time`_.
    ``description``     The collection description.
    ``display_layout``  The collection display layout.
    ``last_update_utc`` Time the collection was last updated, represented in `Unix
                        Time`_.
    ``link_ids``        A list of :class:`.Submission` fullnames.
    ``permalink``       The collection's permalink (to view on the web).
    ``sorted_links``    An iterable listing of the posts in this collection.
    ``title``           The title of the collection.
    =================== =============================================================

    .. _unix time: https://en.wikipedia.org/wiki/Unix_time

    """

    STR_FIELD = "collection_id"

    @cachedproperty
    def mod(self) -> CollectionModeration:
        """Get an instance of :class:`.CollectionModeration`.

        Provides access to various methods, including
        :meth:`~reddit.collections.CollectionModeration.add_post`,
        :meth:`~reddit.collections.CollectionModeration.delete`,
        :meth:`~reddit.collections.CollectionModeration.reorder`, and
        :meth:`~reddit.collections.CollectionModeration.update_title`.

        Example usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            collection = await subreddit.collections("some_uuid")
            await collection.mod.update_title("My new title!")

        """
        return CollectionModeration(self._reddit, self.collection_id)

    async def subreddit(self) -> "asyncpraw.models.Subreddit":
        """Get the subreddit that this collection belongs to.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            collection = await subreddit.collections("some_uuid")
            print(await collection.subreddit())

        """
        async for subreddit in self._reddit.info(fullnames=[self.subreddit_id]):
            return subreddit

    def __init__(
        self,
        reddit: "asyncpraw.Reddit",
        _data: Dict[str, Any] = None,
        collection_id: Optional[str] = None,
        permalink: Optional[str] = None,
    ):
        """Initialize a :class:`.Collection` instance.

        :param reddit: An instance of :class:`.Reddit`.
        :param _data: Any data associated with the :class:`.Collection`.
        :param collection_id: The ID of the :class:`.Collection`.
        :param permalink: The permalink of the :class:`.Collection`.

        """
        if (_data, collection_id, permalink).count(None) != 2:
            raise TypeError(
                "Exactly one of '_data', 'collection_id', or 'permalink' must be"
                " provided."
            )

        if permalink:
            collection_id = self._url_parts(permalink)[4]

        if collection_id:
            self.collection_id = collection_id  # set from _data otherwise

        super().__init__(reddit, _data)

        self._info_params = {
            "collection_id": self.collection_id,
            "include_links": True,
        }

    def __iter__(self) -> Generator[Any, None, None]:
        """Provide a way to iterate over the posts in this :class:`.Collection`.

        Example usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            collection = await subreddit.collections("some_uuid")
            for submission in collection:
                print(submission.title, submission.permalink)

        """
        for item in self.sorted_links:
            yield item

    def __len__(self) -> int:
        """Get the number of posts in this :class:`.Collection`.

        Example usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            collection = await subreddit.collections("some_uuid")
            print(len(collection))

        """
        return len(self.link_ids)

    def __setattr__(self, attribute: str, value: Any):
        """Objectify author, subreddit, and sorted_links attributes."""
        if attribute == "author_name":
            self.author = Redditor(self._reddit, name=attribute)
        elif attribute == "sorted_links":
            value = self._reddit._objector.objectify(value)
        super().__setattr__(attribute, value)

    def _fetch_info(self):
        return "collection", {}, self._info_params

    async def _fetch_data(self):
        name, fields, params = self._fetch_info()
        path = API_PATH[name].format(**fields)
        return await self._reddit.request(method="GET", params=params, path=path)

    async def _fetch(self):
        data = await self._fetch_data()
        try:
            self._reddit._objector.check_error(data)
        except ClientException:
            # A well-formed but invalid Collections ID during fetch time
            # causes Reddit to return something that looks like an error
            # but with no content.
            raise ClientException(
                f"Error during fetch. Check collection ID {self.collection_id!r} is"
                " correct."
            )

        other = type(self)(self._reddit, _data=data)
        self.__dict__.update(other.__dict__)
        self._fetched = True

    async def follow(self):
        """Follow this :class:`.Collection`.

        Example usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            collection = await subreddit.collections("some_uuid")
            await collection.follow()

        .. seealso::

            :meth:`.unfollow`

        """
        await self._reddit.post(
            API_PATH["collection_follow"],
            data={"collection_id": self.collection_id, "follow": True},
        )

    async def unfollow(self):
        """Unfollow this :class:`.Collection`.

        Example usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            collection = await subreddit.collections("some_uuid")
            await collection.unfollow()

        .. seealso::

            :meth:`.follow`

        """
        await self._reddit.post(
            API_PATH["collection_follow"],
            data={"collection_id": self.collection_id, "follow": False},
        )


class SubredditCollectionsModeration(AsyncPRAWBase):
    r"""Class to represent moderator actions on a :class:`.Subreddit`'s :class:`.Collection`\ s.

    Obtain an instance via:

    .. code-block:: python

        subreddit = await reddit.subreddit("test")
        subreddit.collections.mod

    """

    def __init__(
        self,
        reddit: "asyncpraw.Reddit",
        subreddit: "asyncpraw.models.Subreddit",
        _data: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a :class:`.SubredditCollectionsModeration` instance."""
        super().__init__(reddit, _data)
        self.subreddit = subreddit

    @_deprecate_args("title", "description", "display_layout")
    async def create(
        self, *, description: str, display_layout: Optional[str] = None, title: str
    ):
        """Create a new :class:`.Collection`.

        The authenticated account must have appropriate moderator permissions in the
        subreddit this collection belongs to.

        :param description: The description, up to 500 characters.
        :param display_layout: Either ``"TIMELINE"`` for events or discussions or
            ``"GALLERY"`` for images or memes. Passing ``""`` or ``None`` will make the
            collection appear on Reddit as if this is set to ``"TIMELINE"`` (default:
            ``None``).
        :param title: The title of the collection, up to 300 characters.

        :returns: The newly created :class:`.Collection`.

        Example usage:

        .. code-block:: python

            sub = await reddit.subreddit("test")
            new_collection = await sub.collections.mod.create(title="Title", description="desc")
            await new_collection.mod.add_post("bgibu9")

        To specify the display layout as ``"GALLERY"`` when creating the collection:

        .. code-block:: python

            my_sub = await reddit.subreddit("test")
            new_collection = await my_sub.collections.mod.create(
                title="Title", description="desc", display_layout="GALLERY"
            )
            await new_collection.mod.add_post("bgibu9")

        .. seealso::

            :meth:`~.CollectionModeration.delete`

        """
        if not self.subreddit._fetched:
            await self.subreddit._fetch()
        data = {
            "sr_fullname": self.subreddit.fullname,
            "title": title,
            "description": description,
        }
        if display_layout:
            data["display_layout"] = display_layout
        return await self._reddit.post(
            API_PATH["collection_create"],
            data=data,
        )


class SubredditCollections(AsyncPRAWBase):
    r"""Class to represent a :class:`.Subreddit`'s :class:`.Collection`\ s.

    Obtain an instance via:

    .. code-block:: python

        subreddit = await reddit.subreddit("test")
        subreddit.collections

    """

    @cachedproperty
    def mod(self) -> SubredditCollectionsModeration:
        """Get an instance of :class:`.SubredditCollectionsModeration`.

        Provides :meth:`~SubredditCollectionsModeration.create`:

        .. code-block:: python

            my_sub = await reddit.subreddit("test", fetch=True)
            new_collection = await my_sub.collections.mod.create(title="Title", description="desc")

        """
        return SubredditCollectionsModeration(self._reddit, self.subreddit)

    @deprecate_lazy
    async def __call__(
        self,
        collection_id: Optional[str] = None,
        permalink: Optional[str] = None,
        fetch: bool = True,
        **kwargs,
    ):
        """Return the :class:`.Collection` with the specified ID.

        :param collection_id: The ID of a :class:`.Collection` (default: ``None``).
        :param permalink: The permalink of a collection (default: ``None``).
        :param fetch: Determines if Async PRAW will fetch the object (default:
            ``True``).

        :returns: The specified :class:`.Collection`.

        Exactly one of ``collection_id`` or ``permalink`` is required.

        Example usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")

            uuid = "847e4548-a3b5-4ad7-afb4-edbfc2ed0a6b"
            collection = await subreddit.collections(uuid)
            print(collection.title)
            print(collection.description)

            permalink = "https://www.reddit.com/r/test/collection/" + uuid
            collection = await subreddit.collections(permalink=permalink)
            print(collection.title)
            print(collection.description)

        If you don't need the object fetched right away (e.g., to utilize a class
        method) you can do:

        .. code-block:: python

            subreddit = await reddit.subreddit("test", fetch=True)
            collection = await subreddit.collections(uuid, fetch=False)
            await collection.mod.add("submission_id")

        """
        if (collection_id is None) == (permalink is None):
            raise TypeError(
                "Exactly one of 'collection_id' or 'permalink' must be provided."
            )
        collection = Collection(
            self._reddit, collection_id=collection_id, permalink=permalink
        )
        if fetch:
            await collection._fetch()
        return collection

    def __init__(
        self,
        reddit: "asyncpraw.Reddit",
        subreddit: "asyncpraw.models.Subreddit",
        _data: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a :class:`.SubredditCollections` instance."""
        super().__init__(reddit, _data)
        self.subreddit = subreddit

    async def __aiter__(self):
        r"""Iterate over the :class:`.Subreddit`'s :class:`.Collection`\ s.

        Example usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            async for collection in subreddit.collections:
                print(collection.permalink)

        """
        if not self.subreddit._fetched:
            await self.subreddit._fetch()
        request = await self._reddit.get(
            API_PATH["collection_subreddit"],
            params={"sr_fullname": self.subreddit.fullname},
        )
        for collection in request:
            yield collection


Subreddit._subreddit_collections_class = SubredditCollections
