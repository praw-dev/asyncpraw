"""Provide the helper classes."""
from json import dumps
from typing import TYPE_CHECKING, AsyncGenerator, List, Optional, Union

from ..const import API_PATH
from .base import AsyncPRAWBase
from .reddit.draft import Draft
from .reddit.live import LiveThread
from .reddit.multi import Multireddit, Subreddit

if TYPE_CHECKING:  # pragma: no cover
    import asyncpraw


class DraftHelper(AsyncPRAWBase):
    r"""Provide a set of functions to interact with :class:`.Draft` instances.

    .. note::

        The methods provided by this class will only work on the currently authenticated
        user's :class:`.Draft`\ s.

    """

    async def __call__(
        self, *, draft_id: Optional[str] = None, fetch: bool = True
    ) -> Union[List["asyncpraw.models.Draft"], "asyncpraw.models.Draft"]:
        """Return a list of :class:`.Draft` instances.

        :param draft_id: When provided, this returns a :class:`.Draft` instance
            (default: ``None``).
        :param fetch: Determines if Async PRAW will fetch the object (default:
            ``True``).

        :returns: A :class:`.Draft` instance if ``draft_id`` is provided. Otherwise, a
            list of :class:`.Draft` objects.

        This method can be used to fetch a specific draft by ID, like so:

        .. code-block:: python

            draft_id = "124862bc-e1e9-11eb-aa4f-e68667a77cbb"
            draft = await reddit.drafts(draft_id=draft_id)
            print(draft)

        """
        if draft_id is not None:
            draft = Draft(self._reddit, id=draft_id)
            if fetch:
                await draft.load()
            return draft
        return await self._draft_list()

    async def __aiter__(self):
        r"""Iterate through all the :class:`.Draft`\ s.

        :returns: An asynchronous iterator containing all the currently authenticated
            user's :class:`.Draft`\ s.

        .. code-block:: python

            async for draft in reddit.drafts:
                print(draft)

        """
        drafts = await self._draft_list()
        for draft in drafts:
            yield draft

    async def _draft_list(self) -> List["asyncpraw.models.Draft"]:
        """Get a list of :class:`.Draft` instances.

        :returns: A list of :class:`.Draft` instances.

        """
        return await self._reddit.get(API_PATH["drafts"], params={"md_body": True})

    async def create(
        self,
        *,
        flair_id: Optional[str] = None,
        flair_text: Optional[str] = None,
        is_public_link: bool = False,
        nsfw: bool = False,
        original_content: bool = False,
        selftext: Optional[str] = None,
        send_replies: bool = True,
        spoiler: bool = False,
        subreddit: Optional[
            Union[str, "asyncpraw.models.Subreddit", "asyncpraw.models.UserSubreddit"]
        ] = None,
        title: Optional[str] = None,
        url: Optional[str] = None,
        **draft_kwargs,
    ) -> "asyncpraw.models.Draft":
        """Create a new :class:`.Draft`.

        :param flair_id: The flair template to select (default: ``None``).
        :param flair_text: If the template's ``flair_text_editable`` value is ``True``,
            this value will set a custom text (default: ``None``). ``flair_id`` is
            required when ``flair_text`` is provided.
        :param is_public_link: Whether to enable public viewing of the draft before it
            is submitted (default: ``False``).
        :param nsfw: Whether the draft should be marked NSFW (default: ``False``).
        :param original_content: Whether the submission should be marked as original
            content (default: ``False``).
        :param selftext: The Markdown formatted content for a text submission draft. Use
            ``None`` to make a title-only submission draft (default: ``None``).
            ``selftext`` can not be provided if ``url`` is provided.
        :param send_replies: When ``True``, messages will be sent to the submission
            author when comments are made to the submission (default: ``True``).
        :param spoiler: Whether the submission should be marked as a spoiler (default:
            ``False``).
        :param subreddit: The subreddit to create the draft for. This accepts a
            subreddit display name, :class:`.Subreddit` object, or
            :class:`.UserSubreddit` object. If ``None``, the :class:`.UserSubreddit` of
            currently authenticated user will be used (default: ``None``).
        :param title: The title of the draft (default: ``None``).
        :param url: The URL for a ``link`` submission draft (default: ``None``). ``url``
            can not be provided if ``selftext`` is provided.

        Additional keyword arguments can be provided to handle new parameters as Reddit
        introduces them.

        :returns: The new :class:`.Draft` object.

        """
        if selftext and url:
            raise TypeError("Exactly one of `selftext` or `url` must be provided.")
        if isinstance(subreddit, str):
            subreddit = await self._reddit.subreddit(subreddit)

        data = await Draft._prepare_data(
            flair_id=flair_id,
            flair_text=flair_text,
            is_public_link=is_public_link,
            nsfw=nsfw,
            original_content=original_content,
            selftext=selftext,
            send_replies=send_replies,
            spoiler=spoiler,
            subreddit=subreddit,
            title=title,
            url=url,
            **draft_kwargs,
        )
        return await self._reddit.post(API_PATH["draft"], data=data)


class LiveHelper(AsyncPRAWBase):
    r"""Provide a set of functions to interact with :class:`.LiveThread`\ s."""

    async def __call__(
        self, id: str, fetch: bool = False
    ) -> "asyncpraw.models.LiveThread":  # pylint: disable=invalid-name,redefined-builtin
        """Return a new instance of :class:`.LiveThread`.

        This method is intended to be used as:

        .. code-block:: python

            livethread = await reddit.live("ukaeu1ik4sw5")

        If you need the object fetched right away (e.g., to access attributes) you can
        do:

        .. code-block:: python

            livethread = await reddit.live("ukaeu1ik4sw5", fetch=True)
            await livethread.close()

        :param id: A live thread ID, e.g., ``ukaeu1ik4sw5``.
        :param fetch: Determines if Async PRAW will fetch the object (default: False).

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
        r"""Create a new :class:`.LiveThread`.

        :param title: The title of the new :class:`.LiveThread`.
        :param description: The new :class:`.LiveThread`'s description.
        :param nsfw: Indicate whether this thread is not safe for work (default:
            ``False``).
        :param resources: Markdown formatted information that is useful for the
            :class:`.LiveThread`.

        :returns: The new :class`.LiveThread` object.

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
    """Provide a set of functions to interact with multireddits."""

    async def __call__(
        self,
        redditor: Union[str, "asyncpraw.models.Redditor"],
        name: str,
        fetch: bool = False,
    ) -> "asyncpraw.models.Multireddit":
        """Return an instance of :class:`.Multireddit`.

        If you need the object fetched right away (e.g., to access an attribute) you can
        do:

        .. code-block:: python

            multireddit = await reddit.multireddit("redditor", "multi", fetch=True)
            async for comment in multireddit.comments(limit=25):
                print(comment.author)

        :param redditor: A redditor name or :class:`.Redditor` instance who owns the
            multireddit.
        :param name: The name of the multireddit.
        :param fetch: Determines if Async PRAW will fetch the object (default: False).

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
        """Create a new :class:`.Multireddit`.

        :param display_name: The display name for the new multireddit.
        :param subreddits: Subreddits to add to the new multireddit. Can be a list of
            either :class:`.Subreddit` instances or subreddit display names.
        :param description_md: Description for the new multireddit, formatted in
            markdown.
        :param icon_name: Can be one of: ``art and design``, ``ask``, ``books``,
            ``business``, ``cars``, ``comics``, ``cute animals``, ``diy``,
            ``entertainment``, ``food and drink``, ``funny``, ``games``, ``grooming``,
            ``health``, ``life advice``, ``military``, ``models pinup``, ``music``,
            ``news``, ``philosophy``, ``pictures and gifs``, ``science``, ``shopping``,
            ``sports``, ``style``, ``tech``, ``travel``, ``unusual stories``, ``video``,
            or ``None`` (default ``None``).
        :param key_color: RGB hex color code of the form ``"#FFFFFF"``.
        :param visibility: Can be one of: ``hidden``, ``private``, or ``public``
            (default: private).
        :param weighting_scheme: Can be one of: ``classic`` or ``fresh`` (default:
            classic).

        :returns: The new :class:`.Multireddit` object.

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
        """Return an instance of :class:`.Subreddit`.

        :param display_name: The name of the subreddit.
        :param fetch: Determines if Async PRAW will fetch the object (default: False).

        If you need the object fetched right away (e.g., to access an attribute) you can
        do:

        .. code-block:: python

            subreddit = await reddit.subreddit("test", fetch=True)
            print(subreddit.subscribers)

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
        """Create a new :class:`.Subreddit`.

        :param name: The name for the new subreddit.
        :param title: The title of the subreddit. When ``None`` or ``""`` use the value
            of ``name``.
        :param link_type: The types of submissions users can make. One of ``any``,
            ``link``, or ``self`` (default: any).
        :param subreddit_type: One of ``archived``, ``employees_only``, ``gold_only``,
            ``gold_restricted``, ``private``, ``public``, or ``restricted`` (default:
            public).
        :param wikimode: One of ``anyone``, ``disabled``, or ``modonly`` (default:
            ``disabled``).

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
