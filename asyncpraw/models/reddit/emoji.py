"""Provide the Emoji class."""
import os
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from ...const import API_PATH
from ...exceptions import ClientException
from .base import RedditBase

if TYPE_CHECKING:  # pragma: no cover
    from .... import asyncpraw


class Emoji(RedditBase):
    """An individual Emoji object.

    **Typical Attributes**

    This table describes attributes that typically belong to objects of this class.
    Since attributes are dynamically provided (see
    :ref:`determine-available-attributes-of-an-object`), there is not a guarantee that
    these attributes will always be present, nor is this list necessarily comprehensive.

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

    def __eq__(self, other: Union[str, "Emoji"]) -> bool:
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
        reddit: "asyncpraw.Reddit",
        subreddit: "asyncpraw.models.Subreddit",
        name: str,
        _data: Optional[Dict[str, Any]] = None,
    ):
        """Construct an instance of the Emoji object."""
        self.name = name
        self.subreddit = subreddit
        super().__init__(reddit, _data=_data)

    async def _fetch(self):
        async for emoji in self.subreddit.emoji:
            if emoji.name == self.name:
                self.__dict__.update(emoji.__dict__)
                self._fetched = True
                return
        raise ClientException(f"r/{self.subreddit} does not have the emoji {self.name}")

    async def delete(self):
        """Delete an emoji from this subreddit by Emoji.

        To delete ``"test"`` as an emoji on the subreddit ``"praw_test"`` try:

        .. code-block:: python

            subreddit = await reddit.subreddit("praw_test")
            emoji = await subreddit.emoji.get_emoji("test")
            await emoji.delete()

        """
        url = API_PATH["emoji_delete"].format(
            emoji_name=self.name, subreddit=self.subreddit
        )
        await self._reddit.delete(url)

    async def update(
        self,
        mod_flair_only: Optional[bool] = None,
        post_flair_allowed: Optional[bool] = None,
        user_flair_allowed: Optional[bool] = None,
    ):
        """Update the permissions of an emoji in this subreddit.

        :param mod_flair_only: (boolean) Indicate whether the emoji is restricted to mod
            use only. Respects pre-existing settings if not provided.
        :param post_flair_allowed: (boolean) Indicate whether the emoji may appear in
            post flair. Respects pre-existing settings if not provided.
        :param user_flair_allowed: (boolean) Indicate whether the emoji may appear in
            user flair. Respects pre-existing settings if not provided.

        .. note::

            In order to retain pre-existing values for those that are not explicitly
            passed, a network request is issued. To avoid that network request,
            explicitly provide all values.

        To restrict the emoji ``test`` in subreddit ``wowemoji`` to mod use only, try:

        .. code-block:: python

            subreddit = await reddit.subreddit("wowemoji")
            emoji = await subreddit.emoji.get_emoji("test")
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
            raise TypeError("At least one attribute must be provided")

        data = {"name": self.name}
        for attribute, value in mapping.items():
            if value is None:
                value = getattr(self, attribute)
            data[attribute] = value
        url = API_PATH["emoji_update"].format(subreddit=self.subreddit)
        await self._reddit.post(url, data=data)
        for attribute, value in data.items():
            setattr(self, attribute, value)


class SubredditEmoji:
    """Provides a set of functions to a Subreddit for emoji."""

    async def get_emoji(self, name: str, lazy: bool = False) -> Emoji:
        """Return the Emoji for the subreddit named ``name``.

        :param name: The name of the emoji
        :param lazy: If True, object is loaded lazily (default: False)

        This method is to be used to fetch a specific emoji url, like so:

        .. code-block:: python

            subreddit = await reddit.subreddit("praw_test")
            emoji = await subreddit.emoji.get_emoji("test")
            print(emoji)

        If you don't need the object fetched right away (e.g., to utilize a class
        method) you can do:

        .. code-block:: python

            subreddit = await reddit.subreddit("praw_test")
            emoji = await subreddit.emoji.get_emoji("test", lazy=True)
            await emoji.delete()

        """
        emoji = Emoji(self._reddit, self.subreddit, name)
        if not lazy:
            await emoji._fetch()
        return emoji

    def __init__(self, subreddit: "asyncpraw.models.Subreddit"):
        """Create a SubredditEmoji instance.

        :param subreddit: The subreddit whose emoji are affected.

        """
        self.subreddit = subreddit
        self._reddit = subreddit._reddit

    async def __aiter__(self) -> List[Emoji]:
        """Return a list of Emoji for the subreddit.

        This method is to be used to discover all emoji for a subreddit:

        .. code-block:: python

            subreddit = await reddit.subreddit("praw_test")
            async for emoji in subreddit.emoji:
                print(emoji)

        """
        response = await self._reddit.get(
            API_PATH["emoji_list"].format(subreddit=self.subreddit)
        )
        subreddit_keys = [
            key
            for key in response.keys()
            if key.startswith(self._reddit.config.kinds["subreddit"])
        ]
        assert len(subreddit_keys) == 1
        for emoji_name, emoji_data in response[subreddit_keys[0]].items():
            yield Emoji(self._reddit, self.subreddit, emoji_name, _data=emoji_data)

    async def add(
        self,
        name: str,
        image_path: str,
        mod_flair_only: Optional[bool] = None,
        post_flair_allowed: Optional[bool] = None,
        user_flair_allowed: Optional[bool] = None,
    ) -> Emoji:
        """Add an emoji to this subreddit.

        :param name: The name of the emoji
        :param image_path: A path to a jpeg or png image.
        :param mod_flair_only: (boolean) When provided, indicate whether the emoji is
            restricted to mod use only. (Default: ``None``)
        :param post_flair_allowed: (boolean) When provided, indicate whether the emoji
            may appear in post flair. (Default: ``None``)
        :param user_flair_allowed: (boolean) When provided, indicate whether the emoji
            may appear in user flair. (Default: ``None``)

        :returns: The Emoji added.

        To add ``test`` to the subreddit ``praw_test`` try:

        .. code-block:: python

            subreddit = await reddit.subreddit("praw_test")
            await subreddit.emoji.add("test", "test.png")

        """
        data = {
            "filepath": os.path.basename(image_path),
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

        with open(image_path, "rb") as image:
            upload_data["file"] = image
            response = await self._reddit._core._requestor._http.post(
                upload_url, data=upload_data
            )
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
