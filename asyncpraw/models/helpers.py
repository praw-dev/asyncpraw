"""Provide the helper classes."""
from json import dumps
from typing import TYPE_CHECKING, AsyncGenerator, List, Optional, Union

from ..const import API_PATH
from .base import AsyncPRAWBase
from .reddit.live import LiveThread
from .reddit.multi import Multireddit, Subreddit

if TYPE_CHECKING:  # pragma: no cover
    from ... import asyncpraw


class LiveHelper(AsyncPRAWBase):
    """Provide a set of functions to interact with LiveThreads."""

    async def __call__(
        self, id: str, fetch: bool = False
    ) -> "asyncpraw.models.LiveThread":  # pylint: disable=invalid-name,redefined-builtin
        """Return a new instance of :class:`~.LiveThread`.

        This method is intended to be used as:

        .. code-block:: python

            livethread = await reddit.live("ukaeu1ik4sw5")

        If you need the object fetched right away (e.g., to access attributes) you can
        do:

        .. code-block:: python

            livethread = await reddit.live("ukaeu1ik4sw5", fetch=True)
            await livethread.close()

        :param id: A live thread ID, e.g., ``ukaeu1ik4sw5``.
        :param fetch: Determines if the object is lazily loaded (default: False).

        """
        live_thread = LiveThread(self._reddit, id=id)
        if fetch:
            await live_thread._fetch()
        return live_thread

    def info(
        self, ids: List[str]
    ) -> AsyncGenerator["asyncpraw.models.LiveThread", None]:
        """Fetch information about each live thread in ``ids``.

        :param ids: A list of IDs for a live thread.

        :returns: A generator that yields :class:`.LiveThread` instances.

        :raises: ``asyncprawcore.ServerError`` if invalid live threads are requested.

        Requests will be issued in batches for each 100 IDs.

        .. note::

            This method doesn't support IDs for live updates.

        .. warning::

            Unlike :meth:`.Reddit.info`, the output of this method may not reflect the
            order of input.

        Usage:

        .. code-block:: python

            ids = ["3rgnbke2rai6hen7ciytwcxadi", "sw7bubeycai6hey4ciytwamw3a", "t8jnufucss07"]
            async for thread in reddit.live.info(ids):
                print(thread.title)

        """
        if not isinstance(ids, list):
            raise TypeError("ids must be a list")

        async def generator():
            for position in range(0, len(ids), 100):
                ids_chunk = ids[position : position + 100]
                url = API_PATH["live_info"].format(ids=",".join(ids_chunk))
                params = {"limit": 100}  # 25 is used if not specified
                for result in await self._reddit.get(url, params=params):
                    yield result

        return generator()

    async def create(
        self,
        title: str,
        description: Optional[str] = None,
        nsfw: bool = False,
        resources: str = None,
    ) -> "asyncpraw.models.LiveThread":
        """Create a new LiveThread.

        :param title: The title of the new LiveThread.
        :param description: (Optional) The new LiveThread's description.
        :param nsfw: (boolean) Indicate whether this thread is not safe for work
            (default: False).
        :param resources: (Optional) Markdown formatted information that is useful for
            the LiveThread.

        :returns: The new LiveThread object.

        """
        return await self._reddit.post(
            API_PATH["livecreate"],
            data={
                "description": description,
                "nsfw": nsfw,
                "resources": resources,
                "title": title,
            },
        )

    async def now(self) -> Optional["asyncpraw.models.LiveThread"]:
        """Get the currently featured live thread.

        :returns: The :class:`.LiveThread` object, or ``None`` if there is no currently
            featured live thread.

        Usage:

        .. code-block:: python

            thread = await reddit.live.now()  # LiveThread object or None

        """
        return await self._reddit.get(API_PATH["live_now"])


class MultiredditHelper(AsyncPRAWBase):
    """Provide a set of functions to interact with Multireddits."""

    async def __call__(
        self,
        redditor: Union[str, "asyncpraw.models.Redditor"],
        name: str,
        fetch: bool = False,
    ) -> "asyncpraw.models.Multireddit":
        """Return an instance of :class:`~.Multireddit`.

        If you need the object fetched right away (e.g., to access an attribute) you can
        do:

        .. code-block:: python

            multireddit = await reddit.multireddit("redditor", "multi", fetch=True)
            async for comment in multireddit.comments(limit=25):
                print(comment.author)

        :param redditor: A redditor name (e.g., ``"spez"``) or :class:`~.Redditor`
            instance who owns the multireddit.
        :param name: The name of the multireddit.
        :param fetch: Determines if the object is lazily loaded (default: False).

        """
        path = f"/user/{redditor}/m/{name}"
        multireddit = Multireddit(self._reddit, _data={"name": name, "path": path})
        if fetch:
            await multireddit._fetch()
        return multireddit

    async def create(
        self,
        display_name: str,
        subreddits: Union[str, "asyncpraw.models.Subreddit"],
        description_md: Optional[str] = None,
        icon_name: Optional[str] = None,
        key_color: Optional[str] = None,
        visibility: str = "private",
        weighting_scheme: str = "classic",
    ) -> "asyncpraw.models.Multireddit":
        """Create a new multireddit.

        :param display_name: The display name for the new multireddit.
        :param subreddits: Subreddits to add to the new multireddit.
        :param description_md: (Optional) Description for the new multireddit, formatted
            in markdown.
        :param icon_name: (Optional) Can be one of: ``art and design``, ``ask``,
            ``books``, ``business``, ``cars``, ``comics``, ``cute animals``, ``diy``,
            ``entertainment``, ``food and drink``, ``funny``, ``games``, ``grooming``,
            ``health``, ``life advice``, ``military``, ``models pinup``, ``music``,
            ``news``, ``philosophy``, ``pictures and gifs``, ``science``, ``shopping``,
            ``sports``, ``style``, ``tech``, ``travel``, ``unusual stories``, ``video``,
            or ``None``.
        :param key_color: (Optional) RGB hex color code of the form ``"#FFFFFF"``.
        :param visibility: (Optional) Can be one of: ``hidden``, ``private``, ``public``
            (default: private).
        :param weighting_scheme: (Optional) Can be one of: ``classic``, ``fresh``
            (default: classic).

        :returns: The new Multireddit object.

        """
        model = {
            "description_md": description_md,
            "display_name": display_name,
            "icon_name": icon_name,
            "key_color": key_color,
            "subreddits": [{"name": str(sub)} for sub in subreddits],
            "visibility": visibility,
            "weighting_scheme": weighting_scheme,
        }
        return await self._reddit.post(
            API_PATH["multireddit_base"], data={"model": dumps(model)}
        )


class SubredditHelper(AsyncPRAWBase):
    """Provide a set of functions to interact with Subreddits."""

    async def __call__(
        self, display_name: str, fetch: bool = False
    ) -> "asyncpraw.models.Subreddit":
        """Return an instance of :class:`~.Subreddit`.

        If you need the object fetched right away (e.g., to access an attribute) you can
        do:

        .. code-block:: python

            multireddit = await reddit.subreddit("redditor", fetch=True)
            async for comment in multireddit.comments(limit=25):
                print(comment.author)

        :param display_name: The name of the subreddit.
        :param fetch: Determines if the object is lazily loaded (default: False).

        """
        lower_name = display_name.lower()

        if lower_name == "random":
            return await self._reddit.random_subreddit()
        if lower_name == "randnsfw":
            return await self._reddit.random_subreddit(nsfw=True)
        subreddit = Subreddit(self._reddit, display_name=display_name)
        if fetch:
            await subreddit._fetch()
        return subreddit

    async def create(
        self,
        name: str,
        title: Optional[str] = None,
        link_type: str = "any",
        subreddit_type: str = "public",
        wikimode: str = "disabled",
        **other_settings: Optional[str],
    ) -> "asyncpraw.models.Subreddit":
        """Create a new subreddit.

        :param name: The name for the new subreddit.
        :param title: The title of the subreddit. When ``None`` or ``""`` use the value
            of ``name``.
        :param link_type: The types of submissions users can make. One of ``any``,
            ``link``, ``self`` (default: any).
        :param subreddit_type: One of ``archived``, ``employees_only``, ``gold_only``,
            ``gold_restricted``, ``private``, ``public``, ``restricted`` (default:
            public).
        :param wikimode: One of ``anyone``, ``disabled``, ``modonly``.

        Any keyword parameters not provided, or set explicitly to None, will take on a
        default value assigned by the Reddit server.

        .. seealso::

            :meth:`~.SubredditModeration.update` for documentation of other available
            settings.

        """
        await Subreddit._create_or_update(
            _reddit=self._reddit,
            name=name,
            link_type=link_type,
            subreddit_type=subreddit_type,
            title=title or name,
            wikimode=wikimode,
            **other_settings,
        )
        subreddit = await self(name, fetch=True)
        return subreddit
