"""Provide the Submission class."""

from __future__ import annotations

import re
from json import dumps
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin
from warnings import warn

from asyncprawcore import Conflict

from asyncpraw.const import API_PATH
from asyncpraw.exceptions import InvalidURL
from asyncpraw.models.comment_forest import CommentForest
from asyncpraw.models.listing.listing import Listing
from asyncpraw.models.listing.mixins import SubmissionListingMixin
from asyncpraw.models.reddit.base import RedditBase
from asyncpraw.models.reddit.mixins import FullnameMixin, ModNoteMixin, ThingModerationMixin, UserContentMixin
from asyncpraw.models.reddit.poll import PollData
from asyncpraw.models.reddit.redditor import Redditor
from asyncpraw.models.reddit.subreddit import Subreddit
from asyncpraw.util import cachedproperty

if TYPE_CHECKING:
    from collections.abc import Iterator

    import asyncpraw.models

INLINE_MEDIA_PATTERN = re.compile(
    r"\n\n!?(\[.*?])?\(?((https://((preview|i)\.redd\.it|reddit.com/link).*?)|(?!https)([a-zA-Z0-9]+( \".*?\")?))\)?"
)
MEDIA_TYPE_MAPPING = {
    "Image": "img",
    "RedditVideo": "video",
    "AnimatedImage": "gif",
}


class SubmissionFlair:
    """Provide a set of functions pertaining to :class:`.Submission` flair."""

    def __init__(self, submission: asyncpraw.models.Submission) -> None:
        """Initialize a :class:`.SubmissionFlair` instance.

        :param submission: The :class:`.Submission` associated with the flair functions.

        """
        self.submission = submission

    async def choices(self) -> list[dict[str, bool | list | str]]:
        """Return list of available flair choices.

        Choices are required in order to use :meth:`.select`.

        For example:

        .. code-block:: python

            choices = await submission.flair.choices()

        """
        if not self.submission._fetched:
            await self.submission._fetch()
        url = API_PATH["flairselector"].format(subreddit=self.submission.subreddit)
        data = await self.submission._reddit.post(url, data={"link": self.submission.fullname})
        return data["choices"]

    async def select(self, flair_template_id: str, *, text: str | None = None) -> None:
        """Select flair for submission.

        :param flair_template_id: The flair template to select. The possible values can
            be discovered through :meth:`.choices`.
        :param text: If the template's ``flair_text_editable`` value is ``True``, this
            value will set a custom text (default: ``None``).

        For example, to select an arbitrary editable flair text (assuming there is one)
        and set a custom value try:

        .. code-block:: python

            choices = await submission.flair.choices()
            template_id = next(x for x in choices if x["flair_text_editable"])["flair_template_id"]
            await submission.flair.select(template_id, text="my custom value")

        """
        data = {
            "flair_template_id": flair_template_id,
            "link": self.submission.fullname,
            "text": text,
        }
        if not self.submission._fetched:
            await self.submission._fetch()
        url = API_PATH["select_flair"].format(subreddit=self.submission.subreddit)
        await self.submission._reddit.post(url, data=data)


class SubmissionModeration(ThingModerationMixin, ModNoteMixin):
    """Provide a set of functions pertaining to :class:`.Submission` moderation.

    Example usage:

    .. code-block:: python

        submission = await reddit.submission("8dmv8z", fetch=False)
        await submission.mod.approve()

    """

    REMOVAL_MESSAGE_API = "removal_link_message"

    def __init__(self, submission: asyncpraw.models.Submission) -> None:
        """Initialize a :class:`.SubmissionModeration` instance.

        :param submission: The submission to moderate.

        """
        self.thing = submission

    async def contest_mode(self, *, state: bool = True) -> None:
        """Set contest mode for the comments of this submission.

        :param state: ``True`` enables contest mode and ``False`` disables (default:
            ``True``).

        Contest mode have the following effects:

        - The comment thread will default to being sorted randomly.
        - Replies to top-level comments will be hidden behind "[show replies]" buttons.
        - Scores will be hidden from non-moderators.
        - Scores accessed through the API (mobile apps, bots) will be obscured to "1"
          for non-moderators.

        Example usage:

        .. code-block:: python

            submission = await reddit.submission("5or86n", fetch=False)
            await submission.mod.contest_mode()

        """
        await self.thing._reddit.post(API_PATH["contest_mode"], data={"id": self.thing.fullname, "state": state})

    async def flair(
        self,
        *,
        css_class: str = "",
        flair_template_id: str | None = None,
        text: str = "",
    ) -> None:
        """Set flair for the submission.

        :param css_class: The css class to associate with the flair html (default:
            ``""``).
        :param flair_template_id: The flair template ID to use when flairing.
        :param text: The flair text to associate with the :class:`.Submission` (default:
            ``""``).

        This method can only be used by an authenticated user who is a moderator of the
        submission's :class:`.Subreddit`.

        Example usage:

        .. code-block:: python

            submission = await reddit.submission("5or86n", fetch=False)
            await submission.mod.flair(text="PRAW", css_class="bot")

        """
        data = {
            "css_class": css_class,
            "link": self.thing.fullname,
            "text": text,
        }
        if not self.thing._fetched:
            await self.thing._fetch()
        url = API_PATH["flair"].format(subreddit=self.thing.subreddit)
        if flair_template_id is not None:
            data["flair_template_id"] = flair_template_id
            url = API_PATH["select_flair"].format(subreddit=self.thing.subreddit)
        await self.thing._reddit.post(url, data=data)

    async def nsfw(self) -> None:
        """Mark as not safe for work.

        This method can be used both by the submission author and moderators of the
        subreddit that the submission belongs to.

        Example usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            submission = await subreddit.submit("nsfw test", selftext="nsfw")
            await submission.mod.nsfw()

        .. seealso::

            :meth:`.sfw`

        """
        await self.thing._reddit.post(API_PATH["marknsfw"], data={"id": self.thing.fullname})

    async def set_original_content(self) -> None:
        """Mark as original content.

        This method can be used by moderators of the subreddit that the submission
        belongs to. If the subreddit has enabled the Original Content beta feature in
        settings, then the submission's author can use it as well.

        Example usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            submission = await subreddit.submit("oc test", selftext="original")
            await submission.mod.set_original_content()

        .. seealso::

            :meth:`.unset_original_content`

        """
        data = {
            "id": self.thing.id,
            "fullname": self.thing.fullname,
            "should_set_oc": True,
            "executed": False,
            "r": self.thing.subreddit,
        }
        await self.thing._reddit.post(API_PATH["set_original_content"], data=data)

    async def sfw(self) -> None:
        """Mark as safe for work.

        This method can be used both by the submission author and moderators of the
        subreddit that the submission belongs to.

        Example usage:

        .. code-block:: python

            submission = await reddit.submission("5or86n", fetch=False)
            await submission.mod.sfw()

        .. seealso::

            :meth:`.nsfw`

        """
        await self.thing._reddit.post(API_PATH["unmarknsfw"], data={"id": self.thing.fullname})

    async def spoiler(self) -> None:
        """Indicate that the submission contains spoilers.

        This method can be used both by the submission author and moderators of the
        subreddit that the submission belongs to.

        Example usage:

        .. code-block:: python

            submission = await reddit.submission("5or86n", fetch=False)
            await submission.mod.spoiler()

        .. seealso::

            :meth:`.unspoiler`

        """
        await self.thing._reddit.post(API_PATH["spoiler"], data={"id": self.thing.fullname})

    async def sticky(self, *, bottom: bool = True, state: bool = True) -> asyncpraw.models.Submission:
        """Set the submission's sticky state in its subreddit.

        :param bottom: When ``True``, set the submission as the bottom sticky. If no top
            sticky exists, this submission will become the top sticky regardless
            (default: ``True``).
        :param state: ``True`` sets the sticky for the submission and ``False`` unsets
            (default: ``True``).

        :returns: The stickied submission object.

        .. note::

            When a submission is stickied two or more times, the Reddit API responds
            with a 409 error that is raised as a ``Conflict`` by asyncprawcore. This
            method suppresses these ``Conflict`` errors.

        This submission will replace the second stickied submission if one exists.

        For example:

        .. code-block:: python

            submission = await reddit.submission("5or86n", fetch=False)
            await submission.mod.sticky()

        """
        data = {"id": self.thing.fullname, "state": state}
        if not bottom:
            data["num"] = 1
        try:
            return await self.thing._reddit.post(API_PATH["sticky_submission"], data=data)
        except Conflict:
            pass

    async def suggested_sort(self, *, sort: str = "blank") -> None:
        """Set the suggested sort for the comments of the submission.

        :param sort: Can be one of: ``"confidence"``, ``"top"``, ``"new"``,
            ``"controversial"``, ``"old"``, ``"random"``, ``"qa"``, or ``"blank"``
            (default: ``"blank"``).

        """
        await self.thing._reddit.post(API_PATH["suggested_sort"], data={"id": self.thing.fullname, "sort": sort})

    async def unset_original_content(self) -> None:
        """Indicate that the submission is not original content.

        This method can be used by moderators of the subreddit that the submission
        belongs to. If the subreddit has enabled the Original Content beta feature in
        settings, then the submission's author can use it as well.

        Example usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            submission = await subreddit.submit("oc test", selftext="original")
            await submission.mod.unset_original_content()

        .. seealso::

            :meth:`.set_original_content`

        """
        data = {
            "id": self.thing.id,
            "fullname": self.thing.fullname,
            "should_set_oc": False,
            "executed": False,
            "r": self.thing.subreddit,
        }
        await self.thing._reddit.post(API_PATH["set_original_content"], data=data)

    async def unspoiler(self) -> None:
        """Indicate that the submission does not contain spoilers.

        This method can be used both by the submission author and moderators of the
        subreddit that the submission belongs to.

        For example:

        .. code-block:: python

            sub = await reddit.subreddit("test")
            submission = await sub.submit("not spoiler", selftext="spoiler")
            await submission.mod.unspoiler()

        .. seealso::

            :meth:`.spoiler`

        """
        await self.thing._reddit.post(API_PATH["unspoiler"], data={"id": self.thing.fullname})

    async def update_crowd_control_level(self, level: int) -> None:
        """Change the Crowd Control level of the submission.

        :param level: An integer between 0 and 3.

        **Level Descriptions**

        ===== ======== ================================================================
        Level Name     Description
        ===== ======== ================================================================
        0     Off      Crowd Control will not action any of the submission's comments.
        1     Lenient  Comments from users who have negative karma in the subreddit are
                       automatically collapsed.
        2     Moderate Comments from new users and users with negative karma in the
                       subreddit are automatically collapsed.
        3     Strict   Comments from users who haven't joined the subreddit, new users,
                       and users with negative karma in the subreddit are automatically
                       collapsed.
        ===== ======== ================================================================

        Example usage:

        .. code-block:: python

            submission = await reddit.submission("745ryj")
            await submission.mod.update_crowd_control_level(2)

        .. seealso::

            :meth:`~.CommentModeration.show`

        """
        await self.thing._reddit.post(
            API_PATH["update_crowd_control"],
            data={"id": self.thing.fullname, "level": level},
        )


class Submission(SubmissionListingMixin, UserContentMixin, FullnameMixin, RedditBase):
    """A class for submissions to Reddit.

    .. include:: ../../typical_attributes.rst

    ========================== =========================================================
    Attribute                  Description
    ========================== =========================================================
    ``author``                 Provides an instance of :class:`.Redditor`.
    ``author_flair_text``      The text content of the author's flair, or ``None`` if
                               not flaired.
    ``clicked``                Whether or not the submission has been clicked by the
                               client.
    ``comments``               Provides an instance of :class:`.CommentForest`.
    ``created_utc``            Time the submission was created, represented in `Unix
                               Time`_.
    ``distinguished``          Whether or not the submission is distinguished.
    ``edited``                 Whether or not the submission has been edited.
    ``id``                     ID of the submission.
    ``is_original_content``    Whether or not the submission has been set as original
                               content.
    ``is_self``                Whether or not the submission is a selfpost (text-only).
    ``link_flair_template_id`` The link flair's ID.
    ``link_flair_text``        The link flair's text content, or ``None`` if not
                               flaired.
    ``locked``                 Whether or not the submission has been locked.
    ``name``                   Fullname of the submission.
    ``num_comments``           The number of comments on the submission.
    ``over_18``                Whether or not the submission has been marked as NSFW.
    ``permalink``              A permalink for the submission.
    ``poll_data``              A :class:`.PollData` object representing the data of this
                               submission, if it is a poll submission.
    ``saved``                  Whether or not the submission is saved.
    ``score``                  The number of upvotes for the submission.
    ``selftext``               The submissions' selftext - an empty string if a link
                               post.
    ``spoiler``                Whether or not the submission has been marked as a
                               spoiler.
    ``stickied``               Whether or not the submission is stickied.
    ``subreddit``              Provides an instance of :class:`.Subreddit`.
    ``title``                  The title of the submission.
    ``upvote_ratio``           The percentage of upvotes from all votes on the
                               submission.
    ``url``                    The URL the submission links to, or the permalink if a
                               selfpost.
    ========================== =========================================================

    .. _unix time: https://en.wikipedia.org/wiki/Unix_time

    """

    STR_FIELD = "id"

    @staticmethod
    def id_from_url(url: str) -> str:
        """Return the ID contained within a submission URL.

        :param url: A url to a submission in one of the following formats (http urls
            will also work):

            - ``"https://redd.it/2gmzqe"``
            - ``"https://reddit.com/comments/2gmzqe/"``
            - ``"https://www.reddit.com/r/redditdev/comments/2gmzqe/praw_https/"``
            - ``"https://www.reddit.com/gallery/2gmzqe"``

        :raises: :class:`.InvalidURL` if ``url`` is not a valid submission URL.

        """
        parts = RedditBase._url_parts(url)
        if "comments" not in parts and "gallery" not in parts:
            submission_id = parts[-1]
            if "r" in parts:
                raise InvalidURL(url, message="Invalid URL (subreddit, not submission): {}")

        elif "gallery" in parts:
            submission_id = parts[parts.index("gallery") + 1]

        elif parts[-1] == "comments":
            raise InvalidURL(url, message="Invalid URL (submission ID not present): {}")

        else:
            submission_id = parts[parts.index("comments") + 1]

        if not submission_id.isalnum():
            raise InvalidURL(url)
        return submission_id

    @cachedproperty
    def flair(self) -> SubmissionFlair:
        """Provide an instance of :class:`.SubmissionFlair`.

        This attribute is used to work with flair as a regular user of the subreddit the
        submission belongs to. Moderators can directly use :meth:`.flair`.

        For example, to select an arbitrary editable flair text (assuming there is one)
        and set a custom value try:

        .. code-block:: python

            choices = await submission.flair.choices()
            template_id = next(x for x in choices if x["flair_text_editable"])["flair_template_id"]
            await submission.flair.select(template_id, text="my custom value")

        """
        return SubmissionFlair(self)

    @cachedproperty
    def mod(self) -> SubmissionModeration:
        """Provide an instance of :class:`.SubmissionModeration`.

        Example usage:

        .. code-block:: python

            submission = await reddit.submission("8dmv8z", fetch=False)
            await submission.mod.approve()

        """
        return SubmissionModeration(self)

    @property
    def _kind(self) -> str:
        """Return the class's kind."""
        return self._reddit.config.kinds["submission"]

    @property
    def shortlink(self) -> str:
        """Return a shortlink to the submission.

        For example, https://redd.it/eorhm is a shortlink for
        https://www.reddit.com/r/announcements/comments/eorhm/reddit_30_less_typing/.

        """
        return urljoin(self._reddit.config.short_url, self.id)

    def __init__(
        self,
        reddit: asyncpraw.Reddit,
        id: str | None = None,
        url: str | None = None,
        _data: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a :class:`.Submission` instance.

        :param reddit: An instance of :class:`.Reddit`.
        :param id: A reddit base36 submission ID, e.g., ``"2gmzqe"``.
        :param url: A URL supported by :meth:`.id_from_url`.

        Either ``id`` or ``url`` can be provided, but not both.

        """
        if sum(1 for value in (id, url, _data) if value is not None) != 1:
            msg = "Exactly one of 'id', 'url', or '_data' must be provided."
            raise TypeError(msg)
        self.comment_limit = 2048

        # Specify the sort order for ``comments``
        self.comment_sort = "confidence"

        if id:
            self.id = id
        elif url:
            self.id = self.id_from_url(url)

        super().__init__(reddit, _data=_data)

        self._additional_fetch_params = {}
        self._comments_by_id = {}
        self.comments = CommentForest(self)
        """Provide an instance of :class:`.CommentForest`.

        This attribute can be used, for example, to obtain a flat list of comments, with
        any :class:`.MoreComments` removed:

        .. code-block:: python

            await submission.comments.replace_more(limit=0)
            comments = submission.comments.list()

        :raises: :py:class:`TypeError` if the submission is not fetched.

        Sort order and comment limit must be set with the ``comment_sort`` and
        ``comment_limit`` attributes before the submission and its comments are fetched,
        including any call to :meth:`.replace_more`. The ``fetch`` argument will need to
        set when initializing the :class:`.Submission` instance:

        .. code-block:: python

            submission = await reddit.submission("8dmv8z", fetch=False)
            submission.comment_sort = "new"
            await submission.load()
            comments = submission.comments.list()

        .. note::

            The appropriate values for ``comment_sort`` include ``confidence``,
            ``controversial``, ``new``, ``old``, ``q&a``, and ``top``

        See :ref:`extracting_comments` for more on working with a
        :class:`.CommentForest`.

        """

    def __setattr__(self, attribute: str, value: Any) -> None:
        """Objectify author, subreddit, and poll data attributes."""
        if attribute == "author":
            value = Redditor.from_data(self._reddit, value)
        elif attribute == "subreddit":
            value = Subreddit(self._reddit, value)
        elif attribute == "poll_data":
            value = PollData(self._reddit, value)
        elif (
            attribute == "comment_sort"
            and hasattr(self, "_fetched")
            and self._fetched
            and hasattr(self, "_reddit")
            and self._reddit.config.warn_comment_sort
        ):
            warn(
                "The comments for this submission have already been fetched, so the"
                " updated comment_sort will not have any effect.",
                stacklevel=2,
            )
        super().__setattr__(attribute, value)

    def _chunk(
        self,
        *,
        chunk_size: int,
        other_submissions: list[asyncpraw.models.Submission] | None,
    ) -> Iterator[str]:
        all_submissions = [self.fullname]
        if other_submissions:
            all_submissions += [x.fullname for x in other_submissions]

        for position in range(0, len(all_submissions), chunk_size):
            yield ",".join(all_submissions[position : position + 50])

    async def _edit_experimental(
        self,
        body: str,
        *,
        preserve_inline_media: bool = False,
        inline_media: dict[str, asyncpraw.models.InlineMedia] | None = None,
    ) -> asyncpraw.models.Submission:
        """Replace the body of the object with ``body``.

        :param body: The Markdown formatted content for the updated object.
        :param preserve_inline_media: Attempt to preserve inline media in ``body``.

            .. danger::

                This method is experimental. It is reliant on undocumented API endpoints
                and may result in existing inline media not displaying correctly and/or
                creating a malformed body. Use at your own risk. This method may be
                removed in the future without warning.

        :param inline_media: A dict of :class:`.InlineMedia` objects where the key is
            the placeholder name in ``body``.

        :returns: The current instance after updating its attributes.

        Example usage:

        .. code-block:: python

            from asyncpraw.models import InlineGif, InlineImage, InlineVideo

            submission = await reddit.submission("5or86n")
            gif = InlineGif(path="path/to/image.gif", caption="optional caption")
            image = InlineImage(path="path/to/image.jpg", caption="optional caption")
            video = InlineVideo(path="path/to/video.mp4", caption="optional caption")
            body = "New body with a gif {gif1} an image {image1} and a video {video1} inline"
            media = {"gif1": gif, "image1": image, "video1": video}
            await submission._edit_experimental(submission.selftext + body, inline_media=media)

        """
        data = {
            "thing_id": self.fullname,
            "validate_on_submit": True,
        }
        is_richtext_json = False
        if INLINE_MEDIA_PATTERN.search(body) and self.media_metadata:
            is_richtext_json = True
        if inline_media:
            body = body.format(**{
                placeholder: await self.subreddit._upload_inline_media(media)
                for placeholder, media in inline_media.items()
            })
            is_richtext_json = True
        if is_richtext_json:
            richtext_json = await self.subreddit._convert_to_fancypants(body)
            if preserve_inline_media:
                self._replace_richtext_links(richtext_json)
            data["richtext_json"] = dumps(richtext_json)
        else:
            data["text"] = body
        updated = await self._reddit.post(API_PATH["edit"], data=data)
        if not is_richtext_json:
            updated = updated[0]
            for attribute in [
                "_fetched",
                "_reddit",
                "_submission",
                "replies",
                "subreddit",
            ]:
                if attribute in updated.__dict__:
                    delattr(updated, attribute)
            self.__dict__.update(updated.__dict__)
        else:
            self.__dict__.update(updated)
        return self

    async def _fetch(self) -> None:
        data = await self._fetch_data()
        submission_listing, comment_listing = data
        comment_listing = Listing(self._reddit, _data=comment_listing["data"])

        submission_data = submission_listing["data"]["children"][0]["data"]
        submission = type(self)(self._reddit, _data=submission_data)
        delattr(submission, "comment_limit")
        delattr(submission, "comment_sort")
        submission.comments = CommentForest(self)

        self.__dict__.update(submission.__dict__)
        self.comments._update(comment_listing.children)
        await super()._fetch()

    async def _fetch_data(self) -> dict:
        name, fields, params = self._fetch_info()
        params.update(self._additional_fetch_params.copy())
        path = API_PATH[name].format(**fields)
        return await self._reddit.request(method="GET", params=params, path=path)

    def _fetch_info(self) -> tuple[str, dict[str, str], dict[str, int | str]]:
        return (
            "submission",
            {"id": self.id},
            {"limit": self.comment_limit, "sort": self.comment_sort},
        )

    def _replace_richtext_links(self, richtext_json: dict) -> None:
        parsed_media_types = {
            media_id: MEDIA_TYPE_MAPPING[value["e"]] for media_id, value in self.media_metadata.items()
        }

        for index, element in enumerate(richtext_json["document"][:]):
            element_items = element.get("c")
            if isinstance(element_items, str):
                assert element.get("e") in {"gif", "img", "video"}, (
                    "Unexpected richtext JSON schema. Please file a bug report with Async PRAW."
                )  # make sure this is an inline element
                continue  # pragma: no cover
            for item in element.get("c"):
                if item.get("e") == "link":
                    ids = set(parsed_media_types)
                    # remove extra bits from the url
                    url = item["u"].split("https://")[1].split("?")[0]
                    # the id is in the url somewhere, so we split by '/' and '.'
                    matched_id = ids.intersection(re.split(r"[./]", url))
                    if matched_id:
                        matched_id = matched_id.pop()
                        correct_element = {
                            "e": parsed_media_types[matched_id],
                            "id": matched_id,
                        }
                        if item.get("t") != item.get("u"):  # add caption if it exists
                            correct_element["c"] = item["t"]
                        richtext_json["document"][index] = correct_element

    def add_fetch_param(self, key: str, value: str) -> None:
        """Add a parameter to be used for the next fetch.

        :param key: The key of the fetch parameter.
        :param value: The value of the fetch parameter.

        For example, to fetch a submission with the ``rtjson`` attribute populated:

        .. code-block:: python

            submission = await reddit.submission("mcqjl8", fetch=False)
            submission.add_fetch_param("rtj", "all")
            await submission.load()
            print(submission.rtjson)

        """
        if (
            hasattr(self, "_fetched")
            and self._fetched
            and hasattr(self, "_reddit")
            and self._reddit.config.warn_additional_fetch_params
        ):
            warn(
                f"This {self.__class__.__name__.lower()} has already been fetched, so"
                " adding additional fetch parameters will not have any effect."
                f" Initialize the {self.__class__.__name__} instance with the parameter"
                " `fetch=False` to use additional fetch parameters.",
                stacklevel=2,
            )
        self._additional_fetch_params[key] = value

    async def crosspost(
        self,
        subreddit: asyncpraw.models.Subreddit,
        *,
        flair_id: str | None = None,
        flair_text: str | None = None,
        nsfw: bool = False,
        send_replies: bool = True,
        spoiler: bool = False,
        title: str | None = None,
    ) -> asyncpraw.models.Submission:
        """Crosspost the submission to a subreddit.

        .. note::

            Be aware you have to be subscribed to the target subreddit.

        :param subreddit: Name of the subreddit or :class:`.Subreddit` object to
            crosspost into.
        :param flair_id: The flair template to select (default: ``None``).
        :param flair_text: If the template's ``flair_text_editable`` value is ``True``,
            this value will set a custom text (default: ``None``).
        :param nsfw: Whether the submission should be marked NSFW (default: ``False``).
        :param send_replies: When ``True``, messages will be sent to the created
            submission's author when comments are made to the submission (default:
            ``True``).
        :param spoiler: Whether the submission should be marked as a spoiler (default:
            ``False``).
        :param title: Title of the submission. Will use this submission's title if
            ``None`` (default: ``None``).

        :returns: A :class:`.Submission` object for the newly created submission.

        Example usage:

        .. code-block:: python

            submission = await reddit.submission("5or86n")
            cross_post = await submission.crosspost("learnprogramming", send_replies=False)

        .. seealso::

            :meth:`.hide`

        """
        if title is None:
            title = self.title

        data = {
            "sr": str(subreddit),
            "title": title,
            "sendreplies": bool(send_replies),
            "kind": "crosspost",
            "crosspost_fullname": self.fullname,
            "nsfw": bool(nsfw),
            "spoiler": bool(spoiler),
        }
        for key, value in (("flair_id", flair_id), ("flair_text", flair_text)):
            if value is not None:
                data[key] = value

        return await self._reddit.post(API_PATH["submit"], data=data)

    async def hide(self, *, other_submissions: list[asyncpraw.models.Submission] | None = None) -> None:
        """Hide :class:`.Submission`.

        :param other_submissions: When provided, additionally hide this list of
            :class:`.Submission` instances as part of a single request (default:
            ``None``).

        Example usage:

        .. code-block:: python

            submission = await reddit.submission("5or86n", fetch=False)
            await submission.hide()

        .. seealso::

            :meth:`.unhide`

        """
        for submissions in self._chunk(chunk_size=50, other_submissions=other_submissions):
            await self._reddit.post(API_PATH["hide"], data={"id": submissions})

    async def mark_visited(self) -> None:
        """Mark submission as visited.

        This method requires a subscription to reddit premium.

        Example usage:

        .. code-block:: python

            submission = await reddit.submission("5or86n", fetch=False)
            await submission.mark_visited()

        """
        data = {"links": self.fullname}
        await self._reddit.post(API_PATH["store_visits"], data=data)

    async def unhide(self, *, other_submissions: list[asyncpraw.models.Submission] | None = None) -> None:
        """Unhide :class:`.Submission`.

        :param other_submissions: When provided, additionally unhide this list of
            :class:`.Submission` instances as part of a single request (default:
            ``None``).

        Example usage:

        .. code-block:: python

            submission = await reddit.submission("5or86n", fetch=False)
            await submission.unhide()

        .. seealso::

            :meth:`.hide`

        """
        for submissions in self._chunk(chunk_size=50, other_submissions=other_submissions):
            await self._reddit.post(API_PATH["unhide"], data={"id": submissions})


Subreddit._submission_class = Submission
