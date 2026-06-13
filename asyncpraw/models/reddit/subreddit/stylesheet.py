"""Provide the SubredditStylesheet class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from asyncpraw.const import API_PATH

if TYPE_CHECKING:
    import asyncpraw.models


class SubredditStylesheet:
    """Provides a set of stylesheet functions to a :class:`.Subreddit`.

    For example, to add the css data ``.test{color:blue}`` to the existing stylesheet:

    .. code-block:: python

        subreddit = await reddit.subreddit("test")
        stylesheet = await subreddit.stylesheet()
        stylesheet.stylesheet.stylesheet += ".test{color:blue}"
        await subreddit.stylesheet.update(stylesheet.stylesheet)

    """

    async def __call__(self) -> asyncpraw.models.Stylesheet:
        """Return the :class:`.Subreddit`'s stylesheet.

        To be used as:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            stylesheet = await subreddit.stylesheet()

        """
        url = API_PATH["about_stylesheet"].format(subreddit=self.subreddit)
        return await self.subreddit._reddit.get(url)

    def __init__(self, subreddit: asyncpraw.models.Subreddit) -> None:
        """Initialize a :class:`.SubredditStylesheet` instance.

        :param subreddit: The :class:`.Subreddit` associated with the stylesheet.

        An instance of this class is provided as:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            subreddit.stylesheet

        """
        self.subreddit = subreddit

    async def _update_structured_styles(self, style_data: dict[str, str | Any]) -> None:
        url = API_PATH["structured_styles"].format(subreddit=self.subreddit)
        await self.subreddit._reddit.patch(url, data=style_data)

    async def delete_banner(self) -> None:
        """Remove the current :class:`.Subreddit` (redesign) banner image.

        Succeeds even if there is no banner image.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            await subreddit.stylesheet.delete_banner()

        """
        data = {"bannerBackgroundImage": ""}
        await self._update_structured_styles(data)

    async def delete_banner_additional_image(self) -> None:
        """Remove the current :class:`.Subreddit` (redesign) banner additional image.

        Succeeds even if there is no additional image. Will also delete any configured
        hover image.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            await subreddit.stylesheet.delete_banner_additional_image()

        """
        data = {"bannerPositionedImage": "", "secondaryBannerPositionedImage": ""}
        await self._update_structured_styles(data)

    async def delete_banner_hover_image(self) -> None:
        """Remove the current :class:`.Subreddit` (redesign) banner hover image.

        Succeeds even if there is no hover image.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            await subreddit.stylesheet.delete_banner_hover_image()

        """
        data = {"secondaryBannerPositionedImage": ""}
        await self._update_structured_styles(data)

    async def delete_header(self) -> None:
        """Remove the current :class:`.Subreddit` header image.

        Succeeds even if there is no header image.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            await subreddit.stylesheet.delete_header()

        """
        url = API_PATH["delete_sr_header"].format(subreddit=self.subreddit)
        await self.subreddit._reddit.post(url)

    async def delete_image(self, name: str) -> None:
        """Remove the named image from the :class:`.Subreddit`.

        Succeeds even if the named image does not exist.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            await subreddit.stylesheet.delete_image("smile")

        """
        url = API_PATH["delete_sr_image"].format(subreddit=self.subreddit)
        await self.subreddit._reddit.post(url, data={"img_name": name})

    async def delete_mobile_banner(self) -> None:
        """Remove the current :class:`.Subreddit` (redesign) mobile banner.

        Succeeds even if there is no mobile banner.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            await subreddit.stylesheet.delete_banner_hover_image()

        """
        data = {"mobileBannerImage": ""}
        await self._update_structured_styles(data)

    async def delete_mobile_header(self) -> None:
        """Remove the current :class:`.Subreddit` mobile header.

        Succeeds even if there is no mobile header.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            await subreddit.stylesheet.delete_mobile_header()

        """
        url = API_PATH["delete_sr_header"].format(subreddit=self.subreddit)
        await self.subreddit._reddit.post(url)

    async def delete_mobile_icon(self) -> None:
        """Remove the current :class:`.Subreddit` mobile icon.

        Succeeds even if there is no mobile icon.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            await subreddit.stylesheet.delete_mobile_icon()

        """
        url = API_PATH["delete_sr_icon"].format(subreddit=self.subreddit)
        await self.subreddit._reddit.post(url)

    async def update(self, stylesheet: str, *, reason: str | None = None) -> None:
        """Update the :class:`.Subreddit`'s stylesheet.

        :param stylesheet: The CSS for the new stylesheet.
        :param reason: The reason for updating the stylesheet.

        For example:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            await subreddit.stylesheet.update("p { color: green; }", reason="color text green")

        """
        data = {"op": "save", "reason": reason, "stylesheet_contents": stylesheet}
        url = API_PATH["subreddit_stylesheet"].format(subreddit=self.subreddit)
        await self.subreddit._reddit.post(url, data=data)

    async def upload(self, media: asyncpraw.models.StylesheetImage, /, *, name: str) -> dict[str, str]:
        """Upload an image to the :class:`.Subreddit`.

        :param media: The :class:`.StylesheetImage` to upload.
        :param name: The name to use for the image. If an image already exists with the
            same name, it will be replaced.

        :returns: A dictionary containing a link to the uploaded image under the key
            ``img_src``.

        :raises: ``asyncprawcore.TooLarge`` if the overall request body is too large.
        :raises: :class:`.RedditAPIException` if there are other issues with the
            uploaded image. Unfortunately the exception info might not be very specific,
            so try through the website with the same image to see what the problem
            actually might be.

        For example:

        .. code-block:: python

            from asyncpraw.models import StylesheetImage

            subreddit = await reddit.subreddit("test")
            await subreddit.stylesheet.upload(StylesheetImage("img.png"), name="smile")

        """
        return await media._upload(self.subreddit, name=name, upload_type="img")

    async def upload_banner(self, media: asyncpraw.models.StylesheetAsset, /) -> None:
        """Upload an image for the :class:`.Subreddit`'s (redesign) banner image.

        :param media: The :class:`.StylesheetAsset` to upload.

        :raises: ``asyncprawcore.TooLarge`` if the overall request body is too large.
        :raises: :class:`.RedditAPIException` if there are other issues with the
            uploaded image. Unfortunately the exception info might not be very specific,
            so try through the website with the same image to see what the problem
            actually might be.

        For example:

        .. code-block:: python

            from asyncpraw.models import StylesheetAsset

            subreddit = await reddit.subreddit("test")
            await subreddit.stylesheet.upload_banner(StylesheetAsset("banner.png"))

        """
        image_type = "bannerBackgroundImage"
        image_url = await media._upload(self.subreddit, image_type=image_type)
        await self._update_structured_styles({image_type: image_url})

    async def upload_banner_additional_image(
        self,
        media: asyncpraw.models.StylesheetAsset,
        /,
        *,
        align: str | None = None,
    ) -> None:
        """Upload an image for the :class:`.Subreddit`'s (redesign) additional image.

        :param media: The :class:`.StylesheetAsset` to upload.
        :param align: Either ``"left"``, ``"centered"``, or ``"right"``. (default:
            ``"left"``).

        :raises: ``asyncprawcore.TooLarge`` if the overall request body is too large.
        :raises: :class:`.RedditAPIException` if there are other issues with the
            uploaded image. Unfortunately the exception info might not be very specific,
            so try through the website with the same image to see what the problem
            actually might be.

        For example:

        .. code-block:: python

            from asyncpraw.models import StylesheetAsset

            subreddit = await reddit.subreddit("test")
            await subreddit.stylesheet.upload_banner_additional_image(StylesheetAsset("banner.png"))

        """
        alignment = {}
        if align is not None:
            if align not in {"left", "centered", "right"}:
                msg = "'align' argument must be either 'left', 'centered', or 'right'"
                raise ValueError(msg)
            alignment["bannerPositionedImagePosition"] = align

        image_type = "bannerPositionedImage"
        image_url = await media._upload(self.subreddit, image_type=image_type)
        style_data = {image_type: image_url}
        if alignment:
            style_data.update(alignment)
        await self._update_structured_styles(style_data)

    async def upload_banner_hover_image(self, media: asyncpraw.models.StylesheetAsset, /) -> None:
        """Upload an image for the :class:`.Subreddit`'s (redesign) additional image.

        :param media: The :class:`.StylesheetAsset` to upload.

        Fails if the :class:`.Subreddit` does not have an additional image defined.

        :raises: ``asyncprawcore.TooLarge`` if the overall request body is too large.
        :raises: :class:`.RedditAPIException` if there are other issues with the
            uploaded image. Unfortunately the exception info might not be very specific,
            so try through the website with the same image to see what the problem
            actually might be.

        For example:

        .. code-block:: python

            from asyncpraw.models import StylesheetAsset

            subreddit = await reddit.subreddit("test")
            await subreddit.stylesheet.upload_banner_hover_image(StylesheetAsset("banner.png"))

        """
        image_type = "secondaryBannerPositionedImage"
        image_url = await media._upload(self.subreddit, image_type=image_type)
        await self._update_structured_styles({image_type: image_url})

    async def upload_header(self, media: asyncpraw.models.StylesheetImage, /) -> dict[str, str]:
        """Upload an image to be used as the :class:`.Subreddit`'s header image.

        :param media: The :class:`.StylesheetImage` to upload.

        :returns: A dictionary containing a link to the uploaded image under the key
            ``img_src``.

        :raises: ``asyncprawcore.TooLarge`` if the overall request body is too large.
        :raises: :class:`.RedditAPIException` if there are other issues with the
            uploaded image. Unfortunately the exception info might not be very specific,
            so try through the website with the same image to see what the problem
            actually might be.

        For example:

        .. code-block:: python

            from asyncpraw.models import StylesheetImage

            subreddit = await reddit.subreddit("test")
            await subreddit.stylesheet.upload_header(StylesheetImage("header.png"))

        """
        return await media._upload(self.subreddit, upload_type="header")

    async def upload_mobile_banner(self, media: asyncpraw.models.StylesheetAsset, /) -> None:
        """Upload an image for the :class:`.Subreddit`'s (redesign) mobile banner.

        :param media: The :class:`.StylesheetAsset` to upload.

        For example:

        .. code-block:: python

            from asyncpraw.models import StylesheetAsset

            subreddit = await reddit.subreddit("test")
            await subreddit.stylesheet.upload_mobile_banner(StylesheetAsset("banner.png"))

        Fails if the :class:`.Subreddit` does not have an additional image defined.

        :raises: ``prawcore.TooLarge`` if the overall request body is too large.
        :raises: :class:`.RedditAPIException` if there are other issues with the
            uploaded image. Unfortunately the exception info might not be very specific,
            so try through the website with the same image to see what the problem
            actually might be.

        """
        image_type = "mobileBannerImage"
        image_url = await media._upload(self.subreddit, image_type=image_type)
        await self._update_structured_styles({image_type: image_url})

    async def upload_mobile_header(self, media: asyncpraw.models.StylesheetImage, /) -> dict[str, str]:
        """Upload an image to be used as the :class:`.Subreddit`'s mobile header.

        :param media: The :class:`.StylesheetImage` to upload.

        :returns: A dictionary containing a link to the uploaded image under the key
            ``img_src``.

        :raises: ``asyncprawcore.TooLarge`` if the overall request body is too large.
        :raises: :class:`.RedditAPIException` if there are other issues with the
            uploaded image. Unfortunately the exception info might not be very specific,
            so try through the website with the same image to see what the problem
            actually might be.

        For example:

        .. code-block:: python

            from asyncpraw.models import StylesheetImage

            subreddit = await reddit.subreddit("test")
            await subreddit.stylesheet.upload_mobile_header(StylesheetImage("header.png"))

        """
        return await media._upload(self.subreddit, upload_type="banner")

    async def upload_mobile_icon(self, media: asyncpraw.models.StylesheetImage, /) -> dict[str, str]:
        """Upload an image to be used as the :class:`.Subreddit`'s mobile icon.

        :param media: The :class:`.StylesheetImage` to upload.

        :returns: A dictionary containing a link to the uploaded image under the key
            ``img_src``.

        :raises: ``asyncprawcore.TooLarge`` if the overall request body is too large.
        :raises: :class:`.RedditAPIException` if there are other issues with the
            uploaded image. Unfortunately the exception info might not be very specific,
            so try through the website with the same image to see what the problem
            actually might be.

        For example:

        .. code-block:: python

            from asyncpraw.models import StylesheetImage

            subreddit = await reddit.subreddit("test")
            await subreddit.stylesheet.upload_mobile_icon(StylesheetImage("icon.png"))

        """
        return await media._upload(self.subreddit, upload_type="icon")
