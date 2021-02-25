"""Provide the Subreddit class."""

# pylint: disable=too-many-lines
import socket
from asyncio import TimeoutError
from copy import deepcopy
from csv import writer
from io import StringIO
from json import dumps
from os.path import basename, dirname, isfile, join
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Dict,
    Iterator,
    List,
    Optional,
    Union,
)
from urllib.parse import urljoin
from xml.etree.ElementTree import XML

from aiohttp.web_ws import WebSocketError
from asyncprawcore import Redirect
from requests import Response

from ...const import API_PATH, JPEG_HEADER
from ...exceptions import (
    ClientException,
    InvalidFlairTemplateID,
    MediaPostFailed,
    RedditAPIException,
    TooLargeMediaException,
    WebSocketException,
)
from ...util.cache import cachedproperty
from ..listing.generator import ListingGenerator
from ..listing.mixins import SubredditListingMixin
from ..util import permissions_string, stream_generator
from .base import RedditBase
from .emoji import SubredditEmoji
from .mixins import FullnameMixin, MessageableMixin
from .modmail import ModmailConversation
from .removal_reasons import SubredditRemovalReasons
from .rules import SubredditRules
from .widgets import SubredditWidgets, WidgetEncoder
from .wikipage import WikiPage

if TYPE_CHECKING:  # pragma: no cover
    from .... import asyncpraw


class Subreddit(MessageableMixin, SubredditListingMixin, FullnameMixin, RedditBase):
    """A class for Subreddits.

    To obtain an instance of this class for subreddit ``r/redditdev`` execute:

    .. code-block:: python

        subreddit = await reddit.subreddit("redditdev")

    To obtain a lazy instance of this class for subreddit ``r/redditdev`` execute:

    .. code-block:: python

        subreddit = await reddit.subreddit("redditdev")

    While ``r/all`` is not a real subreddit, it can still be treated like one. The
    following outputs the titles of the 25 hottest submissions in ``r/all``:

    .. code-block:: python

        subreddit = await reddit.subreddit("all")
        async for submission in subreddit.hot(limit=25):
            print(submission.title)

    Multiple subreddits can be combined with a ``+`` like so:

    .. code-block:: python

        subreddit = await reddit.subreddit("redditdev+learnpython")
        async for submission in subreddit.top("all"):
            print(submission)

    Subreddits can be filtered from combined listings as follows.

    .. note::

        These filters are ignored by certain methods, including :attr:`.comments`,
        :meth:`.gilded`, and :meth:`.SubredditStream.comments`.

    .. code-block:: python

        subreddit = await reddit.subreddit("all-redditdev")
        async for submission in subreddit.new():
            print(submission)

    **Typical Attributes**

    This table describes attributes that typically belong to objects of this class.
    Since attributes are dynamically provided (see
    :ref:`determine-available-attributes-of-an-object`), there is not a guarantee that
    these attributes will always be present, nor is this list necessarily complete.

    ========================= ==========================================================
    Attribute                 Description
    ========================= ==========================================================
    ``can_assign_link_flair`` Whether users can assign their own link flair.
    ``can_assign_user_flair`` Whether users can assign their own user flair.
    ``created_utc``           Time the subreddit was created, represented in `Unix
                              Time`_.
    ``description``           Subreddit description, in Markdown.
    ``description_html``      Subreddit description, in HTML.
    ``display_name``          Name of the subreddit.
    ``id``                    ID of the subreddit.
    ``name``                  Fullname of the subreddit.
    ``over18``                Whether the subreddit is NSFW.
    ``public_description``    Description of the subreddit, shown in searches and on the
                              "You must be invited to visit this community" page (if
                              applicable).
    ``spoilers_enabled``      Whether the spoiler tag feature is enabled.
    ``subscribers``           Count of subscribers.
    ``user_is_banned``        Whether the authenticated user is banned.
    ``user_is_moderator``     Whether the authenticated user is a moderator.
    ``user_is_subscriber``    Whether the authenticated user is subscribed.
    ========================= ==========================================================

    .. note::

        Trying to retrieve attributes of quarantined or private subreddits will result
        in a 403 error. Trying to retrieve attributes of a banned subreddit will result
        in a 404 error.

    .. _unix time: https://en.wikipedia.org/wiki/Unix_time

    """

    # pylint: disable=too-many-public-methods

    STR_FIELD = "display_name"
    MESSAGE_PREFIX = "#"

    @staticmethod
    async def _create_or_update(
        _reddit,
        allow_images=None,
        allow_post_crossposts=None,
        allow_top=None,
        collapse_deleted_comments=None,
        comment_score_hide_mins=None,
        description=None,
        domain=None,
        exclude_banned_modqueue=None,
        header_hover_text=None,
        hide_ads=None,
        lang=None,
        key_color=None,
        link_type=None,
        name=None,
        over_18=None,
        public_description=None,
        public_traffic=None,
        show_media=None,
        show_media_preview=None,
        spam_comments=None,
        spam_links=None,
        spam_selfposts=None,
        spoilers_enabled=None,
        sr=None,
        submit_link_label=None,
        submit_text=None,
        submit_text_label=None,
        subreddit_type=None,
        suggested_comment_sort=None,
        title=None,
        wiki_edit_age=None,
        wiki_edit_karma=None,
        wikimode=None,
        **other_settings,
    ):
        # pylint: disable=invalid-name,too-many-locals,too-many-arguments
        model = {
            "allow_images": allow_images,
            "allow_post_crossposts": allow_post_crossposts,
            "allow_top": allow_top,
            "collapse_deleted_comments": collapse_deleted_comments,
            "comment_score_hide_mins": comment_score_hide_mins,
            "description": description,
            "domain": domain,
            "exclude_banned_modqueue": exclude_banned_modqueue,
            "header-title": header_hover_text,  # Remap here - better name
            "hide_ads": hide_ads,
            "key_color": key_color,
            "lang": lang,
            "link_type": link_type,
            "name": name,
            "over_18": over_18,
            "public_description": public_description,
            "public_traffic": public_traffic,
            "show_media": show_media,
            "show_media_preview": show_media_preview,
            "spam_comments": spam_comments,
            "spam_links": spam_links,
            "spam_selfposts": spam_selfposts,
            "spoilers_enabled": spoilers_enabled,
            "sr": sr,
            "submit_link_label": submit_link_label,
            "submit_text": submit_text,
            "submit_text_label": submit_text_label,
            "suggested_comment_sort": suggested_comment_sort,
            "title": title,
            "type": subreddit_type,
            "wiki_edit_age": wiki_edit_age,
            "wiki_edit_karma": wiki_edit_karma,
            "wikimode": wikimode,
        }

        model.update(other_settings)

        await _reddit.post(API_PATH["site_admin"], data=model)

    @staticmethod
    def _subreddit_list(subreddit, other_subreddits):
        if other_subreddits:
            return ",".join([str(subreddit)] + [str(x) for x in other_subreddits])
        return str(subreddit)

    @staticmethod
    def _validate_gallery(images):
        for image in images:
            image_path = image.get("image_path", "")
            if image_path:
                if not isfile(image_path):
                    raise TypeError(f"{image_path!r} is not a valid image path.")
            else:
                raise TypeError("'image_path' is required.")
            if not len(image.get("caption", "")) <= 180:
                raise TypeError("Caption must be 180 characters or less.")

    @staticmethod
    def _validate_inline_media(inline_media: "asyncpraw.models.InlineMedia"):
        if not isfile(inline_media.path):
            raise ValueError(f"{inline_media.path!r} is not a valid file path.")

    @property
    def _kind(self) -> str:
        """Return the class's kind."""
        return self._reddit.config.kinds["subreddit"]

    @cachedproperty
    def banned(self) -> "asyncpraw.models.reddit.subreddit.SubredditRelationship":
        """Provide an instance of :class:`.SubredditRelationship`.

        For example, to ban a user try:

        .. code-block:: python

            subreddit = await reddit.subreddit("SUBREDDIT")
            await subreddit.banned.add("NAME", ban_reason="...")

        To list the banned users along with any notes, try:

        .. code-block:: python

            subreddit = await reddit.subreddit("SUBREDDIT")
            async for ban in subreddit.banned():
                print(f"{ban}: {ban.note}")

        """
        return SubredditRelationship(self, "banned")

    @cachedproperty
    def collections(self) -> "asyncpraw.models.reddit.collections.SubredditCollections":
        r"""Provide an instance of :class:`.SubredditCollections`.

        To see the permalinks of all :class:`.Collection`\ s that belong to a subreddit,
        try:

        .. code-block:: python

            subreddit = await reddit.subreddit("SUBREDDIT")
            async for collection in subreddit.collections:
                print(collection.permalink)

        To get a specific :class:`.Collection` by its UUID or permalink, use one of the
        following:

        .. code-block:: python

            subreddit = await reddit.subreddit("SUBREDDIT")

            collection = subreddit.collections("some_uuid")
            collection = subreddit.collections(
                permalink="https://reddit.com/r/SUBREDDIT/collection/some_uuid"
            )

        """
        return self._subreddit_collections_class(self._reddit, self)

    @cachedproperty
    def contributor(
        self,
    ) -> "asyncpraw.models.reddit.subreddit.ContributorRelationship":
        """Provide an instance of :class:`.ContributorRelationship`.

        Contributors are also known as approved submitters.

        To add a contributor try:

        .. code-block:: python

            subreddit = await reddit.subreddit("SUBREDDIT")
            await subreddit.contributor.add("NAME")

        """
        return ContributorRelationship(self, "contributor")

    @cachedproperty
    def emoji(self) -> SubredditEmoji:
        """Provide an instance of :class:`.SubredditEmoji`.

        This attribute can be used to discover all emoji for a subreddit:

        .. code-block:: python

            subreddit = await reddit.subreddit("iama")
            async for emoji in subreddit.emoji:
                print(emoji)

        A single emoji can be lazily retrieved via:

        .. code-block:: python

            subreddit = await reddit.subreddit("blah")
            emoji = await subreddit.emoji.get_emoji("emoji_name")

        .. note::

            Attempting to access attributes of an nonexistent emoji will result in a
            :class:`.ClientException`.

        """
        return SubredditEmoji(self)

    @cachedproperty
    def filters(self) -> "asyncpraw.models.reddit.subreddit.SubredditFilters":
        """Provide an instance of :class:`.SubredditFilters`.

        For example, to add a filter, run:

        .. code-block:: python

            subreddit = await reddit.subreddit("all")
            await subreddit.filters.add("subreddit_name")

        """
        return SubredditFilters(self)

    @cachedproperty
    def flair(self) -> "asyncpraw.models.reddit.subreddit.SubredditFlair":
        """Provide an instance of :class:`.SubredditFlair`.

        Use this attribute for interacting with a subreddit's flair. For example, to
        list all the flair for a subreddit which you have the ``flair`` moderator
        permission on try:

        .. code-block:: python

            subreddit = await reddit.subreddit("NAME")
            async for flair in subreddit.flair():
                print(flair)

        Flair templates can be interacted with through this attribute via:

        .. code-block:: python

            subreddit = await reddit.subreddit("NAME")
            async for template in subreddit.flair.templates:
                print(template)

        """
        return SubredditFlair(self)

    @cachedproperty
    def mod(self) -> "asyncpraw.models.reddit.subreddit.SubredditModeration":
        """Provide an instance of :class:`.SubredditModeration`.

        For example, to accept a moderation invite from subreddit ``r/test``:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            await subreddit.mod.accept_invite()

        """
        return SubredditModeration(self)

    @cachedproperty
    def moderator(self) -> "asyncpraw.models.reddit.subreddit.ModeratorRelationship":
        """Provide an instance of :class:`.ModeratorRelationship`.

        For example, to add a moderator try:

        .. code-block:: python

            subreddit = await reddit.subreddit("SUBREDDIT")
            await subreddit.moderator.add("NAME")

        To list the moderators along with their permissions try:

        .. code-block:: python

            subreddit = await reddit.subreddit("SUBREDDIT")
            async for moderator in subreddit.moderator:
                print(f"{moderator}: {moderator.mod_permissions}")

        """
        return ModeratorRelationship(self, "moderator")

    @cachedproperty
    def modmail(self) -> "asyncpraw.models.reddit.subreddit.Modmail":
        """Provide an instance of :class:`.Modmail`.

        For example, to send a new modmail from the subreddit ``r/test`` to user
        ``u/spez`` with the subject ``test`` along with a message body of ``hello``:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            await subreddit.modmail.create("test", "hello", "spez")

        """
        return Modmail(self)

    @cachedproperty
    def muted(self) -> "asyncpraw.models.reddit.subreddit.SubredditRelationship":
        """Provide an instance of :class:`.SubredditRelationship`.

        For example, muted users can be iterated through like so:

        .. code-block:: python

            subreddit = await reddit.subreddit("redditdev")
            async for mute in subreddit.muted():
                print("{mute}: {mute.note}")

        """
        return SubredditRelationship(self, "muted")

    @cachedproperty
    def quaran(self) -> "asyncpraw.models.reddit.subreddit.SubredditQuarantine":
        """Provide an instance of :class:`.SubredditQuarantine`.

        This property is named ``quaran`` because ``quarantine`` is a Subreddit
        attribute returned by Reddit to indicate whether or not a Subreddit is
        quarantined.

        To opt-in into a quarantined subreddit:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            await subreddit.quaran.opt_in()

        """
        return SubredditQuarantine(self)

    @cachedproperty
    def rules(self) -> SubredditRules:
        """Provide an instance of :class:`.SubredditRules`.

        Use this attribute for interacting with a subreddit's rules.

        For example, to list all the rules for a subreddit:

        .. code-block:: python

            subreddit = await reddit.subreddit("AskReddit")
            async for rule in subreddit.rules:
                print(rule)

        Moderators can also add rules to the subreddit. For example, to make a rule
        called ``"No spam"`` in the subreddit ``"NAME"``:

        .. code-block:: python

            subreddit = await reddit.subreddit("NAME")
            await subreddit.rules.mod.add(
                short_name="No spam", kind="all", description="Do not spam. Spam bad"
            )

        """
        return SubredditRules(self)

    @cachedproperty
    def stream(self) -> "asyncpraw.models.reddit.subreddit.SubredditStream":
        """Provide an instance of :class:`.SubredditStream`.

        Streams can be used to indefinitely retrieve new comments made to a subreddit,
        like:

        .. code-block:: python

            subreddit = await reddit.subreddit("iama")
            async for comment in subreddit.stream.comments():
                print(comment)

        Additionally, new submissions can be retrieved via the stream. In the following
        example all submissions are fetched via the special subreddit ``r/all``:

        .. code-block:: python

            subreddit = await reddit.subreddit("all")
            async for submission in subreddit.stream.submissions():
                print(submission)

        """
        return SubredditStream(self)

    @cachedproperty
    def stylesheet(self) -> "asyncpraw.models.reddit.subreddit.SubredditStylesheet":
        """Provide an instance of :class:`.SubredditStylesheet`.

        For example, to add the css data ``.test{color:blue}`` to the existing
        stylesheet:

        .. code-block:: python

            subreddit = await reddit.subreddit("SUBREDDIT")
            stylesheet = await subreddit.stylesheet()
            stylesheet.stylesheet += ".test{color:blue}"
            await subreddit.stylesheet.update(stylesheet.stylesheet)

        """
        return SubredditStylesheet(self)

    @cachedproperty
    def widgets(self) -> "asyncpraw.models.SubredditWidgets":
        """Provide an instance of :class:`.SubredditWidgets`.

        **Example usage**

        Get all sidebar widgets:

        .. code-block:: python

            subreddit = await reddit.subreddit("redditdev")
            async for widget in subreddit.widgets.sidebar:
                print(widget)

        Get ID card widget:

        .. code-block:: python

            subreddit = await reddit.subreddit("redditdev")
            widget = await subreddit.widgets.id_card()
            print(widget)

        """
        return SubredditWidgets(self)

    @cachedproperty
    def wiki(self) -> "asyncpraw.models.reddit.subreddit.SubredditWiki":
        """Provide an instance of :class:`.SubredditWiki`.

        This attribute can be used to discover all wikipages for a subreddit:

        .. code-block:: python

            subreddit = await reddit.subreddit("iama")
            async for wikipage in subreddit.wiki:
                print(wikipage)

        To fetch the content for a given wikipage try:

        .. code-block:: python

            subreddit = await reddit.subreddit("iama")
            wikipage = await subreddit.wiki.get_page("proof")
            print(wikipage.content_md)

        """
        return SubredditWiki(self)

    def __init__(
        self,
        reddit: "asyncpraw.Reddit",
        display_name: Optional[str] = None,
        _data: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a Subreddit instance.

        :param reddit: An instance of :class:`~.Reddit`.
        :param display_name: The name of the subreddit.

        .. note::

            This class should not be initialized directly. Instead obtain an instance
            via:

            .. code-block:: python

                # to lazily load a subreddit instance
                await reddit.subreddit("subreddit_name")

                # to fully load a subreddit instance
                await reddit.subreddit("subreddit_name", fetch=True)

        """
        if (display_name, _data).count(None) != 1:
            raise TypeError("Either `display_name` or `_data` must be provided.")
        if display_name:
            self.display_name = display_name
        super().__init__(reddit, _data=_data)
        self._path = API_PATH["subreddit"].format(subreddit=self)

    async def _convert_to_fancypants(self, markdown_text: str) -> dict:
        """Convert a Markdown string to a dict for use with the ``richtext_json`` param.

        :param markdown_text: A Markdown string to convert.

        :returns: A dict in ``richtext_json`` format.

        """
        text_data = {"output_mode": "rtjson", "markdown_text": markdown_text}
        rte_body = await self._reddit.post(API_PATH["convert_rte_body"], text_data)
        return rte_body["output"]

    def _fetch_info(self):
        return "subreddit_about", {"subreddit": self}, None

    async def _fetch_data(self) -> dict:
        name, fields, params = self._fetch_info()
        path = API_PATH[name].format(**fields)
        return await self._reddit.request("GET", path, params)

    async def _fetch(self):
        data = await self._fetch_data()
        data = data["data"]
        other = type(self)(self._reddit, _data=data)
        self.__dict__.update(other.__dict__)
        self._fetched = True

    def _parse_xml_response(self, response: Response):
        """Parse the XML from a response and raise any errors found."""
        xml = response.text
        root = XML(xml)
        tags = [element.tag for element in root]
        if tags[:4] == ["Code", "Message", "ProposedSize", "MaxSizeAllowed"]:
            # Returned if image is too big
            code, message, actual, maximum_size = [element.text for element in root[:4]]
            raise TooLargeMediaException(int(maximum_size), int(actual))

    async def _submit_media(self, data: dict, timeout: int, websocket_url: str = None):
        """Submit and return an `image`, `video`, or `videogif`.

        This is a helper method for submitting posts that are not link posts or self
        posts.

        """
        if websocket_url is None:
            await self._reddit.post(API_PATH["submit"], data=data)
        else:
            try:
                async with self._reddit._core._requestor._http.ws_connect(
                    websocket_url, timeout=timeout
                ) as websocket:
                    await self._reddit.post(API_PATH["submit"], data=data)
                    try:
                        ws_update = await websocket.receive_json()
                    except (
                        BlockingIOError,
                        socket.error,
                        TimeoutError,
                        WebSocketError,
                    ) as ws_exception:
                        raise WebSocketException(
                            "Websocket error. Check your media file. Your post may"
                            " still have been created.",
                            ws_exception,
                        )
            except (
                BlockingIOError,
                socket.error,
                TimeoutError,
                WebSocketError,
            ) as ws_exception:
                raise WebSocketException(
                    "Error establishing websocket connection.",
                    ws_exception,
                )
            if ws_update.get("type") == "failed":
                raise MediaPostFailed
            url = ws_update["payload"]["redirect"]
            return await self._reddit.submission(url=url)

    async def _upload_media(
        self,
        media_path: str,
        expected_mime_prefix: Optional[str] = None,
        upload_type: str = "link",
    ):
        """Upload media and return its URL and a websocket (Undocumented endpoint).

        :param expected_mime_prefix: If provided, enforce that the media has a mime type
            that starts with the provided prefix.
        :param upload_type: One of ``link``, ``gallery'', or ``selfpost``. (default:
            ``link``)

        :returns: A tuple containing ``(media_url, websocket_url)`` for the piece of
            media. The websocket URL can be used to determine when media processing is
            finished, or it can be ignored.

        """
        if media_path is None:
            media_path = join(
                dirname(dirname(dirname(__file__))), "images", "PRAW logo.png"
            )

        file_name = basename(media_path).lower()
        file_extension = file_name.rpartition(".")[2]
        mime_type = {
            "png": "image/png",
            "mov": "video/quicktime",
            "mp4": "video/mp4",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "gif": "image/gif",
        }.get(
            file_extension, "image/jpeg"
        )  # default to JPEG
        if (
            expected_mime_prefix is not None
            and mime_type.partition("/")[0] != expected_mime_prefix
        ):
            raise ClientException(
                f"Expected a mimetype starting with {expected_mime_prefix!r} but got"
                f" mimetype {mime_type!r} (from file extension {file_extension!r})."
            )
        img_data = {"filepath": file_name, "mimetype": mime_type}

        url = API_PATH["media_asset"]
        # until we learn otherwise, assume this request always succeeds
        upload_response = await self._reddit.post(url, data=img_data)
        upload_lease = upload_response["args"]
        upload_url = f"https:{upload_lease['action']}"
        upload_data = {item["name"]: item["value"] for item in upload_lease["fields"]}

        with open(media_path, "rb") as media:
            upload_data["file"] = media
            response = await self._reddit._core._requestor._http.post(
                upload_url, data=upload_data
            )
        if not response.status == 201:
            self._parse_xml_response(response)
        response.raise_for_status()

        websocket_url = upload_response["asset"]["websocket_url"]

        if upload_type == "link":
            return f"{upload_url}/{upload_data['key']}", websocket_url
        else:
            return upload_response["asset"]["asset_id"], websocket_url

    async def _upload_inline_media(self, inline_media: "asyncpraw.models.InlineMedia"):
        """Upload media for use in self posts and return ``inline_media``.

        :param inline_media: An :class:`.InlineMedia` object to validate and upload.

        """
        self._validate_inline_media(inline_media)
        inline_media.media_id, _ = await self._upload_media(
            inline_media.path, upload_type="selfpost"
        )
        return inline_media

    async def post_requirements(self) -> Dict[str, Union[str, int, bool]]:
        """Get the post requirements for a subreddit.

        :returns: A dict with the various requirements.

        The returned dict contains the following keys:

        - ``domain_blacklist``
        - ``body_restriction_policy``
        - ``domain_whitelist``
        - ``title_regexes``
        - ``body_blacklisted_strings``
        - ``body_required_strings``
        - ``title_text_min_length``
        - ``is_flair_required``
        - ``title_text_max_length``
        - ``body_regexes``
        - ``link_repost_age``
        - ``body_text_min_length``
        - ``link_restriction_policy``
        - ``body_text_max_length``
        - ``title_required_strings``
        - ``title_blacklisted_strings``
        - ``guidelines_text``
        - ``guidelines_display_policy``

        For example, to fetch the post requirements for ``r/test``:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            post_requirements = await subreddit.post_requirements
            print(post_requirements)

        """
        return await self._reddit.get(
            API_PATH["post_requirements"].format(subreddit=str(self))
        )

    async def random(self) -> Union["asyncpraw.models.Submission", None]:
        """Return a random Submission.

        Returns ``None`` on subreddits that do not support the random feature. One
        example, at the time of writing, is ``r/wallpapers``.

        For example, to get a random submission off of ``r/AskReddit``:

        .. code-block:: python

            subreddit = await reddit.subreddit("AskReddit")
            submission = await subreddit.random()
            print(submission.title)

        """
        url = API_PATH["subreddit_random"].format(subreddit=self)
        try:
            await self._reddit.get(url, params={"unique": self._reddit._next_unique})
        except Redirect as redirect:
            path = redirect.path
        try:
            submission = self._submission_class(
                self._reddit, url=urljoin(self._reddit.config.reddit_url, path)
            )
            await submission._fetch()
            return submission
        except ClientException:
            return None

    def search(
        self,
        query: str,
        sort: str = "relevance",
        syntax: str = "lucene",
        time_filter: str = "all",
        **generator_kwargs: Any,
    ) -> Iterator["asyncpraw.models.Submission"]:
        """Return a :class:`.ListingGenerator` for items that match ``query``.

        :param query: The query string to search for.
        :param sort: Can be one of: relevance, hot, top, new, comments. (default:
            relevance).
        :param syntax: Can be one of: cloudsearch, lucene, plain (default: lucene).
        :param time_filter: Can be one of: all, day, hour, month, week, year (default:
            all).

        For more information on building a search query see:
        https://www.reddit.com/wiki/search

        For example, to search all subreddits for ``praw`` try:

        .. code-block:: python

            subreddit = await reddit.subreddit("all")
            async for submission in subreddit.search("praw"):
                print(submission.title)

        """
        self._validate_time_filter(time_filter)
        not_all = self.display_name.lower() != "all"
        self._safely_add_arguments(
            generator_kwargs,
            "params",
            q=query,
            restrict_sr=not_all,
            sort=sort,
            syntax=syntax,
            t=time_filter,
        )
        url = API_PATH["search"].format(subreddit=self)
        return ListingGenerator(self._reddit, url, **generator_kwargs)

    async def sticky(self, number: int = 1) -> "asyncpraw.models.Submission":
        """Return a Submission object for a sticky of the subreddit.

        :param number: Specify which sticky to return. 1 appears at the top (default:
            1).

        :raises: ``asyncprawcore.NotFound`` if the sticky does not exist.

        For example, to get the stickied post on the subreddit ``r/test``:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            await subreddit.sticky()

        """
        url = API_PATH["about_sticky"].format(subreddit=self)
        try:
            await self._reddit.get(url, params={"num": number})
        except Redirect as redirect:
            path = redirect.path
        submission = self._submission_class(
            self._reddit, url=urljoin(self._reddit.config.reddit_url, path)
        )
        await submission._fetch()
        return submission

    async def submit(
        self,
        title: str,
        selftext: Optional[str] = None,
        url: Optional[str] = None,
        flair_id: Optional[str] = None,
        flair_text: Optional[str] = None,
        resubmit: bool = True,
        send_replies: bool = True,
        nsfw: bool = False,
        spoiler: bool = False,
        collection_id: Optional[str] = None,
        discussion_type: Optional[str] = None,
        inline_media: Optional[Dict[str, "asyncpraw.models.InlineMedia"]] = None,
    ) -> "asyncpraw.models.Submission":  # noqa: D301
        r"""Add a submission to the subreddit.

        :param title: The title of the submission.
        :param selftext: The Markdown formatted content for a ``text`` submission. Use
            an empty string, ``""``, to make a title-only submission.
        :param url: The URL for a ``link`` submission.
        :param collection_id: The UUID of a :class:`.Collection` to add the
            newly-submitted post to.
        :param flair_id: The flair template to select (default: None).
        :param flair_text: If the template's ``flair_text_editable`` value is True, this
            value will set a custom text (default: None). ``flair_id`` is required when
            ``flair_text`` is provided.
        :param resubmit: When False, an error will occur if the URL has already been
            submitted (default: True).
        :param send_replies: When True, messages will be sent to the submission author
            when comments are made to the submission (default: True).
        :param nsfw: Whether or not the submission should be marked NSFW (default:
            False).
        :param spoiler: Whether or not the submission should be marked as a spoiler
            (default: False).
        :param discussion_type: Set to ``CHAT`` to enable live discussion instead of
            traditional comments (default: None).
        :param inline_media: A dict of :class:`.InlineMedia` objects where the key is
            the placeholder name in ``selftext``.

        :returns: A :class:`~.Submission` object for the newly created submission.

        Either ``selftext`` or ``url`` can be provided, but not both.

        For example, to submit a URL to ``r/reddit_api_test`` do:

        .. code-block:: python

            title = "Async PRAW documentation"
            url = "https://asyncpraw.readthedocs.io"
            subreddit = await reddit.subreddit("reddit_api_test")
            await subreddit.submit(title, url=url)

        For example, to submit a self post with inline media do:

        .. code-block:: python

            from asyncpraw.models import InlineGif, InlineImage, InlineVideo

            gif = InlineGif("path/to/image.gif", "optional caption")
            image = InlineImage("path/to/image.jpg", "optional caption")
            video = InlineVideo("path/to/video.mp4", "optional caption")
            selftext = "Text with a gif {gif1} an image {image1} and a video {video1} inline"
            media = {"gif1": gif, "image1": image, "video1": video}
            subreddit = await reddit.subreddit("redditdev")
            await subreddit.submit("title", selftext=selftext, inline_media=media)

        .. note::

            Inserted media will have a padding of ``\\n\\n`` automatically added. This
            is due to the weirdness with Reddit's API. Using the example above the
            result selftext body will look like so:

            .. code-block::

                Text with a gif

                ![gif](u1rchuphryq51 "optional caption")

                an image

                ![img](srnr8tshryq51 "optional caption")

                and video

                ![video](gmc7rvthryq51 "optional caption")

                inline

        .. seealso::

            - :meth:`.submit_image` to submit images
            - :meth:`.submit_video` to submit videos and videogifs
            - :meth:`.submit_poll` to submit polls
            - :meth:`.submit_gallery`. to submit more than one image in the same post

        """
        if (bool(selftext) or selftext == "") == bool(url):
            raise TypeError("Either `selftext` or `url` must be provided.")

        data = {
            "sr": str(self),
            "resubmit": bool(resubmit),
            "sendreplies": bool(send_replies),
            "title": title,
            "nsfw": bool(nsfw),
            "spoiler": bool(spoiler),
            "validate_on_submit": self._reddit.validate_on_submit,
        }
        for key, value in (
            ("flair_id", flair_id),
            ("flair_text", flair_text),
            ("collection_id", collection_id),
            ("discussion_type", discussion_type),
        ):
            if value is not None:
                data[key] = value
        if selftext is not None:
            data.update(kind="self")
            if inline_media:
                body = selftext.format(
                    **{
                        placeholder: await self._upload_inline_media(media)
                        for placeholder, media in inline_media.items()
                    }
                )
                converted = await self._convert_to_fancypants(body)
                data.update(richtext_json=dumps(converted))
            else:
                data.update(text=selftext)
        else:
            data.update(kind="link", url=url)

        return await self._reddit.post(API_PATH["submit"], data=data)

    async def submit_gallery(
        self,
        title: str,
        images: List[Dict[str, str]],
        *,
        collection_id: Optional[str] = None,
        discussion_type: Optional[str] = None,
        flair_id: Optional[str] = None,
        flair_text: Optional[str] = None,
        nsfw: bool = False,
        send_replies: bool = True,
        spoiler: bool = False,
    ):
        """Add an image gallery submission to the subreddit.

        :param title: The title of the submission.
        :param images: The images to post in dict with the following structure:
            ``{"image_path": "path", "caption": "caption", "outbound_url": "url"}``,
            only ``"image_path"`` is required.
        :param collection_id: The UUID of a :class:`.Collection` to add the
            newly-submitted post to.
        :param discussion_type: Set to ``CHAT`` to enable live discussion instead of
            traditional comments (default: None).
        :param flair_id: The flair template to select (default: None).
        :param flair_text: If the template's ``flair_text_editable`` value is True, this
            value will set a custom text (default: None). ``flair_id`` is required when
            ``flair_text`` is provided.
        :param nsfw: Whether or not the submission should be marked NSFW (default:
            False).
        :param send_replies: When True, messages will be sent to the submission author
            when comments are made to the submission (default: True).
        :param spoiler: Whether or not the submission should be marked asa spoiler
            (default: False).

        :returns: A :class:`.Submission` object for the newly created submission.

        :raises: :class:`.ClientException` if ``image_path`` in ``images`` refers to a
            file that is not an image.

        For example, to submit an image gallery to ``r/reddit_api_test`` do:

        .. code-block:: python

            title = "My favorite pictures"
            image = "/path/to/image.png"
            image2 = "/path/to/image2.png"
            image3 = "/path/to/image3.png"
            images = [
                {"image_path": image},
                {
                    "image_path": image2,
                    "caption": "Image caption 2",
                },
                {
                    "image_path": image3,
                    "caption": "Image caption 3",
                    "outbound_url": "https://example.com/link3",
                },
            ]
            subreddit = await reddit.subreddit("reddit_api_test")
            await subreddit.submit_gallery(title, images)

        .. seealso::

            - :meth:`.submit` to submit url posts and selftexts
            - :meth:`.submit_image`. to submit single images
            - :meth:`.submit_poll` to submit polls
            - :meth:`.submit_video`. to submit videos and videogifs

        """
        self._validate_gallery(images)
        data = {
            "api_type": "json",
            "items": [],
            "nsfw": bool(nsfw),
            "sendreplies": bool(send_replies),
            "show_error_list": True,
            "spoiler": bool(spoiler),
            "sr": str(self),
            "title": title,
            "validate_on_submit": self._reddit.validate_on_submit,
        }
        for key, value in (
            ("flair_id", flair_id),
            ("flair_text", flair_text),
            ("collection_id", collection_id),
            ("discussion_type", discussion_type),
        ):
            if value is not None:
                data[key] = value
        for image in images:
            data["items"].append(
                {
                    "caption": image.get("caption", ""),
                    "outbound_url": image.get("outbound_url", ""),
                    "media_id": (
                        await self._upload_media(
                            image["image_path"],
                            expected_mime_prefix="image",
                            upload_type="gallery",
                        )
                    )[0],
                }
            )
        response = await self._reddit.request(
            "POST", API_PATH["submit_gallery_post"], json=data
        )
        response = response["json"]
        if response["errors"]:
            raise RedditAPIException(response["errors"])
        else:
            return await self._reddit.submission(url=response["data"]["url"])

    async def submit_image(
        self,
        title: str,
        image_path: str,
        flair_id: Optional[str] = None,
        flair_text: Optional[str] = None,
        resubmit: bool = True,
        send_replies: bool = True,
        nsfw: bool = False,
        spoiler: bool = False,
        timeout: int = 10,
        collection_id: Optional[str] = None,
        without_websockets: bool = False,
        discussion_type: Optional[str] = None,
    ):
        """Add an image submission to the subreddit.

        :param title: The title of the submission.
        :param image_path: The path to an image, to upload and post.
        :param collection_id: The UUID of a :class:`.Collection` to add the
            newly-submitted post to.
        :param flair_id: The flair template to select (default: None).
        :param flair_text: If the template's ``flair_text_editable`` value is True, this
            value will set a custom text (default: None). ``flair_id`` is required when
            ``flair_text`` is provided.
        :param resubmit: When False, an error will occur if the URL has already been
            submitted (default: True).
        :param send_replies: When True, messages will be sent to the submission author
            when comments are made to the submission (default: True).
        :param nsfw: Whether or not the submission should be marked NSFW (default:
            False).
        :param spoiler: Whether or not the submission should be marked as a spoiler
            (default: False).
        :param timeout: Specifies a particular timeout, in seconds. Use to avoid
            "Websocket error" exceptions (default: 10).
        :param without_websockets: Set to ``True`` to disable use of WebSockets (see
            note below for an explanation). If ``True``, this method doesn't return
            anything. (default: ``False``).
        :param discussion_type: Set to ``CHAT`` to enable live discussion instead of
            traditional comments (default: None).

        :returns: A :class:`.Submission` object for the newly created submission, unless
            ``without_websockets`` is ``True``.

        :raises: :class:`.ClientException` if ``image_path`` refers to a file that is
            not an image.

        .. note::

            Reddit's API uses WebSockets to respond with the link of the newly created
            post. If this fails, the method will raise :class:`.WebSocketException`.
            Occasionally, the Reddit post will still be created. More often, there is an
            error with the image file. If you frequently get exceptions but successfully
            created posts, try setting the ``timeout`` parameter to a value above 10.

            To disable the use of WebSockets, set ``without_websockets=True``. This will
            make the method return ``None``, though the post will still be created. You
            may wish to do this if you are running your program in a restricted network
            environment, or using a proxy that doesn't support WebSockets connections.

        For example, to submit an image to ``r/reddit_api_test`` do:

        .. code-block:: python

            title = "My favorite picture"
            image = "/path/to/image.png"
            subreddit = await reddit.subreddit("reddit_api_test")
            await subreddit.submit_image(title, image)

        .. seealso::

            - :meth:`.submit` to submit url posts and selftexts
            - :meth:`.submit_video`. to submit videos and videogifs
            - :meth:`.submit_gallery`. to submit more than one image in the same post

        """
        data = {
            "sr": str(self),
            "resubmit": bool(resubmit),
            "sendreplies": bool(send_replies),
            "title": title,
            "nsfw": bool(nsfw),
            "spoiler": bool(spoiler),
            "validate_on_submit": self._reddit.validate_on_submit,
        }
        for key, value in (
            ("flair_id", flair_id),
            ("flair_text", flair_text),
            ("collection_id", collection_id),
            ("discussion_type", discussion_type),
        ):
            if value is not None:
                data[key] = value

        image_url, websocket_url = await self._upload_media(
            image_path, expected_mime_prefix="image"
        )
        data.update(kind="image", url=image_url)
        if without_websockets:
            websocket_url = None
        return await self._submit_media(
            data,
            timeout,
            websocket_url=websocket_url,
        )

    async def submit_poll(
        self,
        title: str,
        selftext: str,
        options: List[str],
        duration: int,
        flair_id: Optional[str] = None,
        flair_text: Optional[str] = None,
        resubmit: bool = True,
        send_replies: bool = True,
        nsfw: bool = False,
        spoiler: bool = False,
        collection_id: Optional[str] = None,
        discussion_type: Optional[str] = None,
    ):
        """Add a poll submission to the subreddit.

        :param title: The title of the submission.
        :param selftext: The Markdown formatted content for the submission. Use an empty
            string, ``""``, to make a submission with no text contents.
        :param options: A ``list`` of two to six poll options as ``str``.
        :param duration: The number of days the poll should accept votes, as an ``int``.
            Valid values are between ``1`` and ``7``, inclusive.
        :param collection_id: The UUID of a :class:`.Collection` to add the
            newly-submitted post to.
        :param flair_id: The flair template to select (default: None).
        :param flair_text: If the template's ``flair_text_editable`` value is True, this
            value will set a custom text (default: None). ``flair_id`` is required when
            ``flair_text`` is provided.
        :param resubmit: When False, an error will occur if the URL has already been
            submitted (default: True).
        :param send_replies: When True, messages will be sent to the submission author
            when comments are made to the submission (default: True).
        :param nsfw: Whether or not the submission should be marked NSFW (default:
            False).
        :param spoiler: Whether or not the submission should be marked as a spoiler
            (default: False).
        :param discussion_type: Set to ``CHAT`` to enable live discussion instead of
            traditional comments (default: None).

        :returns: A :class:`~.Submission` object for the newly created submission.

        For example, to submit a poll to ``r/reddit_api_test`` do:

        .. code-block:: python

            title = "Do you like Async PRAW?"
            subreddit = await reddit.subreddit("reddit_api_test")
            await subreddit.submit_poll(title, selftext="", options=["Yes", "No"], duration=3)

        """
        data = {
            "sr": str(self),
            "text": selftext,
            "options": options,
            "duration": duration,
            "resubmit": bool(resubmit),
            "sendreplies": bool(send_replies),
            "title": title,
            "nsfw": bool(nsfw),
            "spoiler": bool(spoiler),
            "validate_on_submit": self._reddit.validate_on_submit,
        }
        for key, value in (
            ("flair_id", flair_id),
            ("flair_text", flair_text),
            ("collection_id", collection_id),
            ("discussion_type", discussion_type),
        ):
            if value is not None:
                data[key] = value

        return await self._reddit.post(API_PATH["submit_poll_post"], json=data)

    async def submit_video(
        self,
        title: str,
        video_path: str,
        videogif: bool = False,
        thumbnail_path: Optional[str] = None,
        flair_id: Optional[str] = None,
        flair_text: Optional[str] = None,
        resubmit: bool = True,
        send_replies: bool = True,
        nsfw: bool = False,
        spoiler: bool = False,
        timeout: int = 10,
        collection_id: Optional[str] = None,
        without_websockets: bool = False,
        discussion_type: Optional[str] = None,
    ):
        """Add a video or videogif submission to the subreddit.

        :param title: The title of the submission.
        :param video_path: The path to a video, to upload and post.
        :param videogif: A ``bool`` value. If ``True``, the video is uploaded as a
            videogif, which is essentially a silent video (default: ``False``).
        :param thumbnail_path: (Optional) The path to an image, to be uploaded and used
            as the thumbnail for this video. If not provided, the PRAW logo will be used
            as the thumbnail.
        :param collection_id: The UUID of a :class:`.Collection` to add the
            newly-submitted post to.
        :param flair_id: The flair template to select (default: ``None``).
        :param flair_text: If the template's ``flair_text_editable`` value is True, this
            value will set a custom text (default: ``None``). ``flair_id`` is required
            when ``flair_text`` is provided.
        :param resubmit: When False, an error will occur if the URL has already been
            submitted (default: ``True``).
        :param send_replies: When True, messages will be sent to the submission author
            when comments are made to the submission (default: ``True``).
        :param nsfw: Whether or not the submission should be marked NSFW (default:
            False).
        :param spoiler: Whether or not the submission should be marked as a spoiler
            (default: False).
        :param timeout: Specifies a particular timeout, in seconds. Use to avoid
            "Websocket error" exceptions (default: 10).
        :param without_websockets: Set to ``True`` to disable use of WebSockets (see
            note below for an explanation). If ``True``, this method doesn't return
            anything. (default: ``False``).
        :param discussion_type: Set to ``CHAT`` to enable live discussion instead of
            traditional comments (default: None).

        :returns: A :class:`.Submission` object for the newly created submission, unless
            ``without_websockets`` is ``True``.

        :raises: :class:`.ClientException` if ``video_path`` refers to a file that is
            not a video.

        .. note::

            Reddit's API uses WebSockets to respond with the link of the newly created
            post. If this fails, the method will raise :class:`.WebSocketException`.
            Occasionally, the Reddit post will still be created. More often, there is an
            error with the image file. If you frequently get exceptions but successfully
            created posts, try setting the ``timeout`` parameter to a value above 10.

            To disable the use of WebSockets, set ``without_websockets=True``. This will
            make the method return ``None``, though the post will still be created. You
            may wish to do this if you are running your program in a restricted network
            environment, or using a proxy that doesn't support WebSockets connections.

        For example, to submit a video to ``r/reddit_api_test`` do:

        .. code-block:: python

            title = "My favorite movie"
            video = "/path/to/video.mp4"
            subreddit = await reddit.subreddit("reddit_api_test")
            await subreddit.submit_video(title, video)

        .. seealso::

            - :meth:`.submit` to submit url posts and selftexts
            - :meth:`.submit_image` to submit images
            - :meth:`.submit_gallery`. to submit more than one image in the same post

        """
        data = {
            "sr": str(self),
            "resubmit": bool(resubmit),
            "sendreplies": bool(send_replies),
            "title": title,
            "nsfw": bool(nsfw),
            "spoiler": bool(spoiler),
            "validate_on_submit": self._reddit.validate_on_submit,
        }
        for key, value in (
            ("flair_id", flair_id),
            ("flair_text", flair_text),
            ("collection_id", collection_id),
            ("discussion_type", discussion_type),
        ):
            if value is not None:
                data[key] = value

        video_url, websocket_url = await self._upload_media(
            video_path, expected_mime_prefix="video"
        )
        video_poster_url, _ = await self._upload_media(thumbnail_path)
        data.update(
            kind="videogif" if videogif else "video",
            url=video_url,
            # if thumbnail_path is None, it uploads the PRAW logo
            video_poster_url=video_poster_url,
        )
        if without_websockets:
            websocket_url = None
        return await self._submit_media(
            data,
            timeout,
            websocket_url=websocket_url,
        )

    async def subscribe(
        self, other_subreddits: Optional[List["asyncpraw.models.Subreddit"]] = None
    ):
        """Subscribe to the subreddit.

        :param other_subreddits: When provided, also subscribe to the provided list of
            subreddits.

        For example, to subscribe to ``r/test``:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            await subreddit.subscribe()

        """
        data = {
            "action": "sub",
            "skip_inital_defaults": True,
            "sr_name": self._subreddit_list(self, other_subreddits),
        }
        await self._reddit.post(API_PATH["subscribe"], data=data)

    async def traffic(self) -> Dict[str, List[List[int]]]:
        """Return a dictionary of the subreddit's traffic statistics.

        :raises: ``asyncprawcore.NotFound`` when the traffic stats aren't available to
            the authenticated user, that is, they are not public and the authenticated
            user is not a moderator of the subreddit.

        The traffic method returns a dict with three keys. The keys are ``day``,
        ``hour`` and ``month``. Each key contains a list of lists with 3 or 4 values.
        The first value is a timestamp indicating the start of the category (start of
        the day for the ``day`` key, start of the hour for the ``hour`` key, etc.). The
        second, third, and fourth values indicate the unique pageviews, total pageviews,
        and subscribers, respectively.

        .. note::

            The ``hour`` key does not contain subscribers, and therefore each sub-list
            contains three values.

        For example, to get the traffic stats for ``r/test``:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            stats = await subreddit.traffic()

        """
        return await self._reddit.get(API_PATH["about_traffic"].format(subreddit=self))

    async def unsubscribe(
        self, other_subreddits: Optional[List["asyncpraw.models.Subreddit"]] = None
    ):
        """Unsubscribe from the subreddit.

        :param other_subreddits: When provided, also unsubscribe from the provided list
            of subreddits.

        To unsubscribe from ``r/test``:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            await subreddit.unsubscribe()

        """
        data = {
            "action": "unsub",
            "sr_name": self._subreddit_list(self, other_subreddits),
        }
        await self._reddit.post(API_PATH["subscribe"], data=data)


WidgetEncoder._subreddit_class = Subreddit


class SubredditFilters:
    """Provide functions to interact with the special Subreddit's filters.

    Members of this class should be utilized via ``Subreddit.filters``. For example, to
    add a filter, run:

    .. code-block:: python

        subreddit = await reddit.subreddit("all")
        await subreddit.filters.add("subreddit_name")

    """

    def __init__(self, subreddit: "asyncpraw.models.Subreddit"):
        """Create a SubredditFilters instance.

        :param subreddit: The special subreddit whose filters to work with.

        As of this writing filters can only be used with the special subreddits ``all``
        and ``mod``.

        """
        self.subreddit = subreddit

    async def __aiter__(
        self,
    ) -> AsyncGenerator["asyncpraw.models.Subreddit", None]:
        """Iterate through the special subreddit's filters.

        This method should be invoked as:

        .. code-block:: python

            subreddit = await reddit.subreddit("NAME")
            async for subreddit in subreddit.filters:
                ...

        """
        user = await self.subreddit._reddit.user.me()
        url = API_PATH["subreddit_filter_list"].format(
            special=self.subreddit, user=user
        )
        params = {"unique": self.subreddit._reddit._next_unique}
        response_data = await self.subreddit._reddit.get(url, params=params)
        for subreddit in response_data.subreddits:
            yield subreddit

    async def add(self, subreddit: Union["asyncpraw.models.Subreddit", str]):
        """Add ``subreddit`` to the list of filtered subreddits.

        :param subreddit: The subreddit to add to the filter list.

        Items from subreddits added to the filtered list will no longer be included when
        obtaining listings for ``r/all``.

        Alternatively, you can filter a subreddit temporarily from a special listing in
        a manner like so:

        .. code-block:: python

            await reddit.subreddit("all-redditdev-learnpython")

        :raises: ``asyncprawcore.NotFound`` when calling on a non-special subreddit.

        """
        user = await self.subreddit._reddit.user.me()
        url = API_PATH["subreddit_filter"].format(
            special=self.subreddit,
            user=user,
            subreddit=subreddit,
        )
        await self.subreddit._reddit.put(
            url, data={"model": dumps({"name": str(subreddit)})}
        )

    async def remove(self, subreddit: Union["asyncpraw.models.Subreddit", str]):
        """Remove ``subreddit`` from the list of filtered subreddits.

        :param subreddit: The subreddit to remove from the filter list.

        :raises: ``asyncprawcore.NotFound`` when calling on a non-special subreddit.

        """
        user = await self.subreddit._reddit.user.me()
        url = API_PATH["subreddit_filter"].format(
            special=self.subreddit,
            user=user,
            subreddit=subreddit,
        )
        await self.subreddit._reddit.delete(url)


class SubredditFlair:
    """Provide a set of functions to interact with a Subreddit's flair."""

    @cachedproperty
    def link_templates(
        self,
    ) -> "asyncpraw.models.reddit.subreddit.SubredditLinkFlairTemplates":
        """Provide an instance of :class:`.SubredditLinkFlairTemplates`.

        Use this attribute for interacting with a subreddit's link flair templates. For
        example, to list all the link flair templates for a subreddit which you have the
        ``flair`` moderator permission on try:

        .. code-block:: python

            subreddit = await reddit.subreddit("NAME")
            async for template in subreddit.flair.link_templates:
                print(template)

        """
        return SubredditLinkFlairTemplates(self.subreddit)

    @cachedproperty
    def templates(
        self,
    ) -> "asyncpraw.models.reddit.subreddit.SubredditRedditorFlairTemplates":
        """Provide an instance of :class:`.SubredditRedditorFlairTemplates`.

        Use this attribute for interacting with a subreddit's flair templates. For
        example, to list all the flair templates for a subreddit which you have the
        ``flair`` moderator permission on try:

        .. code-block:: python

            subreddit = await reddit.subreddit("NAME")
            async for template in subreddit.flair.templates:
                print(template)

        """
        return SubredditRedditorFlairTemplates(self.subreddit)

    def __call__(
        self,
        redditor: Optional[Union["asyncpraw.models.Redditor", str]] = None,
        **generator_kwargs: Any,
    ) -> Iterator["asyncpraw.models.Redditor"]:
        """Return a :class:`.ListingGenerator` for Redditors and their flairs.

        :param redditor: When provided, yield at most a single :class:`~.Redditor`
            instance (default: None).

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        Usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("NAME")
            async for flair in subreddit.flair(limit=None):
                print(flair)

        """
        Subreddit._safely_add_arguments(generator_kwargs, "params", name=str(redditor))
        generator_kwargs.setdefault("limit", None)
        url = API_PATH["flairlist"].format(subreddit=self.subreddit)
        return ListingGenerator(self.subreddit._reddit, url, **generator_kwargs)

    def __init__(self, subreddit: "asyncpraw.models.Subreddit"):
        """Create a SubredditFlair instance.

        :param subreddit: The subreddit whose flair to work with.

        """
        self.subreddit = subreddit

    async def configure(
        self,
        position: str = "right",
        self_assign: bool = False,
        link_position: str = "left",
        link_self_assign: bool = False,
        **settings: Any,
    ):
        """Update the subreddit's flair configuration.

        :param position: One of left, right, or False to disable (default: right).
        :param self_assign: (boolean) Permit self assignment of user flair (default:
            False).
        :param link_position: One of left, right, or False to disable (default: left).
        :param link_self_assign: (boolean) Permit self assignment of link flair
            (default: False).

        Additional keyword arguments can be provided to handle new settings as Reddit
        introduces them.

        """
        data = {
            "flair_enabled": bool(position),
            "flair_position": position or "right",
            "flair_self_assign_enabled": self_assign,
            "link_flair_position": link_position or "",
            "link_flair_self_assign_enabled": link_self_assign,
        }
        data.update(settings)
        url = API_PATH["flairconfig"].format(subreddit=self.subreddit)
        await self.subreddit._reddit.post(url, data=data)

    async def delete(self, redditor: Union["asyncpraw.models.Redditor", str]):
        """Delete flair for a Redditor.

        :param redditor: A redditor name (e.g., ``"spez"``) or :class:`~.Redditor`
            instance.

        .. seealso::

            :meth:`~asyncpraw.models.reddit.subreddit.SubredditFlair.update` to delete
            the flair of many Redditors at once.

        """
        url = API_PATH["deleteflair"].format(subreddit=self.subreddit)
        await self.subreddit._reddit.post(url, data={"name": str(redditor)})

    async def delete_all(self) -> List[Dict[str, Union[str, bool, Dict[str, str]]]]:
        """Delete all Redditor flair in the Subreddit.

        :returns: List of dictionaries indicating the success or failure of each delete.

        """
        all_flairs = [x["user"] async for x in self()]
        return await self.update(all_flairs)

    async def set(
        self,
        redditor: Union["asyncpraw.models.Redditor", str],
        text: str = "",
        css_class: str = "",
        flair_template_id: Optional[str] = None,
    ):
        """Set flair for a Redditor.

        :param redditor: (Required) A redditor name (e.g., ``"spez"``) or
            :class:`~.Redditor` instance.
        :param text: The flair text to associate with the Redditor or Submission
            (default: "").
        :param css_class: The css class to associate with the flair html (default: "").
            Use either this or ``flair_template_id``.
        :param flair_template_id: The ID of the flair template to be used (default:
            ``None``). Use either this or ``css_class``.

        This method can only be used by an authenticated user who is a moderator of the
        associated Subreddit.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("redditdev")
            await subreddit.flair.set("bboe", "PRAW author", css_class="mods")
            template = "6bd28436-1aa7-11e9-9902-0e05ab0fad46"
            subreddit = await reddit.subreddit("redditdev")
            await subreddit.flair.set("spez", "Reddit CEO", flair_template_id=template)

        """
        if css_class and flair_template_id is not None:
            raise TypeError(
                "Parameter `css_class` cannot be used in conjunction with"
                " `flair_template_id`."
            )
        data = {"name": str(redditor), "text": text}
        if flair_template_id is not None:
            data["flair_template_id"] = flair_template_id
            url = API_PATH["select_flair"].format(subreddit=self.subreddit)
        else:
            data["css_class"] = css_class
            url = API_PATH["flair"].format(subreddit=self.subreddit)
        await self.subreddit._reddit.post(url, data=data)

    async def update(
        self,
        flair_list: Iterator[
            Union[
                str,
                "asyncpraw.models.Redditor",
                Dict[str, Union[str, "asyncpraw.models.Redditor"]],
            ]
        ],
        text: str = "",
        css_class: str = "",
    ) -> List[Dict[str, Union[str, bool, Dict[str, str]]]]:
        """Set or clear the flair for many Redditors at once.

        :param flair_list: Each item in this list should be either: the name of a
            Redditor, an instance of :class:`.Redditor`, or a dictionary mapping keys
            ``user``, ``flair_text``, and ``flair_css_class`` to their respective
            values. The ``user`` key should map to a Redditor, as described above. When
            a dictionary isn't provided, or the dictionary is missing one of
            ``flair_text``, or ``flair_css_class`` attributes the default values will
            come from the the following arguments.
        :param text: The flair text to use when not explicitly provided in
            ``flair_list`` (default: "").
        :param css_class: The css class to use when not explicitly provided in
            ``flair_list`` (default: "").

        :returns: List of dictionaries indicating the success or failure of each update.

        For example, to clear the flair text, and set the ``praw`` flair css class on a
        few users try:

        .. code-block:: python

            await subreddit.flair.update(["bboe", "spez", "spladug"], css_class="praw")

        """
        templines = StringIO()
        for item in flair_list:
            if isinstance(item, dict):
                writer(templines).writerow(
                    [
                        str(item["user"]),
                        item.get("flair_text", text),
                        item.get("flair_css_class", css_class),
                    ]
                )
            else:
                writer(templines).writerow([str(item), text, css_class])

        lines = templines.getvalue().splitlines()
        templines.close()
        response = []
        url = API_PATH["flaircsv"].format(subreddit=self.subreddit)
        while lines:
            data = {"flair_csv": "\n".join(lines[:100])}
            response.extend(await self.subreddit._reddit.post(url, data=data))
            lines = lines[100:]
        return response


class SubredditFlairTemplates:
    """Provide functions to interact with a Subreddit's flair templates."""

    @staticmethod
    def flair_type(is_link: bool) -> str:
        """Return LINK_FLAIR or USER_FLAIR depending on ``is_link`` value."""
        return "LINK_FLAIR" if is_link else "USER_FLAIR"

    def __init__(self, subreddit: "asyncpraw.models.Subreddit"):
        """Create a SubredditFlairTemplate instance.

        :param subreddit: The subreddit whose flair templates to work with.

        .. note::

            This class should not be initialized directly. Instead obtain an instance
            via:

            .. code-block:: python

                subreddit = await reddit.subreddit("subreddit_name")
                subreddit.flair.templates

            or via

            .. code-block:: python

                subreddit = await reddit.subreddit("subreddit_name")
                subreddit.flair.link_templates

        """
        self.subreddit = subreddit

    async def __aiter__(self):
        """Abstract method to return flair templates."""
        raise NotImplementedError()

    async def _add(
        self,
        text: str,
        css_class: str = "",
        text_editable: bool = False,
        is_link: Optional[bool] = None,
        background_color: Optional[str] = None,
        text_color: Optional[str] = None,
        mod_only: Optional[bool] = None,
        allowable_content: Optional[str] = None,
        max_emojis: Optional[int] = None,
    ):
        url = API_PATH["flairtemplate_v2"].format(subreddit=self.subreddit)
        data = {
            "allowable_content": allowable_content,
            "background_color": background_color,
            "css_class": css_class,
            "flair_type": self.flair_type(is_link),
            "max_emojis": max_emojis,
            "mod_only": bool(mod_only),
            "text": text,
            "text_color": text_color,
            "text_editable": bool(text_editable),
        }
        await self.subreddit._reddit.post(url, data=data)

    async def _clear(self, is_link: Optional[bool] = None):
        url = API_PATH["flairtemplateclear"].format(subreddit=self.subreddit)
        await self.subreddit._reddit.post(
            url, data={"flair_type": self.flair_type(is_link)}
        )

    async def delete(self, template_id: str):
        """Remove a flair template provided by ``template_id``.

        For example, to delete the first Redditor flair template listed, try:

        .. code-block:: python

            async for template_info in subreddit.flair.templates:
                await subreddit.flair.templates.delete(template_info["id"])
                break

        """
        url = API_PATH["flairtemplatedelete"].format(subreddit=self.subreddit)
        await self.subreddit._reddit.post(url, data={"flair_template_id": template_id})

    async def update(
        self,
        template_id: str,
        text: Optional[str] = None,
        css_class: Optional[str] = None,
        text_editable: Optional[bool] = None,
        background_color: Optional[str] = None,
        text_color: Optional[str] = None,
        mod_only: Optional[bool] = None,
        allowable_content: Optional[str] = None,
        max_emojis: Optional[int] = None,
        fetch: bool = True,
    ):
        """Update the flair template provided by ``template_id``.

        :param template_id: The flair template to update. If not valid then an exception
            will be thrown.
        :param text: The flair template's new text (required).
        :param css_class: The flair template's new css_class (default: "").
        :param text_editable: (boolean) Indicate if the flair text can be modified for
            each Redditor that sets it (default: False).
        :param background_color: The flair template's new background color, as a hex
            color.
        :param text_color: The flair template's new text color, either ``"light"`` or
            ``"dark"``.
        :param mod_only: (boolean) Indicate if the flair can only be used by moderators.
        :param allowable_content: If specified, most be one of ``"all"``, ``"emoji"``,
            or ``"text"`` to restrict content to that type. If set to ``"emoji"`` then
            the ``"text"`` param must be a valid emoji string, for example,
            ``":snoo:"``.
        :param max_emojis: (int) Maximum emojis in the flair (Reddit defaults this value
            to 10).
        :param fetch: Whether or not Async PRAW will fetch existing information on the
            existing flair before updating (Default: True).

        .. warning::

            If parameter ``fetch`` is set to ``False``, all parameters not provided will
            be reset to default (``None`` or ``False``) values.

        For example, to make a user flair template text_editable, try:

        .. code-block:: python

            async for template_info in subreddit.flair.templates:
                await subreddit.flair.templates.update(
                    template_info["id"], template_info["flair_text"], text_editable=True
                )
                break

        """
        url = API_PATH["flairtemplate_v2"].format(subreddit=self.subreddit)
        data = {
            "allowable_content": allowable_content,
            "background_color": background_color,
            "css_class": css_class,
            "flair_template_id": template_id,
            "max_emojis": max_emojis,
            "mod_only": mod_only,
            "text": text,
            "text_color": text_color,
            "text_editable": text_editable,
        }
        if fetch:
            _existing_data = [
                template async for template in self if template["id"] == template_id
            ]
            if len(_existing_data) != 1:
                raise InvalidFlairTemplateID(template_id)
            else:
                existing_data = _existing_data[0]
                for key, value in existing_data.items():
                    if data.get(key) is None:
                        data[key] = value
        await self.subreddit._reddit.post(url, data=data)


class SubredditRedditorFlairTemplates(SubredditFlairTemplates):
    """Provide functions to interact with Redditor flair templates."""

    async def __aiter__(
        self,
    ) -> AsyncGenerator[Dict[str, Union[str, int, bool, List[Dict[str, str]]]], None]:
        """Iterate through the user flair templates.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("NAME")
            async for template in subreddit.flair.templates:
                print(template)

        """
        url = API_PATH["user_flair"].format(subreddit=self.subreddit)
        params = {"unique": self.subreddit._reddit._next_unique}
        results = await self.subreddit._reddit.get(url, params=params)
        for template in results:
            yield template

    async def add(
        self,
        text: str,
        css_class: str = "",
        text_editable: bool = False,
        background_color: Optional[str] = None,
        text_color: Optional[str] = None,
        mod_only: Optional[bool] = None,
        allowable_content: Optional[str] = None,
        max_emojis: Optional[int] = None,
    ):
        """Add a Redditor flair template to the associated subreddit.

        :param text: The flair template's text (required).
        :param css_class: The flair template's css_class (default: "").
        :param text_editable: (boolean) Indicate if the flair text can be modified for
            each Redditor that sets it (default: False).
        :param background_color: The flair template's new background color, as a hex
            color.
        :param text_color: The flair template's new text color, either ``"light"`` or
            ``"dark"``.
        :param mod_only: (boolean) Indicate if the flair can only be used by moderators.
        :param allowable_content: If specified, most be one of ``"all"``, ``"emoji"``,
            or ``"text"`` to restrict content to that type. If set to ``"emoji"`` then
            the ``"text"`` param must be a valid emoji string, for example,
            ``":snoo:"``.
        :param max_emojis: (int) Maximum emojis in the flair (Reddit defaults this value
            to 10).

        For example, to add an editable Redditor flair try:

        .. code-block:: python

            subreddit = await reddit.subreddit("NAME")
            await subreddit.flair.templates.add(css_class="praw", text_editable=True)

        """
        await self._add(
            text,
            css_class=css_class,
            text_editable=text_editable,
            is_link=False,
            background_color=background_color,
            text_color=text_color,
            mod_only=mod_only,
            allowable_content=allowable_content,
            max_emojis=max_emojis,
        )

    async def clear(self):
        """Remove all Redditor flair templates from the subreddit.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("NAME")
            await subreddit.flair.templates.clear()

        """
        await self._clear(is_link=False)


class SubredditLinkFlairTemplates(SubredditFlairTemplates):
    """Provide functions to interact with link flair templates."""

    async def __aiter__(
        self,
    ) -> AsyncGenerator[Dict[str, Union[str, int, bool, List[Dict[str, str]]]], None]:
        """Iterate through the link flair templates.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("NAME")
            async for template in subreddit.flair.link_templates:
                print(template)

        """
        url = API_PATH["link_flair"].format(subreddit=self.subreddit)
        results = await self.subreddit._reddit.get(url)
        for template in results:
            yield template

    async def add(
        self,
        text: str,
        css_class: str = "",
        text_editable: bool = False,
        background_color: Optional[str] = None,
        text_color: Optional[str] = None,
        mod_only: Optional[bool] = None,
        allowable_content: Optional[str] = None,
        max_emojis: Optional[int] = None,
    ):
        """Add a link flair template to the associated subreddit.

        :param text: The flair template's text (required).
        :param css_class: The flair template's css_class (default: "").
        :param text_editable: (boolean) Indicate if the flair text can be modified for
            each Redditor that sets it (default: False).
        :param background_color: The flair template's new background color, as a hex
            color.
        :param text_color: The flair template's new text color, either ``"light"`` or
            ``"dark"``.
        :param mod_only: (boolean) Indicate if the flair can only be used by moderators.
        :param allowable_content: If specified, most be one of ``"all"``, ``"emoji"``,
            or ``"text"`` to restrict content to that type. If set to ``"emoji"`` then
            the ``"text"`` param must be a valid emoji string, for example,
            ``":snoo:"``.
        :param max_emojis: (int) Maximum emojis in the flair (Reddit defaults this value
            to 10).

        For example, to add an editable link flair try:

        .. code-block:: python

            subreddit = await reddit.subreddit("NAME")
            await subreddit.flair.link_templates.add(css_class="praw", text_editable=True)

        """
        await self._add(
            text,
            css_class=css_class,
            text_editable=text_editable,
            is_link=True,
            background_color=background_color,
            text_color=text_color,
            mod_only=mod_only,
            allowable_content=allowable_content,
            max_emojis=max_emojis,
        )

    async def clear(self):
        """Remove all link flair templates from the subreddit.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("NAME")
            await subreddit.flair.link_templates.clear()

        """
        await self._clear(is_link=True)


class SubredditModeration:
    """Provides a set of moderation functions to a Subreddit.

    For example, to accept a moderation invite from subreddit ``r/test``:

    .. code-block:: python

        subreddit = await reddit.subreddit("test")
        await subreddit.mod.accept_invite()

    """

    @staticmethod
    def _handle_only(only: Optional[str], generator_kwargs: Dict[str, Any]):
        if only is not None:
            if only == "submissions":
                only = "links"
            RedditBase._safely_add_arguments(generator_kwargs, "params", only=only)

    def __init__(self, subreddit: "asyncpraw.models.Subreddit"):
        """Create a SubredditModeration instance.

        :param subreddit: The subreddit to moderate.

        """
        self.subreddit = subreddit
        self._stream = None

    async def accept_invite(self):
        """Accept an invitation as a moderator of the community."""
        url = API_PATH["accept_mod_invite"].format(subreddit=self.subreddit)
        await self.subreddit._reddit.post(url)

    def edited(
        self, only: Optional[str] = None, **generator_kwargs: Any
    ) -> Iterator[Union["asyncpraw.models.Comment", "asyncpraw.models.Submission"]]:
        """Return a :class:`.ListingGenerator` for edited comments and submissions.

        :param only: If specified, one of ``"comments"``, or ``"submissions"`` to yield
            only results of that type.

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        To print all items in the edited queue try:

        .. code-block:: python

            subreddit = await reddit.subreddit("mod")
            async for item in subreddit.mod.edited(limit=None):
                print(item)

        """
        self._handle_only(only, generator_kwargs)
        return ListingGenerator(
            self.subreddit._reddit,
            API_PATH["about_edited"].format(subreddit=self.subreddit),
            **generator_kwargs,
        )

    def inbox(
        self, **generator_kwargs: Any
    ) -> Iterator["asyncpraw.models.SubredditMessage"]:
        """Return a :class:`.ListingGenerator` for moderator messages.

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        .. seealso::

            :meth:`~.unread` for unread moderator messages.

        To print the last 5 moderator mail messages and their replies, try:

        .. code-block:: python

            subreddit = await reddit.subreddit("mod")
            async for message in subreddit.mod.inbox(limit=5):
                print("From: {}, Body: {}".format(message.author, message.body))
                for reply in message.replies:
                    print("From: {}, Body: {}".format(reply.author, reply.body))

        """
        return ListingGenerator(
            self.subreddit._reddit,
            API_PATH["moderator_messages"].format(subreddit=self.subreddit),
            **generator_kwargs,
        )

    def log(
        self,
        action: Optional[str] = None,
        mod: Optional[Union["asyncpraw.models.Redditor", str]] = None,
        **generator_kwargs: Any,
    ) -> Iterator["asyncpraw.models.ModAction"]:
        """Return a :class:`.ListingGenerator` for moderator log entries.

        :param action: If given, only return log entries for the specified action.
        :param mod: If given, only return log entries for actions made by the passed in
            Redditor.

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        To print the moderator and subreddit of the last 5 modlog entries try:

        .. code-block:: python

            subreddit = await reddit.subreddit("mod")
            async for log in subreddit.mod.log(limit=5):
                print("Mod: {}, Subreddit: {}".format(log.mod, log.subreddit))

        """
        params = {"mod": str(mod) if mod else mod, "type": action}
        Subreddit._safely_add_arguments(generator_kwargs, "params", **params)
        return ListingGenerator(
            self.subreddit._reddit,
            API_PATH["about_log"].format(subreddit=self.subreddit),
            **generator_kwargs,
        )

    def modqueue(
        self, only: Optional[str] = None, **generator_kwargs: Any
    ) -> Iterator[Union["asyncpraw.models.Submission", "asyncpraw.models.Comment"]]:
        """Return a :class:`.ListingGenerator` for modqueue items.

        :param only: If specified, one of ``"comments"``, or ``"submissions"`` to yield
            only results of that type.

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        To print all modqueue items try:

        .. code-block:: python

            subreddit = await reddit.subreddit("mod")
            async for item in subreddit.mod.modqueue(limit=None):
                print(item)

        """
        self._handle_only(only, generator_kwargs)
        return ListingGenerator(
            self.subreddit._reddit,
            API_PATH["about_modqueue"].format(subreddit=self.subreddit),
            **generator_kwargs,
        )

    @cachedproperty
    def stream(self) -> "asyncpraw.models.reddit.subreddit.SubredditModerationStream":
        """Provide an instance of :class:`.SubredditModerationStream`.

        Streams can be used to indefinitely retrieve Moderator only items from
        :class:`.SubredditModeration` made to moderated subreddits, like:

        .. code-block:: python

            subreddit = await reddit.subreddit("mod")
            async for log in subreddit.mod.stream.log():
                print("Mod: {}, Subreddit: {}".format(log.mod, log.subreddit))

        """
        return SubredditModerationStream(self.subreddit)

    @cachedproperty
    def removal_reasons(self) -> SubredditRemovalReasons:
        """Provide an instance of :class:`.SubredditRemovalReasons`.

        Use this attribute for interacting with a subreddit's removal reasons. For
        example, to list all the removal reasons for a subreddit which you have the
        ``posts`` moderator permission on, try:

        .. code-block:: python

            subreddit = await reddit.subreddit("NAME")
            async for removal_reason in subreddit.mod.removal_reasons:
                print(removal_reason)

        A single removal reason can be retrieved via:

        .. code-block:: python

            subreddit = await reddit.subreddit("NAME")
            await subreddit.mod.removal_reasons.get_reason("reason_id")

        .. note::

            Attempting to access attributes of an nonexistent removal reason will result
            in a :class:`.ClientException`.

        """
        return SubredditRemovalReasons(self.subreddit)

    def reports(
        self, only: Optional[str] = None, **generator_kwargs: Any
    ) -> Iterator[Union["asyncpraw.models.Submission", "asyncpraw.models.Comment"]]:
        """Return a :class:`.ListingGenerator` for reported comments and submissions.

        :param only: If specified, one of ``"comments"``, or ``"submissions"`` to yield
            only results of that type.

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        To print the user and mod report reasons in the report queue try:

        .. code-block:: python

            subreddit = await reddit.subreddit("mod")
            async for reported_item in subreddit.mod.reports():
                print("User Reports: {}".format(reported_item.user_reports))
                print("Mod Reports: {}".format(reported_item.mod_reports))

        """
        self._handle_only(only, generator_kwargs)
        return ListingGenerator(
            self.subreddit._reddit,
            API_PATH["about_reports"].format(subreddit=self.subreddit),
            **generator_kwargs,
        )

    async def settings(self) -> Dict[str, Union[str, int, bool]]:
        """Return a dictionary of the subreddit's current settings."""
        url = API_PATH["subreddit_settings"].format(subreddit=self.subreddit)
        response = await self.subreddit._reddit.get(url)
        return response["data"]

    def spam(
        self, only: Optional[str] = None, **generator_kwargs: Any
    ) -> Iterator[Union["asyncpraw.models.Submission", "asyncpraw.models.Comment"]]:
        """Return a :class:`.ListingGenerator` for spam comments and submissions.

        :param only: If specified, one of ``"comments"``, or ``"submissions"`` to yield
            only results of that type.

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        To print the items in the spam queue try:

        .. code-block:: python

            subreddit = await reddit.subreddit("mod")
            async for item in subreddit.mod.spam():
                print(item)

        """
        self._handle_only(only, generator_kwargs)
        return ListingGenerator(
            self.subreddit._reddit,
            API_PATH["about_spam"].format(subreddit=self.subreddit),
            **generator_kwargs,
        )

    def unmoderated(
        self, **generator_kwargs: Any
    ) -> Iterator["asyncpraw.models.Submission"]:
        """Return a :class:`.ListingGenerator` for unmoderated submissions.

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        To print the items in the unmoderated queue try:

        .. code-block:: python

            subreddit = await reddit.subreddit("mod")
            async for item in subreddit.mod.unmoderated():
                print(item)

        """
        return ListingGenerator(
            self.subreddit._reddit,
            API_PATH["about_unmoderated"].format(subreddit=self.subreddit),
            **generator_kwargs,
        )

    def unread(
        self, **generator_kwargs: Any
    ) -> Iterator["asyncpraw.models.SubredditMessage"]:
        """Return a :class:`.ListingGenerator` for unread moderator messages.

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        .. seealso::

            :meth:`inbox` for all messages.

        To print the mail in the unread modmail queue try:

        .. code-block:: python

            subreddit = await reddit.subreddit("mod")
            async for message in subreddit.mod.unread():
                print("From: {}, To: {}".format(message.author, message.dest))

        """
        return ListingGenerator(
            self.subreddit._reddit,
            API_PATH["moderator_unread"].format(subreddit=self.subreddit),
            **generator_kwargs,
        )

    async def update(
        self, **settings: Union[str, int, bool]
    ) -> Dict[str, Union[str, int, bool]]:
        """Update the subreddit's settings.

        See https://www.reddit.com/dev/api#POST_api_site_admin for the full list.

        :param all_original_content: Mandate all submissions to be original content
            only.
        :param allow_chat_post_creation: Allow users to create chat submissions.
        :param allow_images: Allow users to upload images using the native image
            hosting.
        :param allow_polls: Allow users to post polls to the subreddit.
        :param allow_post_crossposts: Allow users to crosspost submissions from other
            subreddits.
        :param  allow_videos: Allow users to upload videos using the native image
            hosting.
        :param collapse_deleted_comments: Collapse deleted and removed comments on
            comments pages by default.
        :param comment_score_hide_mins: The number of minutes to hide comment scores.
        :param content_options: The types of submissions users can make. One of ``any``,
            ``link``, ``self``.
        :param crowd_control_chat_level: Controls the crowd control level for chat
            rooms. Goes from 0-3.
        :param crowd_control_level: Controls the crowd control level for submissions.
            Goes from 0-3.
        :param crowd_control_mode: Enables/disables crowd control.
        :param default_set: Allow the subreddit to appear on ``r/all`` as well as the
            default and trending lists.
        :param disable_contributor_requests: Specifies whether redditors may send
            automated modmail messages requesting approval as a submitter.
        :param exclude_banned_modqueue: Exclude posts by site-wide banned users from
            modqueue/unmoderated.
        :param free_form_reports: Allow users to specify custom reasons in the report
            menu.
        :param header_hover_text: The text seen when hovering over the snoo.
        :param hide_ads: Don't show ads within this subreddit. Only applies to
            Premium-user only subreddits.
        :param key_color: A 6-digit rgb hex color (e.g. ``"#AABBCC"``), used as a
            thematic color for your subreddit on mobile.
        :param language: A valid IETF language tag (underscore separated).
        :param original_content_tag_enabled: Enables the use of the ``original content``
            label for submissions.
        :param over_18: Viewers must be over 18 years old (i.e. NSFW).
        :param public_description: Public description blurb. Appears in search results
            and on the landing page for private subreddits.
        :param restrict_commenting: Specifies whether approved users have the ability to
            comment.
        :param restrict_posting: Specifies whether approved users have the ability to
            submit posts.
        :param show_media: Show thumbnails on submissions.
        :param show_media_preview: Expand media previews on comments pages.
        :param spam_comments: Spam filter strength for comments. One of ``all``,
            ``low``, ``high``.
        :param spam_links: Spam filter strength for links. One of ``all``, ``low``,
            ``high``.
        :param spam_selfposts: Spam filter strength for selfposts. One of ``all``,
            ``low``, ``high``.
        :param spoilers_enabled: Enable marking posts as containing spoilers.
        :param submit_link_label: Custom label for submit link button (None for
            default).
        :param submit_text: Text to show on submission page.
        :param submit_text_label: Custom label for submit text post button (None for
            default).
        :param  subreddit_type: One of ``archived``, ``employees_only``, ``gold_only``,
            ``gold_restricted``, ``private``, ``public``, ``restricted``.
        :param suggested_comment_sort: All comment threads will use this sorting method
            by default. Leave None, or choose one of ``confidence``, ``controversial``,
            ``live``, ``new``, ``old``, ``qa``, ``random``, ``top``.
        :param title: The title of the subreddit.
        :param welcome_message_enabled: Enables the subreddit welcome message.
        :param welcome_message_text: The text to be used as a welcome message. A welcome
            message is sent to all new subscribers by a Reddit bot.
        :param wiki_edit_age: Account age, in days, required to edit and create wiki
            pages.
        :param wiki_edit_karma: "asyncpraw.models.Subreddit" karma required to edit and
            create wiki pages.
        :param wikimode: One of ``anyone``, ``disabled``, ``modonly``.

        .. note::

            Updating the subreddit sidebar on old reddit (``description``) is no longer
            supported using this method. You can update the sidebar by editing the
            ``"config/sidebar"`` wiki page. For example:

            .. code-block:: python

                subreddit = await reddit.subreddit("test")
                sidebar = await subreddit.wiki.get_page("config/sidebar")
                await sidebar.edit(content="new sidebar content")

        Additional keyword arguments can be provided to handle new settings as Reddit
        introduces them.

        Settings that are documented here and aren't explicitly set by you in a call to
        :meth:`.SubredditModeration.update` should retain their current value. If they
        do not, please file a bug.

        """
        if not self.subreddit._fetched:
            await self.subreddit._fetch()
        # These attributes come out using different names than they go in.
        remap = {
            "content_options": "link_type",
            "default_set": "allow_top",
            "header_hover_text": "header_title",
            "language": "lang",
            "subreddit_type": "type",
        }
        settings = {remap.get(key, key): value for key, value in settings.items()}
        settings["sr"] = self.subreddit.fullname
        return await self.subreddit._reddit.patch(
            API_PATH["update_settings"], json=settings
        )


class SubredditModerationStream:
    """Provides moderator streams."""

    def __init__(self, subreddit: "asyncpraw.models.Subreddit"):
        """Create a SubredditModerationStream instance.

        :param subreddit: The moderated subreddit associated with the streams.

        """
        self.subreddit = subreddit

    def edited(
        self, only: Optional[str] = None, **stream_options: Any
    ) -> AsyncGenerator[
        Union["asyncpraw.models.Comment", "asyncpraw.models.Submission"], None
    ]:
        """Yield edited comments and submissions as they become available.

        :param only: If specified, one of ``"comments"``, or ``"submissions"`` to yield
            only results of that type.

        Keyword arguments are passed to :func:`.stream_generator`.

        For example, to retrieve all new edited submissions/comments made to all
        moderated subreddits, try:

        .. code-block:: python

            subreddit = await reddit.subreddit("mod")
            async for item in subreddit.mod.stream.edited():
                print(item)

        """
        return stream_generator(self.subreddit.mod.edited, only=only, **stream_options)

    def log(
        self,
        action: Optional[str] = None,
        mod: Optional[Union[str, "asyncpraw.models.Redditor"]] = None,
        **stream_options: Any,
    ) -> AsyncGenerator["asyncpraw.models.ModAction", None]:
        """Yield moderator log entries as they become available.

        :param action: If given, only return log entries for the specified action.
        :param mod: If given, only return log entries for actions made by the passed in
            Redditor.

        For example, to retrieve all new mod actions made to all moderated subreddits,
        try:

        .. code-block:: python

            subreddit = await reddit.subreddit("mod")
            async for log in subreddit.mod.stream.log():
                print("Mod: {}, Subreddit: {}".format(log.mod, log.subreddit))

        """
        return stream_generator(
            self.subreddit.mod.log,
            action=action,
            mod=mod,
            attribute_name="id",
            **stream_options,
        )

    def modmail_conversations(
        self,
        other_subreddits: Optional[List["asyncpraw.models.Subreddit"]] = None,
        sort: Optional[str] = None,
        state: Optional[str] = None,
        **stream_options: Any,
    ) -> AsyncGenerator[ModmailConversation, None]:
        """Yield new-modmail conversations as they become available.

        :param other_subreddits: A list of :class:`.Subreddit` instances for which to
            fetch conversations (default: None).
        :param sort: Can be one of: mod, recent, unread, user (default: recent).
        :param state: Can be one of: all, appeals, archived, default, highlighted,
            inbox, inprogress, mod, new, notifications (default: all). "all" does not
            include mod or archived conversations. "inbox" does not include appeals
            conversations.

        Keyword arguments are passed to :func:`.stream_generator`.

        To print new mail in the unread modmail queue try:

        .. code-block:: python

            subreddit = await reddit.subreddit("all")
            async for message in subreddit.mod.stream.modmail_conversations():
                print("From: {}, To: {}".format(message.owner, message.participant))

        """  # noqa: E501
        if self.subreddit == "mod":
            self.subreddit = Subreddit(self.subreddit._reddit, "all")
        return stream_generator(
            self.subreddit.modmail.conversations,
            other_subreddits=other_subreddits,
            sort=sort,
            state=state,
            attribute_name="id",
            exclude_before=True,
            **stream_options,
        )

    def modqueue(
        self, only: Optional[str] = None, **stream_options: Any
    ) -> AsyncGenerator[
        Union["asyncpraw.models.Comment", "asyncpraw.models.Submission"], None
    ]:
        """Yield comments/submissions in the modqueue as they become available.

        :param only: If specified, one of ``"comments"``, or ``"submissions"`` to yield
            only results of that type.

        Keyword arguments are passed to :func:`.stream_generator`.

        To print all new modqueue items try:

        .. code-block:: python

            subreddit = await reddit.subreddit("mod")
            async for item in subreddit.mod.stream.modqueue():
                print(item)

        """
        return stream_generator(
            self.subreddit.mod.modqueue, only=only, **stream_options
        )

    def reports(
        self, only: Optional[str] = None, **stream_options: Any
    ) -> AsyncGenerator[
        Union["asyncpraw.models.Comment", "asyncpraw.models.Submission"], None
    ]:
        """Yield reported comments and submissions as they become available.

        :param only: If specified, one of ``"comments"``, or ``"submissions"`` to yield
            only results of that type.

        Keyword arguments are passed to :func:`.stream_generator`.

        To print new user and mod report reasons in the report queue try:

        .. code-block:: python

            subreddit = await reddit.subreddit("mod")
            async for item in subreddit.mod.stream.reports():
                print(item)

        """
        return stream_generator(self.subreddit.mod.reports, only=only, **stream_options)

    def spam(
        self, only: Optional[str] = None, **stream_options: Any
    ) -> AsyncGenerator[
        Union["asyncpraw.models.Comment", "asyncpraw.models.Submission"], None
    ]:
        """Yield spam comments and submissions as they become available.

        :param only: If specified, one of ``"comments"``, or ``"submissions"`` to yield
            only results of that type.

        Keyword arguments are passed to :func:`.stream_generator`.

        To print new items in the spam queue try:

        .. code-block:: python

            subreddit = await reddit.subreddit("mod")
            async for item in subreddit.mod.stream.spam():
                print(item)

        """
        return stream_generator(self.subreddit.mod.spam, only=only, **stream_options)

    def unmoderated(
        self, **stream_options: Any
    ) -> AsyncGenerator["asyncpraw.models.Submission", None]:
        """Yield unmoderated submissions as they become available.

        Keyword arguments are passed to :func:`.stream_generator`.

        To print new items in the unmoderated queue try:

        .. code-block:: python

            subreddit = await reddit.subreddit("mod")
            async for item in subreddit.mod.stream.unmoderated():
                print(item)

        """
        return stream_generator(self.subreddit.mod.unmoderated, **stream_options)

    def unread(
        self, **stream_options: Any
    ) -> AsyncGenerator["asyncpraw.models.SubredditMessage", None]:
        """Yield unread old modmail messages as they become available.

        Keyword arguments are passed to :func:`.stream_generator`.

        .. seealso::

            :meth:`~.inbox` for all messages.

        To print new mail in the unread modmail queue try:

        .. code-block:: python

            subreddit = await reddit.subreddit("mod")
            async for message in subreddit.mod.stream.unread():
                print("From: {}, To: {}".format(message.author, message.dest))

        """
        return stream_generator(self.subreddit.mod.unread, **stream_options)


class SubredditQuarantine:
    """Provides subreddit quarantine related methods.

    To opt-in into a quarantined subreddit:

    .. code-block:: python

        subreddit = await reddit.subreddit("test")
        await subreddit.quaran.opt_in()

    """

    def __init__(self, subreddit: "asyncpraw.models.Subreddit"):
        """Create a SubredditQuarantine instance.

        :param subreddit: The subreddit associated with the quarantine.

        """
        self.subreddit = subreddit

    async def opt_in(self):
        """Permit your user access to the quarantined subreddit.

        Usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("QUESTIONABLE")
            async for submission in subreddit.hot():  # Raises asyncprawcore.Forbidden
                print(submission)

            await subreddit.quaran.opt_in()
            async for submission in subreddit.hot():
                print(submission)  # Returns Submission

        """
        data = {"sr_name": str(self.subreddit)}
        try:
            await self.subreddit._reddit.post(API_PATH["quarantine_opt_in"], data=data)
        except Redirect:
            pass

    async def opt_out(self):
        """Remove access to the quarantined subreddit.

        Usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("QUESTIONABLE")
            async for submission in subreddit.hot():
                print(submission)  # Returns Submission

            await subreddit.quaran.opt_out()
            async for submission in subreddit.hot():  # Raises asyncprawcore.Forbidden
                print(submission)

        """
        data = {"sr_name": str(self.subreddit)}
        try:
            await self.subreddit._reddit.post(API_PATH["quarantine_opt_out"], data=data)
        except Redirect:
            pass


class SubredditRelationship:
    """Represents a relationship between a redditor and subreddit.

    Instances of this class can be iterated through in order to discover the Redditors
    that make up the relationship.

    For example, banned users of a subreddit can be iterated through like so:

    .. code-block:: python

        subreddit = await reddit.subreddit("redditdev")
        async for ban in subreddit.banned():
            print("{ban}: {ban.note}")

    """

    def __call__(
        self,
        redditor: Optional[Union[str, "asyncpraw.models.Redditor"]] = None,
        **generator_kwargs,
    ) -> Iterator["asyncpraw.models.Redditor"]:
        """Return a :class:`.ListingGenerator` for Redditors in the relationship.

        :param redditor: When provided, yield at most a single :class:`~.Redditor`
            instance. This is useful to confirm if a relationship exists, or to fetch
            the metadata associated with a particular relationship (default: None).

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        """
        Subreddit._safely_add_arguments(generator_kwargs, "params", user=redditor)
        url = API_PATH[f"list_{self.relationship}"].format(subreddit=self.subreddit)
        return ListingGenerator(self.subreddit._reddit, url, **generator_kwargs)

    def __init__(self, subreddit: "asyncpraw.models.Subreddit", relationship: str):
        """Create a SubredditRelationship instance.

        :param subreddit: The subreddit for the relationship.
        :param relationship: The name of the relationship.

        """
        self.relationship = relationship
        self.subreddit = subreddit

    async def add(
        self, redditor: Union[str, "asyncpraw.models.Redditor"], **other_settings: Any
    ):
        """Add ``redditor`` to this relationship.

        :param redditor: A redditor name (e.g., ``"spez"``) or :class:`~.Redditor`
            instance.

        """
        data = {"name": str(redditor), "type": self.relationship}
        data.update(other_settings)
        url = API_PATH["friend"].format(subreddit=self.subreddit)
        await self.subreddit._reddit.post(url, data=data)

    async def remove(self, redditor: Union[str, "asyncpraw.models.Redditor"]):
        """Remove ``redditor`` from this relationship.

        :param redditor: A redditor name (e.g., ``"spez"``) or :class:`~.Redditor`
            instance.

        """
        data = {"name": str(redditor), "type": self.relationship}
        url = API_PATH["unfriend"].format(subreddit=self.subreddit)
        await self.subreddit._reddit.post(url, data=data)


class ContributorRelationship(SubredditRelationship):
    """Provides methods to interact with a Subreddit's contributors.

    Contributors are also known as approved submitters.

    Contributors of a subreddit can be iterated through like so:

    .. code-block:: python

        subreddit = await reddit.subreddit("redditdev")
        async for contributor in subreddit.contributor():
            print(contributor)

    """

    async def leave(self):
        """Abdicate the contributor position."""
        if not self.subreddit._fetched:
            await self.subreddit._fetch()
        await self.subreddit._reddit.post(
            API_PATH["leavecontributor"], data={"id": self.subreddit.fullname}
        )


class ModeratorRelationship(SubredditRelationship):
    """Provides methods to interact with a Subreddit's moderators.

    Moderators of a subreddit can be iterated through like so:

    .. code-block:: python

        subreddit = await reddit.subreddit("redditdev")
        async for moderator in subreddit.moderator:
            print(moderator)

    """

    PERMISSIONS = {"access", "config", "flair", "mail", "posts", "wiki"}

    @staticmethod
    def _handle_permissions(permissions: List[str], other_settings: dict):
        other_settings = deepcopy(other_settings) if other_settings else {}
        other_settings["permissions"] = permissions_string(
            permissions, ModeratorRelationship.PERMISSIONS
        )
        return other_settings

    async def __aiter__(self):
        """Asynchronously iterate through Redditors who are moderators.

        For example, to list the moderators along with their permissions try:

        .. code-block:: python

            subreddit = await reddit.subreddit("SUBREDDIT")
            async for moderator in subreddit.moderator:
                print(f"{moderator}: {moderator.mod_permissions}")

        """
        url = API_PATH[f"list_{self.relationship}"].format(subreddit=self.subreddit)
        results = await self.subreddit._reddit.get(url)
        for result in results:
            yield result

    async def __call__(
        self, redditor: Optional[Union[str, "asyncpraw.models.Redditor"]] = None
    ) -> List["asyncpraw.models.Redditor"]:  # pylint: disable=arguments-differ
        """Return a list of Redditors who are moderators.

        :param redditor: When provided, return a list containing at most one
            :class:`~.Redditor` instance. This is useful to confirm if a relationship
            exists, or to fetch the metadata associated with a particular relationship
            (default: None).

        .. note::

            Unlike other relationship callables, this relationship is not paginated.
            Thus it simply returns the full list, rather than an iterator for the
            results.

        To be used like:

        .. code-block:: python

            subreddit = await reddit.subreddit("nameofsub")
            moderators = await subreddit.moderator()

        """
        params = {} if redditor is None else {"user": redditor}
        url = API_PATH[f"list_{self.relationship}"].format(subreddit=self.subreddit)
        return await self.subreddit._reddit.get(url, params=params)

    # pylint: disable=arguments-differ
    async def add(
        self,
        redditor: Union[str, "asyncpraw.models.Redditor"],
        permissions: Optional[List[str]] = None,
        **other_settings: Any,
    ):
        """Add or invite ``redditor`` to be a moderator of the subreddit.

        :param redditor: A redditor name (e.g., ``"spez"``) or :class:`~.Redditor`
            instance.
        :param permissions: When provided (not ``None``), permissions should be a list
            of strings specifying which subset of permissions to grant. An empty list
            ``[]`` indicates no permissions, and when not provided ``None``, indicates
            full permissions.

        An invite will be sent unless the user making this call is an admin user.

        For example, to invite ``"spez"`` with ``"posts"`` and ``"mail"`` permissions to
        ``r/test``, try:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            await subreddit.moderator.add("spez", ["posts", "mail"])

        """
        other_settings = self._handle_permissions(permissions, other_settings)
        await super().add(redditor, **other_settings)

    # pylint: enable=arguments-differ

    async def invite(
        self,
        redditor: Union[str, "asyncpraw.models.Redditor"],
        permissions: Optional[List[str]] = None,
        **other_settings: Any,
    ):
        """Invite ``redditor`` to be a moderator of the subreddit.

        :param redditor: A redditor name (e.g., ``"spez"``) or :class:`~.Redditor`
            instance.
        :param permissions: When provided (not ``None``), permissions should be a list
            of strings specifying which subset of permissions to grant. An empty list
            ``[]`` indicates no permissions, and when not provided ``None``, indicates
            full permissions.

        For example, to invite ``"spez"`` with ``posts`` and ``mail``
            permissions to ``r/test``, try:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            await subreddit.moderator.invite("spez", ["posts", "mail"])

        """
        data = self._handle_permissions(permissions, other_settings)
        data.update({"name": str(redditor), "type": "moderator_invite"})
        url = API_PATH["friend"].format(subreddit=self.subreddit)
        await self.subreddit._reddit.post(url, data=data)

    def invited(
        self,
        redditor: Optional[Union[str, "asyncpraw.models.Redditor"]] = None,
        **generator_kwargs: Any,
    ) -> Iterator["asyncpraw.models.Redditor"]:
        """Return a :class:`.ListingGenerator` for Redditors invited to be moderators.

        :param redditor: When provided, return a list containing at most one
            :class:`~.Redditor` instance. This is useful to confirm if a relationship
            exists, or to fetch the metadata associated with a particular relationship
            (default: None).

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        .. note::

            Unlike other usages of :class:`.ListingGenerator`, ``limit`` has no effect
            in the quantity returned. This endpoint always returns moderators in batches
            of 25 at a time regardless of what ``limit`` is set to.

        Usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("NAME")
            async for invited_mod in subreddit.moderator.invited():
                print(invited_mod)

        """
        generator_kwargs["params"] = {"username": redditor} if redditor else None
        url = API_PATH["list_invited_moderator"].format(subreddit=self.subreddit)
        return ListingGenerator(self.subreddit._reddit, url, **generator_kwargs)

    async def leave(self):
        """Abdicate the moderator position (use with care).

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("subredditname")
            await subreddit.moderator.leave()

        """
        await self.remove(
            self.subreddit._reddit.config.username or self.subreddit._reddit.user.me()
        )

    async def remove_invite(self, redditor: Union[str, "asyncpraw.models.Redditor"]):
        """Remove the moderator invite for ``redditor``.

        :param redditor: A redditor name (e.g., ``"spez"``) or :class:`~.Redditor`
            instance.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("subredditname")
            await subreddit.moderator.remove_invite("spez")

        """
        data = {"name": str(redditor), "type": "moderator_invite"}
        url = API_PATH["unfriend"].format(subreddit=self.subreddit)
        await self.subreddit._reddit.post(url, data=data)

    async def update(
        self,
        redditor: Union[str, "asyncpraw.models.Redditor"],
        permissions: Optional[List[str]] = None,
    ):
        """Update the moderator permissions for ``redditor``.

        :param redditor: A redditor name (e.g., ``"spez"``) or :class:`~.Redditor`
            instance.
        :param permissions: When provided (not ``None``), permissions should be a list
            of strings specifying which subset of permissions to grant. An empty list
            ``[]`` indicates no permissions, and when not provided, ``None``, indicates
            full permissions.

        For example, to add all permissions to the moderator, try:

        .. code-block:: python

            await subreddit.moderator.update("spez")

        To remove all permissions from the moderator, try:

        .. code-block:: python

            await subreddit.moderator.update("spez", [])

        """
        url = API_PATH["setpermissions"].format(subreddit=self.subreddit)
        data = self._handle_permissions(
            permissions, {"name": str(redditor), "type": "moderator"}
        )
        await self.subreddit._reddit.post(url, data=data)

    async def update_invite(
        self,
        redditor: Union[str, "asyncpraw.models.Redditor"],
        permissions: Optional[List[str]] = None,
    ):
        """Update the moderator invite permissions for ``redditor``.

        :param redditor: A redditor name (e.g., ``"spez"``) or :class:`~.Redditor`
            instance.
        :param permissions: When provided (not ``None``), permissions should be a list
            of strings specifying which subset of permissions to grant. An empty list
            ``[]`` indicates no permissions, and when not provided, ``None``, indicates
            full permissions.

        For example, to grant the ``flair``` and ``mail``` permissions to the moderator
        invite, try:

        .. code-block:: python

            await subreddit.moderator.update_invite("spez", ["flair", "mail"])

        """
        url = API_PATH["setpermissions"].format(subreddit=self.subreddit)
        data = self._handle_permissions(
            permissions, {"name": str(redditor), "type": "moderator_invite"}
        )
        await self.subreddit._reddit.post(url, data=data)


class Modmail:
    """Provides modmail functions for a subreddit.

    For example, to send a new modmail from the subreddit ``r/test`` to user ``u/spez``
    with the subject ``test`` along with a message body of ``hello``:

    .. code-block:: python

        subreddit = await reddit.subreddit("test")
        await subreddit.modmail.create("test", "hello", "spez")

    """

    async def __call__(
        self, id: Optional[str] = None, mark_read: bool = False, fetch=True
    ):  # noqa: D207, D301
        """Return an individual conversation.

        :param id: A reddit base36 conversation ID, e.g., ``2gmz``.
        :param mark_read: If True, conversation is marked as read (default: False).
        :param fetch: If True, conversation fully fetched (default: True).

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("redditdev")
            await subreddit.modmail("2gmz", mark_read=True)

        If you don't need the object fetched right away (e.g., to utilize a class
        method) you can do:

        .. code-block:: python

            subreddit = await reddit.subreddit("redditdev")
            message = await subreddit.modmail("2gmz", lazy=True)
            await message.archive()

        To print all messages from a conversation as Markdown source:

        .. code-block:: python

            subreddit = await reddit.subreddit("redditdev")
            conversation = await subreddit.modmail("2gmz", mark_read=True)
            for message in conversation.messages:
                print(message.body_markdown)

        ``ModmailConversation.user`` is a special instance of :class:`.Redditor` with
        extra attributes describing the non-moderator user's recent posts, comments, and
        modmail messages within the subreddit, as well as information on active bans and
        mutes. This attribute does not exist on internal moderator discussions.

        For example, to print the user's ban status:

        .. code-block:: python

            subreddit = await reddit.subreddit("redditdev")
            conversation = await subreddit.modmail("2gmz", mark_read=True)
            print(conversation.user.ban_status)

        To print a list of recent submissions by the user:

        .. code-block:: python

            subreddit = await reddit.subreddit("redditdev")
            conversation = await subreddit.modmail("2gmz", mark_read=True)
            print(conversation.user.recent_posts)

        """
        # pylint: disable=invalid-name,redefined-builtin
        modmail_conversation = ModmailConversation(
            self.subreddit._reddit, id=id, mark_read=mark_read
        )
        if fetch:
            await modmail_conversation._fetch()
        return modmail_conversation

    def __init__(self, subreddit: "asyncpraw.models.Subreddit"):
        """Construct an instance of the Modmail object."""
        self.subreddit = subreddit

    def _build_subreddit_list(
        self, other_subreddits: Optional[List["asyncpraw.models.Subreddit"]]
    ):
        """Return a comma-separated list of subreddit display names."""
        subreddits = [self.subreddit] + (other_subreddits or [])
        return ",".join(str(subreddit) for subreddit in subreddits)

    async def bulk_read(
        self,
        other_subreddits: Optional[
            List[Union["asyncpraw.models.Subreddit", str]]
        ] = None,
        state: Optional[str] = None,
    ) -> List[ModmailConversation]:
        """Mark conversations for subreddit(s) as read.

        Due to server-side restrictions, "all" is not a valid subreddit for this method.
        Instead, use :meth:`~.Modmail.subreddits` to get a list of subreddits using the
        new modmail.

        :param other_subreddits: A list of :class:`.Subreddit` instances for which to
            mark conversations (default: None).
        :param state: Can be one of: all, archived, highlighted, inprogress, mod, new,
            notifications, or appeals, (default: all). "all" does not include internal,
            archived, or appeals conversations.

        :returns: A list of lazy :class:`.ModmailConversation` instances that were
            marked read.

        For example, to mark all notifications for a subreddit as read:

        .. code-block:: python

            subreddit = await reddit.subreddit("redditdev")
            await subreddit.modmail.bulk_read(state="notifications")

        """
        params = {"entity": self._build_subreddit_list(other_subreddits)}
        if state:
            params["state"] = state
        response = await self.subreddit._reddit.post(
            API_PATH["modmail_bulk_read"], params=params
        )
        return [
            await self(conversation_id, fetch=False)
            for conversation_id in response["conversation_ids"]
        ]

    async def conversations(
        self,
        after: Optional[str] = None,
        limit: Optional[int] = None,
        other_subreddits: Optional[List["asyncpraw.models.Subreddit"]] = None,
        sort: Optional[str] = None,
        state: Optional[str] = None,
    ) -> AsyncGenerator[ModmailConversation, None]:  # noqa: D207, D301
        """Generate :class:`.ModmailConversation` objects for subreddit(s).

        :param after: A base36 modmail conversation id. When provided, the listing
            begins after this conversation (default: None).
        :param limit: The maximum number of conversations to fetch. If None, the
            server-side default is 25 at the time of writing (default: None).
        :param other_subreddits: A list of :class:`.Subreddit` instances for which to
            fetch conversations (default: None).
        :param sort: Can be one of: mod, recent, unread, user (default: recent).
        :param state: Can be one of: all, archived, highlighted, inprogress, mod, new,
            notifications, or appeals, (default: all). "all" does not include internal,
            archived, or appeals conversations.

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

        for name, value in {
            "after": after,
            "limit": limit,
            "sort": sort,
            "state": state,
        }.items():
            if value:
                params[name] = value

        response = await self.subreddit._reddit.get(
            API_PATH["modmail_conversations"], params=params
        )
        for conversation_id in response["conversationIds"]:
            data = {
                "conversation": response["conversations"][conversation_id],
                "messages": response["messages"],
            }
            yield ModmailConversation.parse(
                data, self.subreddit._reddit, convert_objects=False
            )

    async def create(
        self,
        subject: str,
        body: str,
        recipient: Union[str, "asyncpraw.models.Redditor"],
        author_hidden: bool = False,
    ) -> ModmailConversation:
        """Create a new modmail conversation.

        :param subject: The message subject. Cannot be empty.
        :param body: The message body. Cannot be empty.
        :param recipient: The recipient; a username or an instance of
            :class:`.Redditor`.
        :param author_hidden: When True, author is hidden from non-moderators (default:
            False).

        :returns: A :class:`.ModmailConversation` object for the newly created
            conversation.

        .. code-block:: python

            subreddit = await reddit.subreddit("redditdev")
            redditor = await reddit.redditor("bboe")
            await subreddit.modmail.create("Subject", "Body", redditor)

        """
        data = {
            "body": body,
            "isAuthorHidden": author_hidden,
            "srName": str(self.subreddit),
            "subject": subject,
            "to": str(recipient),
        }
        return await self.subreddit._reddit.post(
            API_PATH["modmail_conversations"], data=data
        )

    async def subreddits(
        self,
    ) -> AsyncGenerator["asyncpraw.models.Subreddit", None]:
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
            subreddit = type(self.subreddit)(
                self.subreddit._reddit, value["display_name"]
            )
            subreddit.last_updated = value["lastUpdated"]
            yield subreddit

    async def unread_count(self) -> Dict[str, int]:
        """Return unread conversation count by conversation state.

        At time of writing, possible states are: archived, highlighted, inprogress, mod,
        new, notifications, or appeals.

        :returns: A dict mapping conversation states to unread counts.

        For example, to print the count of unread moderator discussions:

        .. code-block:: python

            subreddit = await reddit.subreddit("redditdev")
            unread_counts = await subreddit.modmail.unread_count()
            print(unread_counts["mod"])

        """
        return await self.subreddit._reddit.get(API_PATH["modmail_unread_count"])


class SubredditStream:
    """Provides submission and comment streams."""

    def __init__(self, subreddit: "asyncpraw.models.Subreddit"):
        """Create a SubredditStream instance.

        :param subreddit: The subreddit associated with the streams.

        """
        self.subreddit = subreddit

    def comments(
        self, **stream_options: Any
    ) -> AsyncGenerator["asyncpraw.models.Comment", None]:
        """Yield new comments as they become available.

        Comments are yielded oldest first. Up to 100 historical comments will initially
        be returned.

        Keyword arguments are passed to :func:`.stream_generator`.

        .. note::

            While Async PRAW tries to catch all new comments, some high-volume streams,
            especially the r/all stream, may drop some comments.

        For example, to retrieve all new comments made to the ``iama`` subreddit, try:

        .. code-block:: python

            subreddit = await reddit.subreddit("iama")
            async for comment in subreddit.stream.comments():
                print(comment)

        To only retrieve new submissions starting when the stream is created, pass
        ``skip_existing=True``:

        .. code-block:: python

            subreddit = await reddit.subreddit("iama")
            async for comment in subreddit.stream.comments(skip_existing=True):
                print(comment)

        """
        return stream_generator(self.subreddit.comments, **stream_options)

    def submissions(
        self, **stream_options: Any
    ) -> AsyncGenerator["asyncpraw.models.Submission", None]:
        """Yield new submissions as they become available.

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


class SubredditStylesheet:
    """Provides a set of stylesheet functions to a Subreddit.

    For example, to add the css data ``.test{color:blue}`` to the existing stylesheet:

    .. code-block:: python

        subreddit = await reddit.subreddit("SUBREDDIT")
        stylesheet = await subreddit.stylesheet()
        stylesheet.stylesheet.stylesheet += ".test{color:blue}"
        await subreddit.stylesheet.update(stylesheet.stylesheet)

    """

    async def __call__(self) -> "asyncpraw.models.Stylesheet":
        """Return the subreddit's stylesheet.

        To be used as:

        .. code-block:: python

            subreddit = await reddit.subreddit("SUBREDDIT")
            stylesheet = await subreddit.stylesheet()

        """
        url = API_PATH["about_stylesheet"].format(subreddit=self.subreddit)
        return await self.subreddit._reddit.get(url)

    def __init__(self, subreddit: "asyncpraw.models.Subreddit"):
        """Create a SubredditStylesheet instance.

        :param subreddit: The subreddit associated with the stylesheet.

        An instance of this class is provided as:

        .. code-block:: python

            subreddit = await reddit.subreddit("SUBREDDIT")
            subreddit.stylesheet

        """
        self.subreddit = subreddit

    async def _update_structured_styles(self, style_data: Dict[str, Union[str, Any]]):
        url = API_PATH["structured_styles"].format(subreddit=self.subreddit)
        await self.subreddit._reddit.patch(url, style_data)

    async def _upload_image(
        self, image_path: str, data: Dict[str, Union[str, Any]]
    ) -> Dict[str, Any]:
        with open(image_path, "rb") as image:
            header = image.read(len(JPEG_HEADER))
            image.seek(0)
            data["img_type"] = "jpg" if header == JPEG_HEADER else "png"
            url = API_PATH["upload_image"].format(subreddit=self.subreddit)
            response = await self.subreddit._reddit.post(
                url, data=data, files={"file": image}
            )
            if response["errors"]:
                error_type = response["errors"][0]
                error_value = response.get("errors_values", [""])[0]
                assert error_type in [
                    "BAD_CSS_NAME",
                    "IMAGE_ERROR",
                ], "Please file a bug with Async PRAW."
                raise RedditAPIException([[error_type, error_value, None]])
            return response

    async def _upload_style_asset(self, image_path: str, image_type: str) -> str:
        data = {"imagetype": image_type, "filepath": basename(image_path)}
        data["mimetype"] = "image/jpeg"
        if image_path.lower().endswith(".png"):
            data["mimetype"] = "image/png"
        url = API_PATH["style_asset_lease"].format(subreddit=self.subreddit)

        response = await self.subreddit._reddit.post(url, data=data)
        upload_lease = response["s3UploadLease"]
        upload_data = {item["name"]: item["value"] for item in upload_lease["fields"]}
        upload_url = f"https:{upload_lease['action']}"

        with open(image_path, "rb") as image:
            upload_data["file"] = image
            response = await self.subreddit._reddit._core._requestor._http.post(
                upload_url, data=upload_data
            )
        response.raise_for_status()

        return f"{upload_url}/{upload_data['key']}"

    async def delete_banner(self):
        """Remove the current subreddit (redesign) banner image.

        Succeeds even if there is no banner image.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("SUBREDDIT")
            await subreddit.stylesheet.delete_banner()

        """
        data = {"bannerBackgroundImage": ""}
        await self._update_structured_styles(data)

    async def delete_banner_additional_image(self):
        """Remove the current subreddit (redesign) banner additional image.

        Succeeds even if there is no additional image. Will also delete any configured
        hover image.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("SUBREDDIT")
            await subreddit.stylesheet.delete_banner_additional_image()

        """
        data = {"bannerPositionedImage": "", "secondaryBannerPositionedImage": ""}
        await self._update_structured_styles(data)

    async def delete_banner_hover_image(self):
        """Remove the current subreddit (redesign) banner hover image.

        Succeeds even if there is no hover image.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("SUBREDDIT")
            await subreddit.stylesheet.delete_banner_hover_image()

        """
        data = {"secondaryBannerPositionedImage": ""}
        await self._update_structured_styles(data)

    async def delete_header(self):
        """Remove the current subreddit header image.

        Succeeds even if there is no header image.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("SUBREDDIT")
            await subreddit.stylesheet.delete_header()

        """
        url = API_PATH["delete_sr_header"].format(subreddit=self.subreddit)
        await self.subreddit._reddit.post(url)

    async def delete_image(self, name: str):
        """Remove the named image from the subreddit.

        Succeeds even if the named image does not exist.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("SUBREDDIT")
            await subreddit.stylesheet.delete_image("smile")

        """
        url = API_PATH["delete_sr_image"].format(subreddit=self.subreddit)
        await self.subreddit._reddit.post(url, data={"img_name": name})

    async def delete_mobile_header(self):
        """Remove the current subreddit mobile header.

        Succeeds even if there is no mobile header.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("SUBREDDIT")
            await subreddit.stylesheet.delete_mobile_header()

        """
        url = API_PATH["delete_sr_header"].format(subreddit=self.subreddit)
        await self.subreddit._reddit.post(url)

    async def delete_mobile_icon(self):
        """Remove the current subreddit mobile icon.

        Succeeds even if there is no mobile icon.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("SUBREDDIT")
            await subreddit.stylesheet.delete_mobile_icon()

        """
        url = API_PATH["delete_sr_icon"].format(subreddit=self.subreddit)
        await self.subreddit._reddit.post(url)

    async def update(self, stylesheet: str, reason: Optional[str] = None):
        """Update the subreddit's stylesheet.

        :param stylesheet: The CSS for the new stylesheet.
        :param reason: The reason for updating the stylesheet.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("SUBREDDIT")
            await subreddit.stylesheet.update("p { color: green; }", "color text green")

        """
        data = {
            "op": "save",
            "reason": reason,
            "stylesheet_contents": stylesheet,
        }
        url = API_PATH["subreddit_stylesheet"].format(subreddit=self.subreddit)
        await self.subreddit._reddit.post(url, data=data)

    async def upload(self, name: str, image_path: str) -> Dict[str, str]:
        """Upload an image to the Subreddit.

        :param name: The name to use for the image. If an image already exists with the
            same name, it will be replaced.
        :param image_path: A path to a jpeg or png image.

        :returns: A dictionary containing a link to the uploaded image under the key
            ``img_src``.

        :raises: ``asyncprawcore.TooLarge`` if the overall request body is too large.

        :raises: :class:`.RedditAPIException` if there are other issues with the
            uploaded image. Unfortunately the exception info might not be very specific,
            so try through the website with the same image to see what the problem
            actually might be.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("SUBREDDIT")
            await subreddit.stylesheet.upload("smile", "img.png")

        """
        return await self._upload_image(
            image_path, {"name": name, "upload_type": "img"}
        )

    async def upload_banner(self, image_path: str):
        """Upload an image for the subreddit's (redesign) banner image.

        :param image_path: A path to a jpeg or png image.

        :raises: ``asyncprawcore.TooLarge`` if the overall request body is too large.

        :raises: :class:`.RedditAPIException` if there are other issues with the
            uploaded image. Unfortunately the exception info might not be very specific,
            so try through the website with the same image to see what the problem
            actually might be.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("SUBREDDIT")
            await subreddit.stylesheet.upload_banner("banner.png")

        """
        image_type = "bannerBackgroundImage"
        image_url = await self._upload_style_asset(image_path, image_type)
        await self._update_structured_styles({image_type: image_url})

    async def upload_banner_additional_image(
        self, image_path: str, align: Optional[str] = None
    ):
        """Upload an image for the subreddit's (redesign) additional image.

        :param image_path: A path to a jpeg or png image.
        :param align: Either ``left``, ``centered``, or ``right``. (default: ``left``).

        :raises: ``asyncprawcore.TooLarge`` if the overall request body is too large.

        :raises: :class:`.RedditAPIException` if there are other issues with the
            uploaded image. Unfortunately the exception info might not be very specific,
            so try through the website with the same image to see what the problem
            actually might be.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("SUBREDDIT")
            await subreddit.stylesheet.upload_banner_additional_image("banner.png")

        """
        alignment = {}
        if align is not None:
            if align not in {"left", "centered", "right"}:
                raise ValueError(
                    "align argument must be either `left`, `centered`, or `right`"
                )
            alignment["bannerPositionedImagePosition"] = align

        image_type = "bannerPositionedImage"
        image_url = await self._upload_style_asset(image_path, image_type)
        style_data = {image_type: image_url}
        if alignment:
            style_data.update(alignment)
        await self._update_structured_styles(style_data)

    async def upload_banner_hover_image(self, image_path: str):
        """Upload an image for the subreddit's (redesign) additional image.

        :param image_path: A path to a jpeg or png image.

        Fails if the Subreddit does not have an additional image defined

        :raises: ``asyncprawcore.TooLarge`` if the overall request body is too large.

        :raises: :class:`.RedditAPIException` if there are other issues with the
            uploaded image. Unfortunately the exception info might not be very specific,
            so try through the website with the same image to see what the problem
            actually might be.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("SUBREDDIT")
            await subreddit.stylesheet.upload_banner_hover_image("banner.png")

        """
        image_type = "secondaryBannerPositionedImage"
        image_url = await self._upload_style_asset(image_path, image_type)
        await self._update_structured_styles({image_type: image_url})

    async def upload_header(self, image_path: str) -> Dict[str, str]:
        """Upload an image to be used as the Subreddit's header image.

        :param image_path: A path to a jpeg or png image.

        :returns: A dictionary containing a link to the uploaded image under the key
            ``img_src``.

        :raises: ``asyncprawcore.TooLarge`` if the overall request body is too large.

        :raises: :class:`.RedditAPIException` if there are other issues with the
            uploaded image. Unfortunately the exception info might not be very specific,
            so try through the website with the same image to see what the problem
            actually might be.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("SUBREDDIT")
            await subreddit.stylesheet.upload_header("header.png")

        """
        return await self._upload_image(image_path, {"upload_type": "header"})

    async def upload_mobile_header(self, image_path: str) -> Dict[str, str]:
        """Upload an image to be used as the Subreddit's mobile header.

        :param image_path: A path to a jpeg or png image.

        :returns: A dictionary containing a link to the uploaded image under the key
            ``img_src``.

        :raises: ``asyncprawcore.TooLarge`` if the overall request body is too large.

        :raises: :class:`.RedditAPIException` if there are other issues with the
            uploaded image. Unfortunately the exception info might not be very specific,
            so try through the website with the same image to see what the problem
            actually might be.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("SUBREDDIT")
            await subreddit.stylesheet.upload_mobile_header("header.png")

        """
        return await self._upload_image(image_path, {"upload_type": "banner"})

    async def upload_mobile_icon(self, image_path: str) -> Dict[str, str]:
        """Upload an image to be used as the Subreddit's mobile icon.

        :param image_path: A path to a jpeg or png image.

        :returns: A dictionary containing a link to the uploaded image under the key
            ``img_src``.

        :raises: ``asyncprawcore.TooLarge`` if the overall request body is too large.

        :raises: :class:`.RedditAPIException` if there are other issues with the
            uploaded image. Unfortunately the exception info might not be very specific,
            so try through the website with the same image to see what the problem
            actually might be.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("SUBREDDIT")
            await subreddit.stylesheet.upload_mobile_icon("icon.png")

        """
        return await self._upload_image(image_path, {"upload_type": "icon"})


class SubredditWiki:
    """Provides a set of wiki functions to a Subreddit."""

    async def get_page(self, page_name, lazy=False) -> WikiPage:
        """Return the WikiPage for the subreddit named ``page_name``.

        Set ``lazy=True`` to skip fetching the wiki page.

        This method is to be used to fetch a specific wikipage, like so:

        .. code-block:: python

            subreddit = await reddit.subreddit("iama")
            wikipage = await subreddit.wiki.get_page("proof")
            print(wikipage.content_md)

        """
        wikipage = WikiPage(self.subreddit._reddit, self.subreddit, page_name.lower())
        if not lazy:
            await wikipage._fetch()
        return wikipage

    def __init__(self, subreddit: "asyncpraw.models.Subreddit"):
        """Create a SubredditWiki instance.

        :param subreddit: The subreddit whose wiki to work with.

        """
        self.banned = SubredditRelationship(subreddit, "wikibanned")
        self.contributor = SubredditRelationship(subreddit, "wikicontributor")
        self.subreddit = subreddit

    async def __aiter__(self) -> AsyncGenerator[WikiPage, None]:
        """Iterate through the pages of the wiki.

        This method is to be used to discover all wikipages for a subreddit:

        .. code-block:: python

            subreddit = await reddit.subreddit("iama")
            async for wikipage in subreddit.wiki:
                print(wikipage)

        """
        response = await self.subreddit._reddit.get(
            API_PATH["wiki_pages"].format(subreddit=self.subreddit),
            params={"unique": self.subreddit._reddit._next_unique},
        )
        for page_name in response["data"]:
            yield WikiPage(self.subreddit._reddit, self.subreddit, page_name)

    async def create(
        self,
        name: str,
        content: str,
        reason: Optional[str] = None,
        **other_settings: Any,
    ):
        """Create a new wiki page.

        :param name: The name of the new WikiPage. This name will be normalized.
        :param content: The content of the new WikiPage.
        :param reason: (Optional) The reason for the creation.
        :param other_settings: Additional keyword arguments to pass.

        To create the wiki page ``praw_test`` in ``r/test`` try:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            await subreddit.wiki.create("praw_test", "wiki body text", reason="PRAW Test Creation")

        """
        name = name.replace(" ", "_").lower()
        new = WikiPage(self.subreddit._reddit, self.subreddit, name)
        await new.edit(content=content, reason=reason, **other_settings)
        return new

    def revisions(
        self, **generator_kwargs: Any
    ) -> AsyncGenerator[
        Dict[
            str, Optional[Union["asyncpraw.models.Redditor", WikiPage, str, int, bool]]
        ],
        None,
    ]:
        """Return a :class:`.ListingGenerator` for recent wiki revisions.

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        To view the wiki revisions for ``"praw_test"`` in ``r/test`` try:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            page = await subreddit.wiki.get_page("praw_test")
            async for item in page.revisions():
                print(item)

        """
        url = API_PATH["wiki_revisions"].format(subreddit=self.subreddit)
        return WikiPage._revision_generator(self.subreddit, url, generator_kwargs)
