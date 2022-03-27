"""Provide classes related to widgets."""

import os.path
from json import JSONEncoder, dumps
from typing import TYPE_CHECKING, Any, Dict, List, Union

from ...const import API_PATH
from ...util.cache import cachedproperty
from ..base import AsyncPRAWBase
from ..list.base import BaseList

if TYPE_CHECKING:  # pragma: no cover
    import asyncpraw

WidgetType = Union[
    "asyncpraw.models.ButtonWidget",
    "asyncpraw.models.Calendar",
    "asyncpraw.models.CommunityList",
    "asyncpraw.models.CustomWidget",
    "asyncpraw.models.IDCard",
    "asyncpraw.models.ImageWidget",
    "asyncpraw.models.Menu",
    "asyncpraw.models.ModeratorsWidget",
    "asyncpraw.models.PostFlairWidget",
    "asyncpraw.models.RulesWidget",
    "asyncpraw.models.TextArea",
    "asyncpraw.models.Widget",
]


class Button(AsyncPRAWBase):
    """Class to represent a single button inside a :class:`.ButtonWidget`.

    .. include:: ../../typical_attributes.rst

    ============== =====================================================================
    Attribute      Description
    ============== =====================================================================
    ``color``      The hex color used to outline the button.
    ``fillColor``  The hex color for the background of the button.
    ``height``     Image height. Only present on image buttons.
    ``hoverState`` A ``dict`` describing the state of the button when hovered over.
                   Optional.
    ``kind``       Either ``"text"`` or ``"image"``.
    ``linkUrl``    A link that can be visited by clicking the button. Only present on
                   image buttons.
    ``text``       The text displayed on the button.
    ``textColor``  The hex color for the text of the button.
    ``url``        - If the button is a text button, a link that can be visited by
                     clicking the button.
                   - If the button is an image button, the URL of a Reddit-hosted image.
    ``width``      Image width. Only present on image buttons.
    ============== =====================================================================

    """


class CalendarConfiguration(AsyncPRAWBase):
    """Class to represent the configuration of a :class:`.Calendar`.

    .. include:: ../../typical_attributes.rst

    =================== ==================================================
    Attribute           Description
    =================== ==================================================
    ``numEvents``       The number of events to display on the calendar.
    ``showDate``        Whether or not to show the dates of events.
    ``showDescription`` Whether or not to show the descriptions of events.
    ``showLocation``    Whether or not to show the locations of events.
    ``showTime``        Whether or not to show the times of events.
    ``showTitle``       Whether or not to show the titles of events.
    =================== ==================================================

    """


class Hover(AsyncPRAWBase):
    """Class to represent the hover data for a :class:`.ButtonWidget`.

    These values will take effect when the button is hovered over (the user moves their
    cursor so it's on top of the button).

    .. include:: ../../typical_attributes.rst

    ============= =====================================================================
    Attribute     Description
    ============= =====================================================================
    ``color``     The hex color used to outline the button.
    ``fillColor`` The hex color for the background of the button.
    ``textColor`` The hex color for the text of the button.
    ``height``    Image height. Only present on image buttons.
    ``kind``      Either ``text`` or ``image``.
    ``text``      The text displayed on the button.
    ``url``       - If the button is a text button, a link that can be visited by
                    clicking the button.
                  - If the button is an image button, the URL of a Reddit-hosted image.
    ``width``     Image width. Only present on image buttons.
    ============= =====================================================================

    """


class Image(AsyncPRAWBase):
    """Class to represent an image that's part of a :class:`.ImageWidget`.

    .. include:: ../../typical_attributes.rst

    =========== =================================================
    Attribute   Description
    =========== =================================================
    ``height``  Image height.
    ``linkUrl`` A link that can be visited by clicking the image.
    ``url``     The URL of the (Reddit-hosted) image.
    ``width``   Image width.
    =========== =================================================

    """


class ImageData(AsyncPRAWBase):
    """Class for image data that's part of a :class:`.CustomWidget`.

    .. include:: ../../typical_attributes.rst

    ========== =========================================
    Attribute  Description
    ========== =========================================
    ``height`` The image height.
    ``name``   The image name.
    ``url``    The URL of the image on Reddit's servers.
    ``width``  The image width.
    ========== =========================================

    """


class MenuLink(AsyncPRAWBase):
    """Class to represent a single link inside a :class:`.Menu` or :class:`.Submenu`.

    .. include:: ../../typical_attributes.rst

    ========= ====================================
    Attribute Description
    ========= ====================================
    ``text``  The text of the menu link.
    ``url``   The URL that the menu item links to.
    ========= ====================================

    """


class Styles(AsyncPRAWBase):
    """Class to represent the style information of a widget.

    .. include:: ../../typical_attributes.rst

    =================== ========================================================
    Attribute           Description
    =================== ========================================================
    ``backgroundColor`` The background color of a widget, given as a hexadecimal
                        (``0x######``).
    ``headerColor``     The header color of a widget, given as a hexadecimal
                        (``0x######``).
    =================== ========================================================

    """


class Submenu(BaseList):
    r"""Class to represent a submenu of links inside a :class:`.Menu`.

    .. include:: ../../typical_attributes.rst

    ============ ======================================================================
    Attribute    Description
    ============ ======================================================================
    ``children`` A list of the :class:`.MenuLink`\ s in this submenu. Can be iterated
                 over by iterating over the :class:`.Submenu` (e.g., ``for menu_link in
                 submenu``).
    ``text``     The name of the submenu.
    ============ ======================================================================

    """

    CHILD_ATTRIBUTE = "children"


class SubredditWidgets(AsyncPRAWBase):
    """Class to represent a :class:`.Subreddit`'s widgets.

    Create an instance like so:

    .. code-block:: python

        subreddit = await reddit.subreddit("test")
        widgets = subreddit.widgets

    Data will be lazy-loaded. By default, Async PRAW will not request progressively
    loading images from Reddit. To enable this, instantiate a :class:`.SubredditWidgets`
    object via :meth:`~.Subreddit.widgets`, then set the attribute
    ``progressive_images`` to ``True`` before performing any action that would result in
    a network request.

    .. code-block:: python

        subreddit = await reddit.subreddit("test")
        widgets = subreddit.widgets
        widgets.progressive_images = True
        async for widget in widgets.sidebar():
            # do something
            ...

    Access a :class:`.Subreddit`'s widgets with the following attributes:

    .. code-block:: python

        print(await widgets.id_card())
        print(await widgets.moderators_widget())
        print([widget async for widget in widgets.sidebar()])
        print([widget async for widget in widgets.topbar()])

    The attribute :attr:`.id_card` contains the :class:`.Subreddit`'s ID card, which
    displays information like the number of subscribers.

    The attribute :attr:`.moderators_widget` contains the :class:`.Subreddit`'s
    moderators widget, which lists the moderators of the subreddit.

    The attribute :attr:`.sidebar` contains a list of widgets which make up the sidebar
    of the subreddit.

    The attribute :attr:`.topbar` contains a list of widgets which make up the top bar
    of the subreddit.

    To edit a :class:`.Subreddit`'s widgets, use :attr:`~.SubredditWidgets.mod`. For
    example:

    .. code-block:: python

        await widgets.mod.add_text_area(
            "My title",
            "**bold text**",
            {"backgroundColor": "#FFFF66", "headerColor": "#3333EE"},
        )

    For more information, see :class:`.SubredditWidgetsModeration`.

    To edit a particular widget, use ``.mod`` on the widget. For example:

    .. code-block:: python

        async for widget in widgets.sidebar():
            await widget.mod.update(shortName="Exciting new name")

    For more information, see :class:`.WidgetModeration`.

    **Currently available widgets**:

    - :class:`.ButtonWidget`
    - :class:`.Calendar`
    - :class:`.CommunityList`
    - :class:`.CustomWidget`
    - :class:`.IDCard`
    - :class:`.ImageWidget`
    - :class:`.Menu`
    - :class:`.ModeratorsWidget`
    - :class:`.PostFlairWidget`
    - :class:`.RulesWidget`
    - :class:`.TextArea`

    """

    async def id_card(self) -> "asyncpraw.models.IDCard":
        """Get this :class:`.Subreddit`'s :class:`.IDCard` widget."""
        items = await self.items()
        return items[self.layout["idCardWidget"]]

    async def items(self) -> Dict[str, "asyncpraw.models.Widget"]:
        """Get this :class:`.Subreddit`'s widgets as a dict from ID to widget."""
        if self._items is None:
            if not self._raw_items:
                await self._fetch()
            self._items = {}
            for item_name, data in self._raw_items.items():
                data["subreddit"] = self.subreddit
                self._items[item_name] = self._reddit._objector.objectify(data)
        return self._items

    @cachedproperty
    def mod(self) -> "asyncpraw.models.SubredditWidgetsModeration":
        """Get an instance of :class:`.SubredditWidgetsModeration`.

        .. note::

            Using any of the methods of :class:`.SubredditWidgetsModeration` will likely
            result in the data of this :class:`.SubredditWidgets` being outdated. To
            re-sync, call :meth:`.refresh`.

        """
        return SubredditWidgetsModeration(self.subreddit, self._reddit)

    async def moderators_widget(self) -> "asyncpraw.models.ModeratorsWidget":
        """Get this :class:`.Subreddit`'s :class:`.ModeratorsWidget`."""
        items = await self.items()
        return items[self.layout["moderatorWidget"]]

    async def sidebar(self) -> List["asyncpraw.models.Widget"]:
        r"""Get a list of :class:`.Widget`\ s that make up the sidebar."""
        items = await self.items()
        for widget in self.layout["sidebar"]["order"]:
            yield items[widget]

    async def topbar(self) -> List["asyncpraw.models.Menu"]:
        r"""Get a list of :class:`.Widget`\ s that make up the top bar."""
        items = await self.items()
        for widget in self.layout["topbar"]["order"]:
            yield items[widget]

    async def refresh(self):
        """Refresh the :class:`.Subreddit`'s widgets.

        By default, Async PRAW will not request progressively loading images from
        Reddit. To enable this, set the attribute ``progressive_images`` to ``True``
        prior to calling ``refresh()``.

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            widgets = subreddit.widgets
            widgets.progressive_images = True
            await widgets.refresh()

        """
        await self._fetch()

    def __getattr__(self, attr: str) -> Any:
        """Return the value of `attr`."""
        if not attr.startswith("_") and not self._fetched:
            raise AttributeError(
                f"{self.__class__.__name__!r} object has no attribute {attr!r}, did you"
                " forget to run '.refresh()'?"
            )
        raise AttributeError(  # pragma: no cover; I have no idea how to cover this
            f"{self.__class__.__name__!r} object has no attribute {attr!r}, did you"
            " forget to run '.refresh()'?"
        )

    def __init__(self, subreddit: "asyncpraw.models.Subreddit"):
        """Initialize a :class:`.SubredditWidgets` instance.

        :param subreddit: The :class:`.Subreddit` the widgets belong to.

        """
        self._raw_items = None
        self._items = None
        self._fetched = False
        self.subreddit = subreddit
        self.progressive_images = False

        super().__init__(subreddit._reddit, {})

    def __repr__(self) -> str:
        """Return an object initialization representation of the instance."""
        return f"SubredditWidgets(subreddit={self.subreddit!r})"

    async def _fetch(self):
        data = await self._reddit.get(
            API_PATH["widgets"].format(subreddit=self.subreddit),
            params={"progressive_images": self.progressive_images},
        )

        self._raw_items = data.pop("items")
        self._items = None
        super().__init__(self.subreddit._reddit, data)

        self._fetched = True


class SubredditWidgetsModeration:
    """Class for moderating a :class:`.Subreddit`'s widgets.

    Get an instance of this class from :attr:`.SubredditWidgets.mod`.

    Example usage:

    .. code-block:: python

        styles = {"backgroundColor": "#FFFF66", "headerColor": "#3333EE"}
        subreddit = await reddit.subreddit("test")
        await subreddit.widgets.mod.add_text_area("My title", "**bold text**", styles)

    .. note::

        To use this class's methods, the authenticated user must be a moderator with
        appropriate permissions.

    """

    def __init__(
        self, subreddit: "asyncpraw.models.Subreddit", reddit: "asyncpraw.Reddit"
    ):
        """Initialize a :class:`.SubredditWidgetsModeration` instance."""
        self._subreddit = subreddit
        self._reddit = reddit

    async def _create_widget(self, payload: Dict[str, Any]) -> WidgetType:
        path = API_PATH["widget_create"].format(subreddit=self._subreddit)
        widget = await self._reddit.post(
            path, data={"json": dumps(payload, cls=WidgetEncoder)}
        )
        widget.subreddit = self._subreddit
        return widget

    async def add_button_widget(
        self,
        short_name: str,
        description: str,
        buttons: List[
            Dict[str, Union[Dict[str, str], str, int, Dict[str, Union[str, int]]]]
        ],
        styles: Dict[str, str],
        **other_settings,
    ) -> "asyncpraw.models.ButtonWidget":
        r"""Add and return a :class:`.ButtonWidget`.

        :param short_name: A name for the widget, no longer than 30 characters.
        :param description: Markdown text to describe the widget.
        :param buttons: A list of ``dict``\ s describing buttons, as specified in
            `Reddit docs`_. As of this writing, the format is:

            Each button is either a text button or an image button. A text button looks
            like this:

            .. code-block:: text

                {
                    "kind": "text",
                    "text": a string no longer than 30 characters,
                    "url": a valid URL,
                    "color": a 6-digit rgb hex color, e.g., `#AABBCC`,
                    "textColor": a 6-digit rgb hex color, e.g., `#AABBCC`,
                    "fillColor": a 6-digit rgb hex color, e.g., `#AABBCC`,
                    "hoverState": {...}
                }

            An image button looks like this:

            .. code-block:: text

                {
                    "kind": "image",
                    "text": a string no longer than 30 characters,
                    "linkUrl": a valid URL,
                    "url": a valid URL of a Reddit-hosted image,
                    "height": an integer,
                    "width": an integer,
                    "hoverState": {...}
                }

            Both types of buttons have the field ``hoverState``. The field does not have
            to be included (it is optional). If it is included, it can be one of two
            types: ``"text"`` or ``"image"``. A text ``hoverState`` looks like this:

            .. code-block:: text

                {
                    "kind": "text",
                    "text": a string no longer than 30 characters,
                    "color": a 6-digit rgb hex color, e.g., `#AABBCC`,
                    "textColor": a 6-digit rgb hex color, e.g., `#AABBCC`,
                    "fillColor": a 6-digit rgb hex color, e.g., `#AABBCC`
                }

            An image ``hoverState`` looks like this:

            .. code-block:: text

                {
                    "kind": "image",
                    "url": a valid URL of a Reddit-hosted image,
                    "height": an integer,
                    "width": an integer
                }

            .. note::

                The method :meth:`.upload_image` can be used to upload images to Reddit
                for a ``url`` field that holds a Reddit-hosted image.

            .. note::

                An image ``hoverState`` may be paired with a text widget, and a text
                ``hoverState`` may be paired with an image widget.

        :param styles: A ``dict`` with keys ``backgroundColor`` and ``headerColor``, and
            values of hex colors. For example, ``{"backgroundColor": "#FFFF66",
            "headerColor": "#3333EE"}``.

        :returns: The created :class:`.ButtonWidget`.

        .. _reddit docs: https://www.reddit.com/dev/api#POST_api_widget

        Example usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            widget_moderation = subreddit.widgets.mod
            my_image = await widget_moderation.upload_image("/path/to/pic.jpg")
            buttons = [
                {
                    "kind": "text",
                    "text": "View source",
                    "url": "https://github.com/asyncpraw-dev/asyncpraw",
                    "color": "#FF0000",
                    "textColor": "#00FF00",
                    "fillColor": "#0000FF",
                    "hoverState": {
                        "kind": "text",
                        "text": "ecruos weiV",
                        "color": "#FFFFFF",
                        "textColor": "#000000",
                        "fillColor": "#0000FF",
                    },
                },
                {
                    "kind": "image",
                    "text": "View documentation",
                    "linkUrl": "https://asyncpraw.readthedocs.io",
                    "url": my_image,
                    "height": 200,
                    "width": 200,
                    "hoverState": {"kind": "image", "url": my_image, "height": 200, "width": 200},
                },
            ]
            styles = {"backgroundColor": "#FFFF66", "headerColor": "#3333EE"}
            new_widget = await widget_moderation.add_button_widget(
                "Things to click", "Click some of these *cool* links!", buttons, styles
            )

        """
        button_widget = {
            "buttons": buttons,
            "description": description,
            "kind": "button",
            "shortName": short_name,
            "styles": styles,
        }
        button_widget.update(other_settings)
        return await self._create_widget(button_widget)

    async def add_calendar(
        self,
        short_name: str,
        google_calendar_id: str,
        requires_sync: bool,
        configuration: Dict[str, Union[bool, int]],
        styles: Dict[str, str],
        **other_settings,
    ) -> "asyncpraw.models.Calendar":
        """Add and return a :class:`.Calendar` widget.

        :param short_name: A name for the widget, no longer than 30 characters.
        :param google_calendar_id: An email-style calendar ID. To share a Google
            Calendar, make it public, then find the "Calendar ID."
        :param requires_sync: A ``bool``.
        :param configuration: A ``dict`` as specified in `Reddit docs`_.

            For example:

            .. code-block:: python

                {
                    "numEvents": 10,
                    "showDate": True,
                    "showDescription": False,
                    "showLocation": False,
                    "showTime": True,
                    "showTitle": True,
                }

        :param styles: A ``dict`` with keys ``backgroundColor`` and ``headerColor``, and
            values of hex colors. For example, ``{"backgroundColor": "#FFFF66",
            "headerColor": "#3333EE"}``.

        :returns: The created :class:`.Calendar`.

        .. _reddit docs: https://www.reddit.com/dev/api#POST_api_widget

        Example usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            widget_moderation = subreddit.widgets.mod
            styles = {"backgroundColor": "#FFFF66", "headerColor": "#3333EE"}
            config = {
                "numEvents": 10,
                "showDate": True,
                "showDescription": False,
                "showLocation": False,
                "showTime": True,
                "showTitle": True,
            }
            cal_id = "y6nm89jy427drk8l71w75w9wjn@group.calendar.google.com"
            new_widget = await widget_moderation.add_calendar(
                "Upcoming Events", cal_id, True, config, styles
            )

        """
        calendar = {
            "shortName": short_name,
            "googleCalendarId": google_calendar_id,
            "requiresSync": requires_sync,
            "configuration": configuration,
            "styles": styles,
            "kind": "calendar",
        }
        calendar.update(other_settings)
        return await self._create_widget(calendar)

    async def add_community_list(
        self,
        short_name: str,
        data: List[Union[str, "asyncpraw.models.Subreddit"]],
        styles: Dict[str, str],
        description: str = "",
        **other_settings,
    ) -> "asyncpraw.models.CommunityList":
        """Add and return a :class:`.CommunityList` widget.

        :param short_name: A name for the widget, no longer than 30 characters.
        :param data: A list of subreddits. Subreddits can be represented as ``str`` or
            as :class:`.Subreddit`. These types may be mixed within the list.
        :param styles: A ``dict`` with keys ``"backgroundColor"`` and ``"headerColor"``,
            and values of hex colors. For example, ``{"backgroundColor": "#FFFF66",
            "headerColor": "#3333EE"}``.
        :param description: A ``str`` containing Markdown (default: ``""``).

        :returns: The created :class:`.CommunityList`.

        Example usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            widget_moderation = subreddit.widgets.mod
            styles = {"backgroundColor": "#FFFF66", "headerColor": "#3333EE"}
            new_subreddit = await reddit.subreddit("test")
            subreddits = ["learnpython", new_subreddit]
            new_widget = await widget_moderation.add_community_list(
                "My fav subs", subreddits, styles, "description"
            )

        """
        community_list = {
            "data": data,
            "kind": "community-list",
            "shortName": short_name,
            "styles": styles,
            "description": description,
        }
        community_list.update(other_settings)
        return await self._create_widget(community_list)

    async def add_custom_widget(
        self,
        short_name: str,
        text: str,
        css: str,
        height: int,
        image_data: List[Dict[str, Union[str, int]]],
        styles: Dict[str, str],
        **other_settings,
    ) -> "asyncpraw.models.CustomWidget":
        r"""Add and return a :class:`.CustomWidget`.

        :param short_name: A name for the widget, no longer than 30 characters.
        :param text: The Markdown text displayed in the widget.
        :param css: The CSS for the widget, no longer than 100000 characters.

            .. note::

                As of this writing, Reddit will not accept empty CSS. If you wish to
                create a custom widget without CSS, consider using ``"/**/"`` (an empty
                comment) as your CSS.

        :param height: The height of the widget, between 50 and 500.
        :param image_data: A list of ``dict``\ s as specified in `Reddit docs`_. Each
            ``dict`` represents an image and has the key ``"url"`` which maps to the URL
            of an image hosted on Reddit's servers. Images should be uploaded using
            :meth:`.upload_image`.

            For example:

            .. code-block:: python

                [
                    {
                        "url": "https://some.link",  # from upload_image()
                        "width": 600,
                        "height": 450,
                        "name": "logo",
                    },
                    {
                        "url": "https://other.link",  # from upload_image()
                        "width": 450,
                        "height": 600,
                        "name": "icon",
                    },
                ]

        :param styles: A ``dict`` with keys ``backgroundColor`` and ``headerColor``, and
            values of hex colors. For example, ``{"backgroundColor": "#FFFF66",
            "headerColor": "#3333EE"}``.

        :returns: The created :class:`.CustomWidget`.

        .. _reddit docs: https://www.reddit.com/dev/api#POST_api_widget

        Example usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            widget_moderation = subreddit.widgets.mod
            image_paths = ["/path/to/image1.jpg", "/path/to/image2.png"]
            image_urls = [widget_moderation.upload_image(img_path) for img_path in image_paths]
            image_dicts = [
                {"width": 600, "height": 450, "name": "logo", "url": image_urls[0]},
                {"width": 450, "height": 600, "name": "icon", "url": image_urls[1]},
            ]
            styles = {"backgroundColor": "#FFFF66", "headerColor": "#3333EE"}
            new_widget = await widget_moderation.add_custom_widget(
                "My widget", "# Hello world!", "/**/", 200, image_dicts, styles
            )

        """
        custom_widget = {
            "css": css,
            "height": height,
            "imageData": image_data,
            "kind": "custom",
            "shortName": short_name,
            "styles": styles,
            "text": text,
        }
        custom_widget.update(other_settings)
        return await self._create_widget(custom_widget)

    async def add_image_widget(
        self,
        short_name: str,
        data: List[Dict[str, Union[str, int]]],
        styles: Dict[str, str],
        **other_settings,
    ) -> "asyncpraw.models.ImageWidget":
        r"""Add and return an :class:`.ImageWidget`.

        :param short_name: A name for the widget, no longer than 30 characters.
        :param data: A list of ``dict``\ s as specified in `Reddit docs`_. Each ``dict``
            has the key ``"url"`` which maps to the URL of an image hosted on Reddit's
            servers. Images should be uploaded using :meth:`.upload_image`.

            For example:

            .. code-block:: python

                [
                    {
                        "url": "https://some.link",  # from upload_image()
                        "width": 600,
                        "height": 450,
                        "linkUrl": "https://github.com/asyncpraw-dev/asyncpraw",
                    },
                    {
                        "url": "https://other.link",  # from upload_image()
                        "width": 450,
                        "height": 600,
                        "linkUrl": "https://asyncpraw.readthedocs.io",
                    },
                ]

        :param styles: A ``dict`` with keys ``backgroundColor`` and ``headerColor``, and
            values of hex colors. For example, ``{"backgroundColor": "#FFFF66",
            "headerColor": "#3333EE"}``.

        :returns: The created :class:`.ImageWidget`.

        .. _reddit docs: https://www.reddit.com/dev/api#POST_api_widget

        Example usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            widget_moderation = subreddit.widgets.mod
            image_paths = ["/path/to/image1.jpg", "/path/to/image2.png"]
            image_dicts = [
                {
                    "width": 600,
                    "height": 450,
                    "linkUrl": "",
                    "url": widget_moderation.upload_image(img_path),
                }
                for img_path in image_paths
            ]
            styles = {"backgroundColor": "#FFFF66", "headerColor": "#3333EE"}
            new_widget = await widget_moderation.add_image_widget(
                "My cool pictures", image_dicts, styles
            )

        """
        image_widget = {
            "data": data,
            "kind": "image",
            "shortName": short_name,
            "styles": styles,
        }
        image_widget.update(other_settings)
        return await self._create_widget(image_widget)

    async def add_menu(
        self, data: List[Dict[str, Union[List[Dict[str, str]], str]]], **other_settings
    ) -> "asyncpraw.models.Menu":
        r"""Add and return a :class:`.Menu` widget.

        :param data: A list of ``dict``\ s describing menu contents, as specified in
            `Reddit docs`_. As of this writing, the format is:

            .. code-block:: text

                [
                    {
                        "text": a string no longer than 20 characters,
                        "url": a valid URL
                    },

                    OR

                    {
                        "children": [
                            {
                                "text": a string no longer than 20 characters,
                                "url": a valid URL,
                            },
                            ...
                        ],
                        "text": a string no longer than 20 characters,
                    },
                    ...
                ]


        :returns: The created :class:`.Menu`.

        .. _reddit docs: https://www.reddit.com/dev/api#POST_api_widget

        Example usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            widget_moderation = subreddit.widgets.mod
            menu_contents = [
                {"text": "My homepage", "url": "https://example.com"},
                {
                    "text": "Python packages",
                    "children": [
                        {"text": "asyncpraw", "url": "https://asyncpraw.readthedocs.io/"},
                        {"text": "requests", "url": "https://docs.python-requests.org/"},
                    ],
                },
                {"text": "Reddit homepage", "url": "https://reddit.com"},
            ]
            new_widget = await widget_moderation.add_menu(menu_contents)

        """
        menu = {"data": data, "kind": "menu"}
        menu.update(other_settings)
        return await self._create_widget(menu)

    async def add_post_flair_widget(
        self,
        short_name: str,
        display: str,
        order: List[str],
        styles: Dict[str, str],
        **other_settings,
    ) -> "asyncpraw.models.PostFlairWidget":
        """Add and return a :class:`.PostFlairWidget`.

        :param short_name: A name for the widget, no longer than 30 characters.
        :param display: Display style. Either ``"cloud"`` or ``"list"``.
        :param order: A list of flair template IDs. You can get all flair template IDs
            in a subreddit with:

            .. code-block:: python

                flairs = [f["id"] for f in subreddit.flair.link_templates]

        :param styles: A ``dict`` with keys ``backgroundColor`` and ``headerColor``, and
            values of hex colors. For example, ``{"backgroundColor": "#FFFF66",
            "headerColor": "#3333EE"}``.

        :returns: The created :class:`.PostFlairWidget`.

        Example usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            widget_moderation = subreddit.widgets.mod
            flairs = [f["id"] async for f in subreddit.flair.link_templates]
            styles = {"backgroundColor": "#FFFF66", "headerColor": "#3333EE"}
            new_widget = await widget_moderation.add_post_flair_widget(
                "Some flairs", "list", flairs, styles
            )

        """
        post_flair = {
            "kind": "post-flair",
            "display": display,
            "shortName": short_name,
            "order": order,
            "styles": styles,
        }
        post_flair.update(other_settings)
        return await self._create_widget(post_flair)

    async def add_text_area(
        self, short_name: str, text: str, styles: Dict[str, str], **other_settings
    ) -> "asyncpraw.models.TextArea":
        """Add and return a :class:`.TextArea` widget.

        :param short_name: A name for the widget, no longer than 30 characters.
        :param text: The Markdown text displayed in the widget.
        :param styles: A ``dict`` with keys ``backgroundColor`` and ``headerColor``, and
            values of hex colors. For example, ``{"backgroundColor": "#FFFF66",
            "headerColor": "#3333EE"}``.

        :returns: The created :class:`.TextArea`.

        Example usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            widget_moderation = subreddit.widgets.mod
            styles = {"backgroundColor": "#FFFF66", "headerColor": "#3333EE"}
            new_widget = await widget_moderation.add_text_area(
                "My cool title", "*Hello* **world**!", styles
            )

        """
        text_area = {
            "shortName": short_name,
            "text": text,
            "styles": styles,
            "kind": "textarea",
        }
        text_area.update(other_settings)
        return await self._create_widget(text_area)

    async def reorder(
        self,
        new_order: List[Union[WidgetType, str]],
        section: str = "sidebar",
    ):
        """Reorder the widgets.

        :param new_order: A list of widgets. Represented as a ``list`` that contains
            :class:`.Widget` objects, or widget IDs as strings. These types may be
            mixed.
        :param section: The section to reorder (default: ``"sidebar"``).

        Example usage:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            widgets = [widget async for widget in subreddit.widgets]
            order = list(widgets.sidebar)
            order.reverse()
            await widgets.mod.reorder(order)

        """
        order = [
            thing.id if isinstance(thing, Widget) else str(thing) for thing in new_order
        ]
        path = API_PATH["widget_order"].format(
            subreddit=self._subreddit, section=section
        )
        await self._reddit.patch(path, data={"json": dumps(order), "section": section})

    async def upload_image(self, file_path: str) -> str:
        """Upload an image to Reddit and get the URL.

        :param file_path: The path to the local file.

        :returns: The URL of the uploaded image as a ``str``.

        This method is used to upload images for widgets. For example, it can be used in
        conjunction with :meth:`.add_image_widget`, :meth:`.add_custom_widget`, and
        :meth:`.add_button_widget`.

        Example usage:

        .. code-block:: python

            my_sub = await reddit.subreddit("test")
            image_url = await my_sub.widgets.mod.upload_image("/path/to/image.jpg")
            images = [{"width": 300, "height": 300, "url": image_url, "linkUrl": ""}]
            styles = {"backgroundColor": "#FFFF66", "headerColor": "#3333EE"}
            await my_sub.widgets.mod.add_image_widget("My cool pictures", images, styles)

        """
        img_data = {
            "filepath": os.path.basename(file_path),
            "mimetype": "image/jpeg",
        }
        if file_path.lower().endswith(".png"):
            img_data["mimetype"] = "image/png"

        url = API_PATH["widget_lease"].format(subreddit=self._subreddit)
        # until we learn otherwise, assume this request always succeeds
        response = await self._reddit.post(url, data=img_data)
        upload_lease = response["s3UploadLease"]
        upload_data = {item["name"]: item["value"] for item in upload_lease["fields"]}
        upload_url = f"https:{upload_lease['action']}"

        with open(file_path, "rb") as image:
            upload_data["file"] = image
            response = await self._reddit._core._requestor._http.post(
                upload_url, data=upload_data
            )
        response.raise_for_status()

        return f"{upload_url}/{upload_data['key']}"


class Widget(AsyncPRAWBase):
    """Base class to represent a :class:`.Widget`."""

    @cachedproperty
    def mod(self) -> "asyncpraw.models.WidgetModeration":
        """Get an instance of :class:`.WidgetModeration` for this widget.

        .. note::

            Using any of the methods of :class:`.WidgetModeration` will likely make
            outdated the data in the :class:`.SubredditWidgets` that this widget belongs
            to. To remedy this, call :meth:`~.SubredditWidgets.refresh`.

        """
        return WidgetModeration(self, self.subreddit, self._reddit)

    def __eq__(self, other: Any) -> bool:
        """Check equality against another object."""
        if isinstance(other, Widget):
            return self.id.lower() == other.id.lower()
        return str(other).lower() == self.id.lower()

    # pylint: disable=invalid-name
    def __init__(self, reddit: "asyncpraw.Reddit", _data: Dict[str, Any]):
        """Initialize a :class:`.Widget` instance."""
        self.subreddit = ""  # in case it isn't in _data
        self.id = ""  # in case it isn't in _data
        super().__init__(reddit, _data=_data)
        self._mod = None


class ButtonWidget(Widget, BaseList):
    r"""Class to represent a widget containing one or more buttons.

    Find an existing one:

    .. code-block:: python

        button_widget = None
        subreddit = await reddit.subreddit("test")
        widgets = subreddit.widgets
        async for widget in widgets.sidebar():
            if isinstance(widget, asyncpraw.models.ButtonWidget):
                button_widget = widget
                break

        for button in button_widget:
            print(button.text, button.url)

    Create one:

    .. code-block:: python

        subreddit = await reddit.subreddit("test")
        widgets = subreddit.widgets
        buttons = [
            {
                "kind": "text",
                "text": "View source",
                "url": "https://github.com/asyncpraw-dev/asyncpraw",
                "color": "#FF0000",
                "textColor": "#00FF00",
                "fillColor": "#0000FF",
                "hoverState": {
                    "kind": "text",
                    "text": "ecruos weiV",
                    "color": "#000000",
                    "textColor": "#FFFFFF",
                    "fillColor": "#0000FF",
                },
            },
            {
                "kind": "text",
                "text": "View documentation",
                "url": "https://asyncpraw.readthedocs.io",
                "color": "#FFFFFF",
                "textColor": "#FFFF00",
                "fillColor": "#0000FF",
            },
        ]
        styles = {"backgroundColor": "#FFFF66", "headerColor": "#3333EE"}
        button_widget = await widgets.mod.add_button_widget(
            "Things to click", "Click some of these *cool* links!", buttons, styles
        )

    For more information on creation, see :meth:`.add_button_widget`.

    Update one:

    .. code-block:: python

        new_styles = {"backgroundColor": "#FFFFFF", "headerColor": "#FF9900"}
        button_widget = await button_widget.mod.update(
            shortName="My fav buttons", styles=new_styles
        )

    Delete one:

    .. code-block:: python

        await button_widget.mod.delete()

    .. include:: ../../typical_attributes.rst

    ==================== ==============================================================
    Attribute            Description
    ==================== ==============================================================
    ``buttons``          A list of :class:`.Button`\ s. These can also be accessed just
                         by iterating over the :class:`.ButtonWidget` (e.g., ``for
                         button in button_widget``).
    ``description``      The description, in Markdown.
    ``description_html`` The description, in HTML.
    ``id``               The widget ID.
    ``kind``             The widget kind (always ``"button"``).
    ``shortName``        The short name of the widget.
    ``styles``           A ``dict`` with the keys ``"backgroundColor"`` and
                         ``"headerColor"``.
    ``subreddit``        The :class:`.Subreddit` the button widget belongs to.
    ==================== ==============================================================

    """

    CHILD_ATTRIBUTE = "buttons"


class Calendar(Widget):
    r"""Class to represent a calendar widget.

    Find an existing one:

    .. code-block:: python

        calendar = None
        subreddit = await reddit.subreddit("test")
        widgets = subreddit.widgets
        async for widget in widgets.sidebar():
            if isinstance(widget, asyncpraw.models.Calendar):
                calendar = widget
                break

        print(calendar.googleCalendarId)

    Create one:

    .. code-block:: python

        subreddit = await reddit.subreddit("test")
        widgets = subreddit.widgets
        styles = {"backgroundColor": "#FFFF66", "headerColor": "#3333EE"}
        config = {
            "numEvents": 10,
            "showDate": True,
            "showDescription": False,
            "showLocation": False,
            "showTime": True,
            "showTitle": True,
        }
        cal_id = "y6nm89jy427drk8l71w75w9wjn@group.calendar.google.com"
        calendar = await widgets.mod.add_calendar(
            "Upcoming Events", cal_id, True, config, styles
        )

    For more information on creation, see :meth:`.add_calendar`.

    Update one:

    .. code-block:: python

        new_styles = {"backgroundColor": "#FFFFFF", "headerColor": "#FF9900"}
        calendar = await calendar.mod.update(shortName="My fav events", styles=new_styles)

    Delete one:

    .. code-block:: python

        await calendar.mod.delete()

    .. include:: ../../typical_attributes.rst

    ================= ============================================================
    Attribute         Description
    ================= ============================================================
    ``configuration`` A ``dict`` describing the calendar configuration.
    ``data``          A list of ``dict``\ s that represent events.
    ``id``            The widget ID.
    ``kind``          The widget kind (always ``"calendar"``).
    ``requiresSync``  A ``bool`` representing whether or not the calendar requires
                      synchronization.
    ``shortName``     The short name of the widget.
    ``styles``        A ``dict`` with the keys ``"backgroundColor"`` and
                      ``"headerColor"``.
    ``subreddit``     The :class:`.Subreddit` the button widget belongs to.
    ================= ============================================================

    """


class CommunityList(Widget, BaseList):
    r"""Class to represent a Related Communities widget.

    Find an existing one:

    .. code-block:: python

        community_list = None
        subreddit = await reddit.subreddit("test")
        widgets = subreddit.widgets
        async for widget in widgets.sidebar():
            if isinstance(widget, asyncpraw.models.CommunityList):
                community_list = widget
                break

        print(community_list)

    Create one:

    .. code-block:: python

        subreddit = await reddit.subreddit("test")
        widgets = subreddit.widgets
        styles = {"backgroundColor": "#FFFF66", "headerColor": "#3333EE"}
        new_subreddit = await reddit.subreddit("test")
        subreddits = ["learnpython", new_subreddit]
        community_list = await widgets.mod.add_community_list(
            "Related subreddits", subreddits, styles, "description"
        )

    For more information on creation, see :meth:`.add_community_list`.

    Update one:

    .. code-block:: python

        new_styles = {"backgroundColor": "#FFFFFF", "headerColor": "#FF9900"}
        community_list = await community_list.mod.update(
            shortName="My fav subs", styles=new_styles
        )

    Delete one:

    .. code-block:: python

        await community_list.mod.delete()

    .. include:: ../../typical_attributes.rst

    ============= =====================================================================
    Attribute     Description
    ============= =====================================================================
    ``data``      A list of :class:`.Subreddit`\ s. These can also be iterated over by
                  iterating over the :class:`.CommunityList` (e.g., ``for sub in
                  community_list``).
    ``id``        The widget ID.
    ``kind``      The widget kind (always ``"community-list"``).
    ``shortName`` The short name of the widget.
    ``styles``    A ``dict`` with the keys ``"backgroundColor"`` and ``"headerColor"``.
    ``subreddit`` The :class:`.Subreddit` the button widget belongs to.
    ============= =====================================================================

    """

    CHILD_ATTRIBUTE = "data"


class CustomWidget(Widget):
    """Class to represent a custom widget.

    Find an existing one:

    .. code-block:: python

        custom = None
        subreddit = await reddit.subreddit("test")
        widgets = subreddit.widgets
        async for widget in widgets.sidebar():
            if isinstance(widget, asyncpraw.models.CustomWidget):
                custom = widget
                break

        print(custom.text)
        print(custom.css)

    Create one:

    .. code-block:: python

        subreddit = await reddit.subreddit("test")
        widgets = subreddit.widgets
        styles = {"backgroundColor": "#FFFF66", "headerColor": "#3333EE"}
        custom = await widgets.mod.add_custom_widget(
            "My custom widget", "# Hello world!", "/**/", 200, [], styles
        )

    For more information on creation, see :meth:`.add_custom_widget`.

    Update one:

    .. code-block:: python

        new_styles = {"backgroundColor": "#FFFFFF", "headerColor": "#FF9900"}
        custom = await custom.mod.update(shortName="My fav customization", styles=new_styles)

    Delete one:

    .. code-block:: python

        await custom.mod.delete()

    .. include:: ../../typical_attributes.rst

    ================= ============================================================
    Attribute         Description
    ================= ============================================================
    ``css``           The CSS of the widget, as a ``str``.
    ``height``        The height of the widget, as an ``int``.
    ``id``            The widget ID.
    ``imageData``     A ``list`` of :class:`.ImageData` that belong to the widget.
    ``kind``          The widget kind (always ``"custom"``).
    ``shortName``     The short name of the widget.
    ``styles``        A ``dict`` with the keys ``"backgroundColor"`` and
                      ``"headerColor"``.
    ``stylesheetUrl`` A link to the widget's stylesheet.
    ``subreddit``     The :class:`.Subreddit` the button widget belongs to.
    ``text``          The text contents, as Markdown.
    ``textHtml``      The text contents, as HTML.
    ================= ============================================================

    """

    def __init__(self, reddit: "asyncpraw.Reddit", _data: Dict[str, Any]):
        """Initialize a :class:`.CustomWidget` instance."""
        _data["imageData"] = [
            ImageData(reddit, data) for data in _data.pop("imageData")
        ]
        super().__init__(reddit, _data=_data)


class IDCard(Widget):
    """Class to represent an ID card widget.

    .. code-block:: python

        subreddit = await reddit.subreddit("test")
        widgets = subreddit.widgets
        id_card = await widgets.id_card()
        print(id_card.subscribersText)

    Update one:

    .. code-block:: python

        id_card = await widgets.id_card()
        await id_card.mod.update(currentlyViewingText="Bots")

    .. include:: ../../typical_attributes.rst

    ========================= =======================================================
    Attribute                 Description
    ========================= =======================================================
    ``currentlyViewingCount`` The number of redditors viewing the subreddit.
    ``currentlyViewingText``  The text displayed next to the view count. For example,
                              ``"users online"``.
    ``description``           The subreddit description.
    ``id``                    The widget ID.
    ``kind``                  The widget kind (always ``"id-card"``).
    ``shortName``             The short name of the widget.
    ``styles``                A ``dict`` with the keys ``"backgroundColor"`` and
                              ``"headerColor"``.
    ``subreddit``             The :class:`.Subreddit` the button widget belongs to.
    ``subscribersCount``      The number of subscribers to the subreddit.
    ``subscribersText``       The text displayed next to the subscriber count. For
                              example, "users subscribed".
    ========================= =======================================================

    """


class ImageWidget(Widget, BaseList):
    r"""Class to represent an image widget.

    Find an existing one:

    .. code-block:: python

        image_widget = None
        subreddit = await reddit.subreddit("test")
        widgets = subreddit.widgets
        async for widget in widgets.sidebar():
            if isinstance(widget, asyncpraw.models.ImageWidget):
                image_widget = widget
                break

        for image in image_widget:
            print(image.url)

    Create one:

    .. code-block:: python

        subreddit = await reddit.subreddit("test")
        widgets = subreddit.widgets
        image_paths = ["/path/to/image1.jpg", "/path/to/image2.png"]
        image_dicts = [
            {
                "width": 600,
                "height": 450,
                "linkUrl": "",
                "url": await widgets.mod.upload_image(img_path),
            }
            for img_path in image_paths
        ]
        styles = {"backgroundColor": "#FFFF66", "headerColor": "#3333EE"}
        image_widget = await widgets.mod.add_image_widget(
            "My cool pictures", image_dicts, styles
        )

    For more information on creation, see :meth:`.add_image_widget`.

    Update one:

    .. code-block:: python

        new_styles = {"backgroundColor": "#FFFFFF", "headerColor": "#FF9900"}
        image_widget = await image_widget.mod.update(
            shortName="My fav images", styles=new_styles
        )

    Delete one:

    .. code-block:: python

        await image_widget.mod.delete()

    .. include:: ../../typical_attributes.rst

    ============= =====================================================================
    Attribute     Description
    ============= =====================================================================
    ``data``      A list of the :class:`.Image`\ s in this widget. Can be iterated over
                  by iterating over the :class:`.ImageWidget` (e.g., ``for img in
                  image_widget``).
    ``id``        The widget ID.
    ``kind``      The widget kind (always ``"image"``).
    ``shortName`` The short name of the widget.
    ``styles``    A ``dict`` with the keys ``"backgroundColor"`` and ``"headerColor"``.
    ``subreddit`` The :class:`.Subreddit` the button widget belongs to.
    ============= =====================================================================

    """

    CHILD_ATTRIBUTE = "data"


class Menu(Widget, BaseList):
    r"""Class to represent the top menu widget of a :class:`.Subreddit`.

    Menus can generally be found as the first item in a :class:`.Subreddit`'s top bar.

    .. code-block:: python

        subreddit = await reddit.subreddit("test")
        topbar = [widget async for widget in subreddit.widgets.topbar()]
        if len(topbar) > 0:
            probably_menu = topbar[0]
            assert isinstance(probably_menu, asyncpraw.models.Menu)
            for item in probably_menu:
                if isinstance(item, asyncpraw.models.Submenu):
                    print(item.text)
                    for child in item:
                        print("\t", child.text, child.url)
                else:  # MenuLink
                    print(item.text, item.url)

    Create one:

    .. code-block:: python

        subreddit = await reddit.subreddit("test")
        widgets = subreddit.widgets
        menu_contents = [
            {"text": "My homepage", "url": "https://example.com"},
            {
                "text": "Python packages",
                "children": [
                    {"text": "asyncpraw", "url": "https://asyncpraw.readthedocs.io/"},
                    {"text": "requests", "url": "http://python-requests.org"},
                ],
            },
            {"text": "Reddit homepage", "url": "https://reddit.com"},
        ]
        menu = await widgets.mod.add_menu(menu_contents)

    For more information on creation, see :meth:`.add_menu`.

    Update one:

    .. code-block:: python

        menu_items = list(menu)
        menu_items.reverse()
        menu = await menu.mod.update(data=menu_items)

    Delete one:

    .. code-block:: python

        await menu.mod.delete()

    .. include:: ../../typical_attributes.rst

    ============= ====================================================================
    Attribute     Description
    ============= ====================================================================
    ``data``      A list of the :class:`.MenuLink`\ s and :class:`.Submenu`\ s in this
                  widget. Can be iterated over by iterating over the :class:`.Menu`
                  (e.g., ``for item in menu``).
    ``id``        The widget ID.
    ``kind``      The widget kind (always ``"menu"``).
    ``subreddit`` The :class:`.Subreddit` the button widget belongs to.
    ============= ====================================================================

    """

    CHILD_ATTRIBUTE = "data"


class ModeratorsWidget(Widget, BaseList):
    r"""Class to represent a moderators widget.

    .. code-block:: python

        subreddit = await reddit.subreddit("test")
        widgets = subreddit.widgets
        print(await widgets.moderators_widget())

    Update one:

    .. code-block:: python

        new_styles = {"backgroundColor": "#FFFFFF", "headerColor": "#FF9900"}
        moderator_widget = await widgets.moderators_widget()
        await moderator_widget.mod.update(styles=new_styles)

    .. include:: ../../typical_attributes.rst

    ============= =====================================================================
    Attribute     Description
    ============= =====================================================================
    ``id``        The widget ID.
    ``kind``      The widget kind (always ``"moderators"``).
    ``mods``      A list of the :class:`.Redditor`\ s that moderate the subreddit. Can
                  be iterated over by iterating over the :class:`.ModeratorsWidget`
                  (e.g., ``for mod in widgets.moderators_widget``).
    ``styles``    A ``dict`` with the keys ``"backgroundColor"`` and ``"headerColor"``.
    ``subreddit`` The :class:`.Subreddit` the button widget belongs to.
    ``totalMods`` The total number of moderators in the subreddit.
    ============= =====================================================================

    """

    CHILD_ATTRIBUTE = "mods"

    def __init__(self, reddit: "asyncpraw.Reddit", _data: Dict[str, Any]):
        """Initialize a :class:`.ModeratorsWidget` instance."""
        if self.CHILD_ATTRIBUTE not in _data:
            # .mod.update() sometimes returns payload without "mods" field
            _data[self.CHILD_ATTRIBUTE] = []
        super().__init__(reddit, _data=_data)


class PostFlairWidget(Widget, BaseList):
    r"""Class to represent a post flair widget.

    Find an existing one:

    .. code-block:: python

        post_flair_widget = None
        subreddit = await reddit.subreddit("test")
        widgets = subreddit.widgets
        async for widget in widgets.sidebar():
            if isinstance(widget, asyncpraw.models.PostFlairWidget):
                post_flair_widget = widget
                break

        async for flair in post_flair_widget:
            print(flair)
            print(post_flair_widget.templates[flair])

    Create one:

    .. code-block:: python

        subreddit = await reddit.subreddit("test")
        widgets = subreddit.widgets
        flairs = [f["id"] async for f in subreddit.flair.link_templates]
        styles = {"backgroundColor": "#FFFF66", "headerColor": "#3333EE"}
        post_flair = await widgets.mod.add_post_flair_widget(
            "Some flairs", "list", flairs, styles
        )

    For more information on creation, see :meth:`.add_post_flair_widget`.

    Update one:

    .. code-block:: python

        new_styles = {"backgroundColor": "#FFFFFF", "headerColor": "#FF9900"}
        post_flair = await post_flair.mod.update(shortName="My fav flairs", styles=new_styles)

    Delete one:

    .. code-block:: python

        await post_flair.mod.delete()

    .. include:: ../../typical_attributes.rst

    ============= =====================================================================
    Attribute     Description
    ============= =====================================================================
    ``display``   The display style of the widget, either ``"cloud"`` or ``"list"``.
    ``id``        The widget ID.
    ``kind``      The widget kind (always ``"post-flair"``).
    ``order``     A list of the flair IDs in this widget. Can be iterated over by
                  iterating over the :class:`.PostFlairWidget` (e.g., ``for flair_id in
                  post_flair``).
    ``shortName`` The short name of the widget.
    ``styles``    A ``dict`` with the keys ``"backgroundColor"`` and ``"headerColor"``.
    ``subreddit`` The :class:`.Subreddit` the button widget belongs to.
    ``templates`` A ``dict`` that maps flair IDs to ``dict``\ s that describe flairs.
    ============= =====================================================================

    """

    CHILD_ATTRIBUTE = "order"


class RulesWidget(Widget, BaseList):
    """Class to represent a rules widget.

    .. code-block:: python

        subreddit = await reddit.subreddit("test")
        widgets = subreddit.widgets
        rules_widget = None
        async for widget in widgets.sidebar():
            if isinstance(widget, asyncpraw.models.RulesWidget):
                rules_widget = widget
                break
        from pprint import pprint

        pprint(rules_widget.data)

    Update one:

    .. code-block:: python

        new_styles = {"backgroundColor": "#FFFFFF", "headerColor": "#FF9900"}
        await rules_widget.mod.update(
            display="compact", shortName="The LAWS", styles=new_styles
        )

    .. include:: ../../typical_attributes.rst

    ============= =====================================================================
    Attribute     Description
    ============= =====================================================================
    ``data``      A list of the subreddit rules. Can be iterated over by iterating over
                  the :class:`.RulesWidget` (e.g., ``for rule in rules_widget``).
    ``display``   The display style of the widget, either ``"full"`` or ``"compact"``.
    ``id``        The widget ID.
    ``kind``      The widget kind (always ``"subreddit-rules"``).
    ``shortName`` The short name of the widget.
    ``styles``    A ``dict`` with the keys ``"backgroundColor"`` and ``"headerColor"``.
    ``subreddit`` The :class:`.Subreddit` the button widget belongs to.
    ============= =====================================================================

    """

    CHILD_ATTRIBUTE = "data"

    def __init__(self, reddit: "asyncpraw.Reddit", _data: Dict[str, Any]):
        """Initialize a :class:`.RulesWidget` instance."""
        if self.CHILD_ATTRIBUTE not in _data:
            # .mod.update() sometimes returns payload without "data" field
            _data[self.CHILD_ATTRIBUTE] = []
        super().__init__(reddit, _data=_data)


class TextArea(Widget):
    """Class to represent a text area widget.

    Find a text area in a subreddit:

    .. code-block:: python

        subreddit = await reddit.subreddit("test")
        widgets = subreddit.widgets
        text_area = None
        async for widget in widgets.sidebar():
            if isinstance(widget, asyncpraw.models.TextArea):
                text_area = widget
                break
        print(text_area.text)

    Create one:

    .. code-block:: python

        subreddit = await reddit.subreddit("test")
        widgets = subreddit.widgets
        styles = {"backgroundColor": "#FFFF66", "headerColor": "#3333EE"}
        text_area = await widgets.mod.add_text_area(
            "My cool title", "*Hello* **world**!", styles
        )

    For more information on creation, see :meth:`.add_text_area`.

    Update one:

    .. code-block:: python

        new_styles = {"backgroundColor": "#FFFFFF", "headerColor": "#FF9900"}
        text_area = await text_area.mod.update(shortName="My fav text", styles=new_styles)

    Delete one:

    .. code-block:: python

        await text_area.mod.delete()

    .. include:: ../../typical_attributes.rst

    ============= =====================================================================
    Attribute     Description
    ============= =====================================================================
    ``id``        The widget ID.
    ``kind``      The widget kind (always ``"textarea"``).
    ``shortName`` The short name of the widget.
    ``styles``    A ``dict`` with the keys ``"backgroundColor"`` and ``"headerColor"``.
    ``subreddit`` The :class:`.Subreddit` the button widget belongs to.
    ``text``      The widget's text, as Markdown.
    ``textHtml``  The widget's text, as HTML.
    ============= =====================================================================

    """


class WidgetEncoder(JSONEncoder):
    """Class to encode widget-related objects."""

    def default(self, o: Any) -> Any:  # pylint: disable=E0202
        """Serialize ``AsyncPRAWBase`` objects."""
        if isinstance(o, self._subreddit_class):
            return str(o)
        elif isinstance(o, AsyncPRAWBase):
            return {key: val for key, val in vars(o).items() if not key.startswith("_")}
        return JSONEncoder.default(self, o)


class WidgetModeration:
    """Class for moderating a particular widget.

    Example usage:

    .. code-block:: python

        subreddit = await reddit.subreddit("test")
        sidebar = [widget async for widget in subreddit.widgets.sidebar()]
        widget = sidebar[0]
        await widget.mod.update(shortName="My new title")
        await widget.mod.delete()

    """

    def __init__(
        self,
        widget: "asyncpraw.models.Widget",
        subreddit: Union["asyncpraw.models.Subreddit", str],
        reddit: "asyncpraw.Reddit",
    ):
        """Initialize a :class:`.WidgetModeration` instance."""
        self.widget = widget
        self._reddit = reddit
        self._subreddit = subreddit

    async def delete(self):
        """Delete the widget.

        Example usage:

        .. code-block:: python

            await widget.mod.delete()

        """
        path = API_PATH["widget_modify"].format(
            widget_id=self.widget.id, subreddit=self._subreddit
        )
        await self._reddit.delete(path)

    async def update(self, **kwargs) -> WidgetType:
        """Update the widget. Returns the updated widget.

        Parameters differ based on the type of widget. See `Reddit documentation
        <https://www.reddit.com/dev/api#PUT_api_widget_{widget_id}>`_ or the document of
        the particular type of widget.

        :returns: The updated :class:`.Widget`.

        For example, update a text widget like so:

        .. code-block:: python

            await text_widget.mod.update(shortName="New text area", text="Hello!")

        .. note::

            Most parameters follow the ``lowerCamelCase`` convention. When in doubt,
            check the Reddit documentation linked above.

        """
        path = API_PATH["widget_modify"].format(
            widget_id=self.widget.id, subreddit=self._subreddit
        )
        payload = {
            key: value
            for key, value in vars(self.widget).items()
            if not key.startswith("_")
        }
        del payload["subreddit"]  # not JSON serializable
        if "mod" in payload:
            del payload["mod"]
        payload.update(kwargs)
        widget = await self._reddit.put(
            path, data={"json": dumps(payload, cls=WidgetEncoder)}
        )
        widget.subreddit = self._subreddit
        return widget
