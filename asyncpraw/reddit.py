"""Provide the Reddit class."""

from __future__ import annotations

import asyncio
import configparser
import os
import re
from copy import copy
from itertools import islice
from logging import getLogger
from typing import IO, TYPE_CHECKING, Any
from urllib.parse import urlparse

from asyncprawcore import (
    Authorizer,
    DeviceIDAuthorizer,
    ReadOnlyAuthorizer,
    Redirect,
    Requestor,
    ScriptAuthorizer,
    TrustedAuthenticator,
    UntrustedAuthenticator,
    session,
)
from asyncprawcore.exceptions import BadRequest

from asyncpraw import models
from asyncpraw.config import Config
from asyncpraw.const import API_PATH, USER_AGENT_FORMAT, __version__
from asyncpraw.exceptions import ClientException, MissingRequiredAttributeException, RedditAPIException
from asyncpraw.objector import Objector

try:
    from update_checker import update_check

    UPDATE_CHECKER_MISSING = False
except ImportError:  # pragma: no cover
    UPDATE_CHECKER_MISSING = True

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import AsyncGenerator, Iterable

    import asyncprawcore

    import asyncpraw
    import asyncpraw.models

Comment = models.Comment
Redditor = models.Redditor
Submission = models.Submission
Subreddit = models.Subreddit

logger = getLogger("asyncpraw")


class Reddit:
    """The Reddit class provides convenient access to Reddit's API.

    Instances of this class are the gateway to interacting with Reddit's API through
    Async PRAW. The canonical way to obtain an instance of this class is via:

    .. code-block:: python

        import asyncpraw

        reddit = asyncpraw.Reddit(
            client_id="CLIENT_ID",
            client_secret="CLIENT_SECRET",
            password="PASSWORD",
            user_agent="USERAGENT",
            username="USERNAME",
        )

    """

    update_checked = False
    _ratelimit_regex = re.compile(r"([0-9]{1,3}) (milliseconds?|seconds?|minutes?)")

    @property
    def _next_unique(self) -> int:
        value = self._unique_counter
        self._unique_counter += 1
        return value

    @property
    def read_only(self) -> bool:
        """Return ``True`` when using the ``ReadOnlyAuthorizer``."""
        return self._core == self._read_only_core

    @read_only.setter
    def read_only(self, value: bool) -> None:
        """Set or unset the use of the ReadOnlyAuthorizer.

        :raises: :class:`.ClientException` when attempting to unset ``read_only`` and
            only the ``ReadOnlyAuthorizer`` is available.

        """
        if value:
            self._core = self._read_only_core
        elif self._authorized_core is None:
            msg = "read_only cannot be unset as only the ReadOnlyAuthorizer is available."
            raise ClientException(msg)
        else:
            self._core = self._authorized_core

    async def __aenter__(self):  # noqa: ANN204
        """Handle the context manager open."""
        return self

    async def __aexit__(self, *_: object) -> None:
        """Handle the context manager close."""
        await self.close()

    def __deepcopy__(self, memodict: dict[str, Any] | None = None) -> Reddit:
        """Shallow copy on deepcopy.

        A shallow copied is performed on deepcopy as
        :py:class:`asyncio.AbstractEventLoop` cannot be deepcopied.

        """
        if memodict is None:
            memodict = {}  # pragma: no cover
        return copy(self)

    def __init__(
        self,
        site_name: str | None = None,
        *,
        config_interpolation: str | None = None,
        requestor_class: type[asyncprawcore.requestor.Requestor] | None = None,
        requestor_kwargs: dict[str, Any] | None = None,
        **config_settings: str | bool | int | None,
    ) -> None:
        """Initialize a :class:`.Reddit` instance.

        :param site_name: The name of a section in your ``praw.ini`` file from which to
            load settings from. This parameter, in tandem with an appropriately
            configured ``praw.ini``, file is useful if you wish to easily save
            credentials for different applications, or communicate with other servers
            running Reddit. If ``site_name`` is ``None``, then the site name will be
            looked for in the environment variable ``praw_site``. If it is not found
            there, the ``DEFAULT`` site will be used (default: ``None``).
        :param config_interpolation: Config parser interpolation type that will be
            passed to :class:`.Config` (default: ``None``).
        :param requestor_class: A class that will be used to create a requestor. If not
            set, use ``asyncprawcore.Requestor`` (default: ``None``).
        :param requestor_kwargs: Dictionary with additional keyword arguments used to
            initialize the requestor (default: ``None``).

        Additional keyword arguments will be used to initialize the :class:`.Config`
        object. This can be used to specify configuration settings during instantiation
        of the :class:`.Reddit` instance. For more details, please see
        :ref:`configuration`.

        Required settings are:

        - ``client_id``
        - ``client_secret`` (for installed applications set this value to ``None``)
        - ``user_agent``

        The ``requestor_class`` and ``requestor_kwargs`` allow for customization of the
        requestor :class:`.Reddit` will use. This allows, e.g., easily adding behavior
        to the requestor or wrapping its |ClientSession|_ in a caching layer. Example
        usage:

        .. |ClientSession| replace:: ``ClientSession``

        .. _clientsession: https://docs.aiohttp.org/en/stable/client_advanced.html

        .. code-block:: python

            import json

            import aiohttp
            from asyncprawcore import Requestor

            from asyncpraw import Reddit


            class JSONDebugRequestor(Requestor):
                async def request(self, *args, **kwargs):
                    response = await super().request(*args, **kwargs)
                    print(json.dumps(await response.json(), indent=4))
                    return response


            my_session = aiohttp.ClientSession(trust_env=True)
            reddit = Reddit(
                ..., requestor_class=JSONDebugRequestor, requestor_kwargs={"session": my_session}
            )

        You can automatically close the requestor session by using this class as an
        asynchronous context manager:

        .. code-block:: python

            async with Reddit(...) as reddit:
                print(await reddit.user.me())

        You can also call :meth:`.Reddit.close`:

        .. code-block:: python

            reddit = Reddit(...)
            # do stuff with reddit
            ...
            # then close the requestor when done
            await reddit.close()

        """
        self._core = self._authorized_core = self._read_only_core = None
        self._objector = None
        self._unique_counter = 0

        try:
            config_section = (
                site_name or os.getenv("praw_site") or "DEFAULT"  # noqa: SIM112
            )
            self.config = Config(config_section, config_interpolation, **config_settings)
        except configparser.NoSectionError as exc:
            help_message = (
                "You provided the name of a praw.ini configuration which does not"
                " exist.\n\nFor help with creating a Reddit instance,"
                " visit\nhttps://asyncpraw.readthedocs.io/en/latest/code_overview/reddit_instance.html\n\nFor"
                " help on configuring Async PRAW,"
                " visit\nhttps://asyncpraw.readthedocs.io/en/latest/getting_started/configuration.html"
            )
            if site_name is not None:
                exc.message += f"\n{help_message}"
            raise

        required_message = (
            "Required configuration setting {!r} missing. \nThis setting can be"
            " provided in a praw.ini file, as a keyword argument to the Reddit class"
            " constructor, or as an environment variable."
        )
        for attribute in ("client_id", "user_agent"):
            if getattr(self.config, attribute) in {self.config.CONFIG_NOT_SET, None}:
                raise MissingRequiredAttributeException(required_message.format(attribute))
        if self.config.client_secret is self.config.CONFIG_NOT_SET:
            msg = f"{required_message.format('client_secret')}\nFor installed applications this value must be set to None via a keyword argument to the Reddit class constructor."
            raise MissingRequiredAttributeException(msg)
        self._check_for_update()
        self._prepare_objector()
        self.requestor = self._prepare_asyncprawcore(requestor_class=requestor_class, requestor_kwargs=requestor_kwargs)

        self.auth = models.Auth(self, None)
        """An instance of :class:`.Auth`.

        Provides the interface for interacting with installed and web applications.

        .. seealso::

            :ref:`auth_url`

        """

        self.drafts = models.DraftHelper(self, None)
        """An instance of :class:`.DraftHelper`.

        Provides the interface for working with :class:`.Draft` instances.

        For example, to list the currently authenticated user's drafts:

        .. code-block:: python

            drafts = await reddit.drafts()

        You can also asynchronously iterate through the currently authenticated user's
        drafts:

        .. code-block:: python

            async for draft in reddit.drafts():
                # do stuff with draft
                ...

        To create a draft on r/test run:

        .. code-block:: python

            await reddit.drafts.create(title="title", selftext="selftext", subreddit="test")

        """

        self.front = models.Front(self)
        """An instance of :class:`.Front`.

        Provides the interface for interacting with front page listings. For example:

        .. code-block:: python

            async for submission in reddit.front.hot():
                print(submission)

        """

        self.inbox = models.Inbox(self, None)
        """An instance of :class:`.Inbox`.

        Provides the interface to a user's inbox which produces :class:`.Message`,
        :class:`.Comment`, and :class:`.Submission` instances. For example, to iterate
        through comments which mention the authorized user run:

        .. code-block:: python

            async for comment in reddit.inbox.mentions():
                print(comment)

        """

        self.live = models.LiveHelper(self, None)
        """An instance of :class:`.LiveHelper`.

        Provides the interface for working with :class:`.LiveThread` instances. At
        present only new live threads can be created.

        .. code-block:: python

            await reddit.live.create(title="title", description="description")

        """

        self.multireddit = models.MultiredditHelper(self, None)
        """An instance of :class:`.MultiredditHelper`.

        Provides the interface to working with :class:`.Multireddit` instances. For
        example, you can obtain a :class:`.Multireddit` instance via:

        .. code-block:: python

            multireddit = await reddit.multireddit("samuraisam", "programming")

        If you want to obtain a fetched :class:`.Multireddit` instance you can do:

        .. code-block:: python

            multireddit = await reddit.multireddit(
                redditor="samuraisam", name="programming", fetch=True
            )

        """

        self.notes = models.RedditModNotes(self)
        r"""An instance of :class:`.RedditModNotes`.

        Provides the interface for working with :class:`.ModNote`\ s for multiple
        redditors across multiple subreddits.

        .. note::

            The authenticated user must be a moderator of the provided subreddit(s).

        For example, the latest note for u/spez in r/redditdev and r/test, and for
        u/bboe in r/redditdev can be iterated through like so:

        .. code-block:: python

            redditor = await reddit.redditor("bboe")
            subreddit = await reddit.subreddit("redditdev")

            pairs = [(subreddit, "spez"), ("test", "spez"), (subreddit, redditor)]

            async for note in reddit.notes(pairs=pairs):
                print(f"{note.label}: {note.note}")

        """

        self.redditors = models.Redditors(self, None)
        """An instance of :class:`.Redditors`.

        Provides the interface for :class:`.Redditor` discovery. For example, to iterate
        over the newest Redditors, run:

        .. code-block:: python

            async for redditor in reddit.redditors.new(limit=None):
                print(redditor)

        """

        self.subreddit = models.SubredditHelper(self, None)
        """An instance of :class:`.SubredditHelper`.

        Provides the interface to working with :class:`.Subreddit` instances. For
        example, to create a :class:`.Subreddit` run:

        .. code-block:: python

            await reddit.subreddit.create(name="coolnewsubname")

        To obtain a lazy :class:`.Subreddit` instance run:

        .. code-block:: python

            await reddit.subreddit("test")

        To obtain a fetched :class:`.Subreddit` instance run:

        .. code-block:: python

            await reddit.subreddit("test", fetch=True)

        Multiple subreddits can be combined and filtered views of r/all can also be used
        just like a subreddit:

        .. code-block:: python

            await reddit.subreddit("redditdev+learnpython+botwatch")
            await reddit.subreddit("all-redditdev-learnpython")

        """

        self.subreddits = models.Subreddits(self, None)
        """An instance of :class:`.Subreddits`.

        Provides the interface for :class:`.Subreddit` discovery. For example, to
        iterate over the set of default subreddits run:

        .. code-block:: python

            async for subreddit in reddit.subreddits.default(limit=None):
                print(subreddit)

        """

        self.user = models.User(self)
        """An instance of :class:`.User`.

        Provides the interface to the currently authorized :class:`.Redditor`. For
        example, to get the name of the current user run:

        .. code-block:: python

            print(await reddit.user.me())

        """

    def _check_for_update(self) -> None:
        if UPDATE_CHECKER_MISSING:
            return
        if not Reddit.update_checked and self.config.check_for_updates:
            update_check(__package__, __version__)
            Reddit.update_checked = True

    def _handle_rate_limit(self, exception: RedditAPIException) -> int | float | None:
        for item in exception.items:
            if item.error_type == "RATELIMIT":
                amount_search = self._ratelimit_regex.search(item.message)
                if not amount_search:
                    break
                seconds = int(amount_search.group(1))
                if amount_search.group(2).startswith("minute"):
                    seconds *= 60
                elif amount_search.group(2).startswith("millisecond"):
                    seconds = 0
                if seconds <= int(self.config.ratelimit_seconds):
                    return seconds + 1
        return None

    async def _objectify_request(
        self,
        *,
        data: dict[str, str | Any] | bytes | IO | str | None = None,
        files: dict[str, IO] | None = None,
        json: dict[Any, Any] | list[Any] | None = None,
        method: str = "",
        params: str | dict[str, str] | None = None,
        path: str = "",
    ) -> Any:
        """Run a request through the ``Objector``.

        :param data: Dictionary, bytes, or file-like object to send in the body of the
            request (default: ``None``).
        :param files: Dictionary, filename to file (like) object mapping (default:
            ``None``).
        :param json: JSON-serializable object to send in the body of the request with a
            Content-Type header of application/json (default: ``None``). If ``json`` is
            provided, ``data`` should not be.
        :param method: The HTTP method (e.g., ``"GET"``, ``"POST"``, ``"PUT"``,
            ``"DELETE"``).
        :param params: The query parameters to add to the request (default: ``None``).
        :param path: The path to fetch.

        """
        return self._objector.objectify(
            data=await self.request(
                data=data,
                files=files,
                json=json,
                method=method,
                params=params,
                path=path,
            )
        )

    def _prepare_asyncprawcore(
        self,
        *,
        requestor_class: type[Requestor] | None = None,
        requestor_kwargs: Any | None = None,
    ) -> Requestor:
        requestor_class = requestor_class or Requestor
        requestor_kwargs = requestor_kwargs or {}

        requestor = requestor_class(
            USER_AGENT_FORMAT.format(self.config.user_agent),
            self.config.oauth_url,
            self.config.reddit_url,
            **requestor_kwargs,
        )

        if self.config.client_secret:
            self._prepare_trusted_asyncprawcore(requestor)
        else:
            self._prepare_untrusted_asyncprawcore(requestor)

        return requestor

    def _prepare_common_authorizer(self, authenticator: asyncprawcore.auth.BaseAuthenticator) -> None:
        if self.config.refresh_token:
            authorizer = Authorizer(authenticator, refresh_token=self.config.refresh_token)
        else:
            self._core = self._read_only_core
            return
        self._core = self._authorized_core = session(authorizer=authorizer, window_size=self.config.window_size)

    def _prepare_objector(self) -> None:
        mappings = {
            self.config.kinds["comment"]: models.Comment,
            self.config.kinds["message"]: models.Message,
            self.config.kinds["redditor"]: models.Redditor,
            self.config.kinds["submission"]: models.Submission,
            self.config.kinds["subreddit"]: models.Subreddit,
            self.config.kinds["trophy"]: models.Trophy,
            "Button": models.Button,
            "Collection": models.Collection,
            "Draft": models.Draft,
            "DraftList": models.DraftList,
            "Image": models.Image,
            "LabeledMulti": models.Multireddit,
            "Listing": models.Listing,
            "LiveUpdate": models.LiveUpdate,
            "LiveUpdateEvent": models.LiveThread,
            "MenuLink": models.MenuLink,
            "ModeratedList": models.ModeratedList,
            "ModmailAction": models.ModmailAction,
            "ModmailConversation": models.ModmailConversation,
            "ModmailConversations-list": models.ModmailConversationsListing,
            "ModmailMessage": models.ModmailMessage,
            "Submenu": models.Submenu,
            "TrophyList": models.TrophyList,
            "UserList": models.RedditorList,
            "UserSubreddit": models.UserSubreddit,
            "button": models.ButtonWidget,
            "calendar": models.Calendar,
            "community-list": models.CommunityList,
            "custom": models.CustomWidget,
            "id-card": models.IDCard,
            "image": models.ImageWidget,
            "menu": models.Menu,
            "modaction": models.ModAction,
            "moderator-list": models.ModeratorListing,
            "moderators": models.ModeratorsWidget,
            "mod_note": models.ModNote,
            "more": models.MoreComments,
            "post-flair": models.PostFlairWidget,
            "rule": models.Rule,
            "stylesheet": models.Stylesheet,
            "subreddit-rules": models.RulesWidget,
            "textarea": models.TextArea,
            "widget": models.Widget,
        }
        self._objector = Objector(self, mappings)

    def _prepare_trusted_asyncprawcore(self, requestor: Requestor) -> None:
        authenticator = TrustedAuthenticator(
            requestor,
            self.config.client_id,
            self.config.client_secret,
            self.config.redirect_uri,
        )
        read_only_authorizer = ReadOnlyAuthorizer(authenticator)
        self._read_only_core = session(authorizer=read_only_authorizer, window_size=self.config.window_size)

        if self.config.username and self.config.password:
            script_authorizer = ScriptAuthorizer(authenticator, self.config.username, self.config.password)
            self._core = self._authorized_core = session(
                authorizer=script_authorizer, window_size=self.config.window_size
            )
        else:
            self._prepare_common_authorizer(authenticator)

    def _prepare_untrusted_asyncprawcore(self, requestor: Requestor) -> None:
        authenticator = UntrustedAuthenticator(requestor, self.config.client_id, self.config.redirect_uri)
        read_only_authorizer = DeviceIDAuthorizer(authenticator)
        self._read_only_core = session(authorizer=read_only_authorizer, window_size=self.config.window_size)
        self._prepare_common_authorizer(authenticator)

    async def _resolve_share_url(self, url: str) -> str:
        """Return the canonical URL for a given share URL."""
        parts = urlparse(url).path.rstrip("/").split("/")
        if "s" in parts:  # handling new share urls from mobile apps
            try:
                await self.get(url)
            except Redirect as e:
                return e.response.headers.get("location")
        return url

    async def close(self) -> None:
        """Close the requestor."""
        await self.requestor.close()

    async def comment(
        self,
        id: str | None = None,
        *,
        fetch: bool = True,
        url: str | None = None,
    ) -> models.Comment:
        """Return an instance of :class:`.Comment`.

        :param id: The ID of the comment.
        :param fetch: Determines if Async PRAW will fetch the object (default:
            ``True``).
        :param url: A permalink pointing to the comment.

        If you don't need the object fetched right away (e.g., to utilize a class
        method) then you can do:

        .. code-block:: python

            comment = await reddit.comment("comment_id", fetch=False)
            await comment.reply("reply")

        .. note::

            If call this with ``fetch=False`` and you need to obtain the comment's
            replies, you will need to call this without ``fetch=False`` or call
            :meth:`~.Comment.refresh` on the returned :class:`.Comment`.

        """
        if url:
            url = await self._resolve_share_url(url)
        comment = models.Comment(self, id=id, url=url)
        if fetch:
            await comment._fetch()
        return comment

    async def delete(
        self,
        path: str,
        *,
        data: dict[str, str | Any] | bytes | IO | str | None = None,
        json: dict[Any, Any] | list[Any] | None = None,
        params: str | dict[str, str] | None = None,
    ) -> Any:
        """Return parsed objects returned from a DELETE request to ``path``.

        :param path: The path to fetch.
        :param data: Dictionary, bytes, or file-like object to send in the body of the
            request (default: ``None``).
        :param json: JSON-serializable object to send in the body of the request with a
            Content-Type header of application/json (default: ``None``). If ``json`` is
            provided, ``data`` should not be.
        :param params: The query parameters to add to the request (default: ``None``).

        """
        return await self._objectify_request(data=data, json=json, method="DELETE", params=params, path=path)

    def domain(self, domain: str) -> models.DomainListing:
        """Return an instance of :class:`.DomainListing`.

        :param domain: The domain to obtain submission listings for.

        """
        return models.DomainListing(self, domain)

    async def get(
        self,
        path: str,
        *,
        params: str | dict[str, str | int] | None = None,
    ) -> Any:
        """Return parsed objects returned from a GET request to ``path``.

        :param path: The path to fetch.
        :param params: The query parameters to add to the request (default: ``None``).

        """
        return await self._objectify_request(method="GET", params=params, path=path)

    def info(
        self,
        *,
        fullnames: Iterable[str] | None = None,
        subreddits: Iterable[asyncpraw.models.Subreddit | str] | None = None,
        url: str | None = None,
    ) -> AsyncGenerator[
        asyncpraw.models.Subreddit | asyncpraw.models.Comment | asyncpraw.models.Submission,
        None,
    ]:
        """Fetch information about each item in ``fullnames``, ``url``, or ``subreddits``.

        :param fullnames: A list of fullnames for comments, submissions, and/or
            subreddits.
        :param subreddits: A list of subreddit names or :class:`.Subreddit` objects to
            retrieve subreddits from.
        :param url: A url (as a string) to retrieve lists of link submissions from.

        :returns: A generator that yields found items in their relative order.

        Items that cannot be matched will not be generated. Requests will be issued in
        batches for each 100 fullnames.

        .. note::

            For comments that are retrieved via this method, if you want to obtain its
            replies, you will need to call :meth:`~.Comment.refresh` on the yielded
            :class:`.Comment`.

        .. note::

            When using the URL option, it is important to be aware that URLs are treated
            literally by Reddit's API. As such, the URLs ``"youtube.com"`` and
            ``"https://www.youtube.com"`` will provide a different set of submissions.

        """
        set_count = sum(1 for value in (fullnames, url, subreddits) if value is not None)
        if set_count != 1:
            msg = "Either 'fullnames', 'url', or 'subreddits' must be provided."
            raise TypeError(msg)

        is_using_fullnames = fullnames is not None
        ids_or_names = fullnames if is_using_fullnames else subreddits

        if ids_or_names is not None:
            if isinstance(ids_or_names, str):
                msg = "'fullnames' and 'subreddits' must be a non-str iterable."
                raise TypeError(msg)

            api_parameter_name = "id" if is_using_fullnames else "sr_name"

            async def generator(
                names: Iterable[str | asyncpraw.models.Subreddit],
            ) -> AsyncGenerator[
                asyncpraw.models.Subreddit | asyncpraw.models.Comment | asyncpraw.models.Submission,
                None,
                None,
            ]:
                iterable = iter(names) if is_using_fullnames else iter([str(item) for item in names])
                while True:
                    chunk = list(islice(iterable, 100))
                    if not chunk:
                        break
                    params = {api_parameter_name: ",".join(chunk)}
                    for result in await self.get(API_PATH["info"], params=params):
                        yield result

            return generator(ids_or_names)

        async def generator(
            _url: str,
        ) -> AsyncGenerator[
            asyncpraw.models.Subreddit | asyncpraw.models.Comment | asyncpraw.models.Submission,
            None,
            None,
        ]:
            params = {"url": _url}
            for result in await self.get(API_PATH["info"], params=params):
                yield result

        return generator(url)

    async def patch(
        self,
        path: str,
        *,
        data: dict[str, str | Any] | bytes | IO | str | None = None,
        json: dict[Any, Any] | list[Any] | None = None,
        params: str | dict[str, str] | None = None,
    ) -> Any:
        """Return parsed objects returned from a PATCH request to ``path``.

        :param path: The path to fetch.
        :param data: Dictionary, bytes, or file-like object to send in the body of the
            request (default: ``None``).
        :param json: JSON-serializable object to send in the body of the request with a
            Content-Type header of application/json (default: ``None``). If ``json`` is
            provided, ``data`` should not be.
        :param params: The query parameters to add to the request (default: ``None``).

        """
        return await self._objectify_request(data=data, json=json, method="PATCH", params=params, path=path)

    async def post(
        self,
        path: str,
        *,
        data: dict[str, str | Any] | bytes | IO | str | None = None,
        files: dict[str, IO] | None = None,
        json: dict[Any, Any] | list[Any] | None = None,
        params: str | dict[str, str] | None = None,
    ) -> Any:
        """Return parsed objects returned from a POST request to ``path``.

        :param path: The path to fetch.
        :param data: Dictionary, bytes, or file-like object to send in the body of the
            request (default: ``None``).
        :param files: Dictionary, filename to file (like) object mapping (default:
            ``None``).
        :param json: JSON-serializable object to send in the body of the request with a
            Content-Type header of application/json (default: ``None``). If ``json`` is
            provided, ``data`` should not be.
        :param params: The query parameters to add to the request (default: ``None``).

        """
        if json is None:
            data = data or {}

        attempts = 3
        last_exception = None
        while attempts > 0:
            attempts -= 1
            try:
                return await self._objectify_request(
                    data=data,
                    files=files,
                    json=json,
                    method="POST",
                    params=params,
                    path=path,
                )
            except RedditAPIException as exception:
                last_exception = exception
                seconds = self._handle_rate_limit(exception=exception)
                if seconds is None:
                    break
                second_string = "second" if seconds == 1 else "seconds"
                logger.debug("Rate limit hit, sleeping for %d %s", seconds, second_string)
                await asyncio.sleep(seconds)
        raise last_exception

    async def put(
        self,
        path: str,
        *,
        data: dict[str, str | Any] | bytes | IO | str | None = None,
        json: dict[Any, Any] | list[Any] | None = None,
    ) -> Any:
        """Return parsed objects returned from a PUT request to ``path``.

        :param path: The path to fetch.
        :param data: Dictionary, bytes, or file-like object to send in the body of the
            request (default: ``None``).
        :param json: JSON-serializable object to send in the body of the request with a
            Content-Type header of application/json (default: ``None``). If ``json`` is
            provided, ``data`` should not be.

        """
        return await self._objectify_request(data=data, json=json, method="PUT", path=path)

    async def redditor(
        self,
        name: str | None = None,
        *,
        fetch: bool = False,
        fullname: str | None = None,
    ) -> asyncpraw.models.Redditor:
        """Return an instance of :class:`.Redditor`.

        :param name: The name of the redditor.
        :param fetch: Determines if Async PRAW will fetch the object (default:
            ``False``).
        :param fullname: The fullname of the redditor, starting with ``t2_``.

        Either ``name`` or ``fullname`` can be provided, but not both.

        """
        redditor = models.Redditor(self, name=name, fullname=fullname)
        if fetch:
            await redditor._fetch()
        return redditor

    async def request(
        self,
        *,
        data: dict[str, str | Any] | bytes | IO | str | None = None,
        files: dict[str, IO] | None = None,
        json: dict[Any, Any] | list[Any] | None = None,
        method: str,
        params: str | dict[str, str | int] | None = None,
        path: str,
    ) -> Any:
        """Return the parsed JSON data returned from a request to URL.

        :param data: Dictionary, bytes, or file-like object to send in the body of the
            request (default: ``None``).
        :param files: Dictionary, filename to file (like) object mapping (default:
            ``None``).
        :param json: JSON-serializable object to send in the body of the request with a
            Content-Type header of application/json (default: ``None``). If ``json`` is
            provided, ``data`` should not be.
        :param method: The HTTP method (e.g., ``"GET"``, ``"POST"``, ``"PUT"``,
            ``"DELETE"``).
        :param params: The query parameters to add to the request (default: ``None``).
        :param path: The path to fetch.

        """
        if data and json:
            msg = "At most one of 'data' or 'json' is supported."
            raise ClientException(msg)
        try:
            return await self._core.request(
                data=data,
                files=files,
                json=json,
                method=method,
                params=params,
                path=path,
            )
        except BadRequest as exception:
            try:
                data = await exception.response.json(content_type=None)
            except ValueError:
                text = await exception.response.text()
                if text:
                    data = {"reason": text}
                else:
                    raise exception from None
            if set(data) == {"error", "message"}:
                raise
            explanation = data.get("explanation")
            if "fields" in data:
                assert len(data["fields"]) == 1
                field = data["fields"][0]
            else:
                field = None
            raise RedditAPIException([data["reason"], explanation, field]) from exception

    async def submission(
        self,
        id: str | None = None,
        *,
        fetch: bool = True,
        url: str | None = None,
    ) -> asyncpraw.models.Submission:
        """Return an instance of :class:`.Submission`.

        :param id: A Reddit base36 submission ID, e.g., ``2gmzqe``.
        :param fetch: Determines if Async PRAW will fetch the object (default:
            ``True``).
        :param url: A URL supported by :meth:`.Submission.id_from_url`.

        Either ``id`` or ``url`` can be provided, but not both.

        If you don't need the object fetched right away (e.g., to utilize a class
        method) then you can do:

        .. code-block:: python

            submission = await reddit.submission("submission_id", fetch=False)
            await submission.mod.remove()

        """
        if url:
            url = await self._resolve_share_url(url)
        submission = models.Submission(self, id=id, url=url)
        if fetch:
            await submission._fetch()
        return submission

    async def username_available(self, name: str) -> bool:
        """Check to see if the username is available.

        For example, to check if the username ``bboe`` is available, try:

        .. code-block:: python

            await reddit.username_available("bboe")

        """
        return await self._objectify_request(method="GET", params={"user": name}, path=API_PATH["username_available"])
