"""Provide the Emoji class."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ...const import API_PATH
from ...exceptions import ClientException
from ...util import _deprecate_args
from ..util import deprecate_lazy
from .base import RedditBase

if TYPE_CHECKING:  # pragma: no cover
    import asyncpraw


class Emoji(RedditBase):
    """An individual :class:`.Emoji` object.

    .. include:: ../../typical_attributes.rst

    ====================== =================================================
    Attribute              Description
    ====================== =================================================
    ``mod_flair_only``     Whether the emoji is restricted for mod use only.
    ``name``               The name of the emoji.
    ``post_flair_allowed`` Whether the emoji may appear in post flair.
    ``url``                The URL of the emoji image.
    ``user_flair_allowed`` Whether the emoji may appear in user flair.
    ====================== =================================================

    """

    STR_FIELD = "name"

    def __eq__(self, other: str | Emoji) -> bool:
        """Return whether the other instance equals the current."""
        if isinstance(other, str):
            return other == str(self)
        if isinstance(other, self.__class__):
            return str(self) == str(other) and other.subreddit == self.subreddit
        return super().__eq__(other)

    def __hash__(self) -> int:
        """Return the hash of the current instance."""
        return hash(self.__class__.__name__) ^ hash(str(self)) ^ hash(self.subreddit)

    def __init__(
        self,
        reddit: asyncpraw.Reddit,
        subreddit: asyncpraw.models.Subreddit,
        name: str,
        _data: dict[str, Any] | None = None,
    ):
        """Initialize an :class:`.Emoji` instance."""
        self.name = name
        self.subreddit = subreddit
        super().__init__(reddit, _data=_data)

    async def _fetch(self):
        async for emoji in self.subreddit.emoji:
            if emoji.name == self.name:
                self.__dict__.update(emoji.__dict__)
                await super()._fetch()
                return
        msg = f"r/{self.subreddit} does not have the emoji {self.name}"
        raise ClientException(msg)

    async def delete(self):
        """Delete an emoji from this subreddit by :class:`.Emoji`.

        To delete ``"emoji"`` as an emoji on r/test try:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            emoji = await subreddit.emoji.get_emoji("emoji")
            await emoji.delete()

        """
        url = API_PATH["emoji_delete"].format(
            emoji_name=self.name, subreddit=self.subreddit
        )
        await self._reddit.delete(url)

    @_deprecate_args("mod_flair_only", "post_flair_allowed", "user_flair_allowed")
    async def update(
        self,
        *,
        mod_flair_only: bool | None = None,
        post_flair_allowed: bool | None = None,
        user_flair_allowed: bool | None = None,
    ):
        """Update the permissions of an emoji in this subreddit.

        :param mod_flair_only: Indicate whether the emoji is restricted to mod use only.
            Respects pre-existing settings if not provided.
        :param post_flair_allowed: Indicate whether the emoji may appear in post flair.
            Respects pre-existing settings if not provided.
        :param user_flair_allowed: Indicate whether the emoji may appear in user flair.
            Respects pre-existing settings if not provided.

        .. note::

            In order to retain pre-existing values for those that are not explicitly
            passed, a network request is issued. To avoid that network request,
            explicitly provide all values.

        To restrict the emoji ``"emoji"`` in r/test to mod use only, try:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            emoji = await subreddit.emoji.get_emoji("emoji")
            await emoji.update(mod_flair_only=True)

        """
        locals_reference = locals()
        mapping = {
            attribute: locals_reference[attribute]
            for attribute in (
                "mod_flair_only",
                "post_flair_allowed",
                "user_flair_allowed",
            )
        }
        if all(value is None for value in mapping.values()):
            msg = "At least one attribute must be provided"
            raise TypeError(msg)

        data = {"name": self.name}
        for attribute, value in mapping.items():
            if value is None:
                value = getattr(self, attribute)  # noqa: PLW2901
            data[attribute] = value
        url = API_PATH["emoji_update"].format(subreddit=self.subreddit)
        await self._reddit.post(url, data=data)
        for attribute, value in data.items():
            setattr(self, attribute, value)


class SubredditEmoji:
    """Provides a set of functions to a :class:`.Subreddit` for emoji."""

    async def __aiter__(self) -> list[Emoji]:
        """Return a list of :class:`.Emoji` for the subreddit.

        This method is to be used to discover all emoji for a subreddit:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            async for emoji in subreddit.emoji:
                print(emoji)

        """
        response = await self._reddit.get(
            API_PATH["emoji_list"].format(subreddit=self.subreddit)
        )
        subreddit_keys = [
            key
            for key in response
            if key.startswith(self._reddit.config.kinds["subreddit"])
        ]
        assert len(subreddit_keys) == 1
        for emoji_name, emoji_data in response[subreddit_keys[0]].items():
            yield Emoji(self._reddit, self.subreddit, emoji_name, _data=emoji_data)

    def __init__(self, subreddit: asyncpraw.models.Subreddit):
        """Initialize a :class:`.SubredditEmoji` instance.

        :param subreddit: The subreddit whose emoji are affected.

        """
        self.subreddit = subreddit
        self._reddit = subreddit._reddit

    async def add(
        self,
        *,
        image_path: str,
        mod_flair_only: bool | None = None,
        name: str,
        post_flair_allowed: bool | None = None,
        user_flair_allowed: bool | None = None,
    ) -> Emoji:
        """Add an emoji to this subreddit.

        :param image_path: A path to a jpeg or png image.
        :param mod_flair_only: When provided, indicate whether the emoji is restricted
            to mod use only (default: ``None``).
        :param name: The name of the emoji.
        :param post_flair_allowed: When provided, indicate whether the emoji may appear
            in post flair (default: ``None``).
        :param user_flair_allowed: When provided, indicate whether the emoji may appear
            in user flair (default: ``None``).

        :returns: The :class:`.Emoji` added.

        To add ``"emoji"`` to r/test try:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            await subreddit.emoji.add(name="emoji", image_path="emoji.png")

        """
        file = Path(image_path)
        data = {
            "filepath": file.name,
            "mimetype": "image/jpeg",
        }
        if image_path.lower().endswith(".png"):
            data["mimetype"] = "image/png"
        url = API_PATH["emoji_lease"].format(subreddit=self.subreddit)

        # until we learn otherwise, assume this request always succeeds
        response = await self._reddit.post(url, data=data)
        upload_lease = response["s3UploadLease"]
        upload_data = {item["name"]: item["value"] for item in upload_lease["fields"]}
        upload_url = f"https:{upload_lease['action']}"

        # TODO(@LilSpazJoekp): This is a blocking operation. It should be made async.
        with file.open("rb") as image:  # noqa: ASYNC230
            upload_data["file"] = image
            async with self._reddit._core._requestor.request(
                "POST", upload_url, data=upload_data
            ) as response:
                response.raise_for_status()

        data = {
            "mod_flair_only": mod_flair_only,
            "name": name,
            "post_flair_allowed": post_flair_allowed,
            "s3_key": upload_data["key"],
            "user_flair_allowed": user_flair_allowed,
        }
        url = API_PATH["emoji_upload"].format(subreddit=self.subreddit)
        await self._reddit.post(url, data=data)
        return Emoji(self._reddit, self.subreddit, name)

    @deprecate_lazy
    async def get_emoji(self, name: str, fetch: bool = True, **_: Any) -> Emoji:
        """Return the :class:`.Emoji` for the subreddit named ``name``.

        :param name: The name of the emoji.
        :param fetch: Determines if Async PRAW will fetch the object (default:
            ``True``).

        This method is to be used to fetch a specific emoji url, like so:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            emoji = await subreddit.emoji.get_emoji("emoji")
            print(emoji)

        If you don't need the object fetched right away (e.g., to utilize a class
        method) you can do:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            emoji = await subreddit.emoji.get_emoji("emoji", fetch=False)
            await emoji.delete()

        """
        emoji = Emoji(self._reddit, self.subreddit, name)
        if fetch:
            await emoji._fetch()
        return emoji
