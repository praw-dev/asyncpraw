import sys
from os.path import abspath, dirname, join

import pytest
from asynctest import mock

from asyncpraw.models import (
    Button,
    ButtonWidget,
    Calendar,
    CommunityList,
    CustomWidget,
    IDCard,
    Image,
    ImageData,
    ImageWidget,
    Menu,
    MenuLink,
    ModeratorsWidget,
    PostFlairWidget,
    Redditor,
    RulesWidget,
    Submenu,
    Subreddit,
    TextArea,
    Widget,
)

from ... import IntegrationTest


def image_path(name):
    test_dir = abspath(dirname(sys.modules[__name__].__file__))
    return abspath(join(test_dir, "..", "..", "files", name))


class TestButtonWidget(IntegrationTest):
    async def test_button_widget(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets
        with self.use_cassette("TestSubredditWidgets.fetch_widgets"):
            button_widget = None
            async for widget in widgets.sidebar():
                if isinstance(widget, ButtonWidget):
                    button_widget = widget
                    break
            assert isinstance(button_widget, ButtonWidget)
            assert len(button_widget) >= 1
            assert all(isinstance(button, Button) for button in button_widget.buttons)
            assert button_widget == button_widget
            assert button_widget.id == button_widget
            assert button_widget in await self.async_list(widgets.sidebar())

            assert button_widget[0].text
            assert button_widget.shortName
            assert hasattr(button_widget, "description")

            assert subreddit == button_widget.subreddit

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_create_and_update_and_delete(self, _):
        self.reddit.read_only = False

        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets

        with self.use_cassette():
            styles = {"headerColor": "#123456", "backgroundColor": "#bb0e00"}
            my_image = await widgets.mod.upload_image(image_path("test.png"))
            buttons = [
                {
                    "kind": "text",
                    "text": "View source",
                    "url": "https://github.com/praw-dev/asyncpraw",
                    "color": "#FF0000",
                    "textColor": "#00FF00",
                    "fillColor": "#0000FF",
                    "hoverState": {
                        "kind": "text",
                        "text": "VIEW SOURCE!",
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
                    "hoverState": {
                        "kind": "image",
                        "url": my_image,
                        "height": 200,
                        "width": 200,
                    },
                },
                {
                    "kind": "text",
                    "text": "/r/redditdev",
                    "url": "https://reddit.com/r/redditdev",
                    "color": "#000000",
                    "textColor": "#FF00FF",
                    "fillColor": "#005500",
                },
            ]
            widget = await widgets.mod.add_button_widget(
                "Things to click",
                "Click some of these *cool* links!",
                buttons,
                styles,
            )

            assert isinstance(widget, ButtonWidget)
            assert len(widget) == 3
            assert all(isinstance(item, Button) for item in widget)
            assert widget.shortName == "Things to click"
            assert widget.description == "Click some of these *cool* links!"
            assert widget.styles == styles

            assert widget[0].text == "View source"
            assert widget[0].url == "https://github.com/praw-dev/asyncpraw"
            assert widget[2].text == "/r/redditdev"
            assert widget[2].url == "https://reddit.com/r/redditdev"

            assert widget[1].text == "View documentation"
            assert widget[1].linkUrl == "https://asyncpraw.readthedocs.io"
            assert widget[1].hoverState["kind"] == "image"
            assert widget[1].hoverState["height"] == 200

            await widgets.refresh()  # the links are initially invalid
            async for new_widget in widgets.sidebar():
                if new_widget == widget:
                    widget = new_widget
                    break

            widget = await widget.mod.update(shortName="New short name")

            assert isinstance(widget, ButtonWidget)
            assert len(widget) == 3
            assert all(isinstance(item, Button) for item in widget)
            assert widget.shortName == "New short name"
            assert widget.description == "Click some of these *cool* links!"
            assert widget.styles == styles

            assert widget[0].text == "View source"
            assert widget[0].url == "https://github.com/praw-dev/asyncpraw"
            assert widget[2].text == "/r/redditdev"
            assert widget[2].url == "https://reddit.com/r/redditdev"

            assert widget[1].text == "View documentation"
            assert widget[1].linkUrl == "https://asyncpraw.readthedocs.io"
            assert widget[1].hoverState["kind"] == "image"
            assert widget[1].hoverState["height"] == 200

            buttons.reverse()
            widget = await widget.mod.update(buttons=buttons)

            assert isinstance(widget, ButtonWidget)
            assert len(widget) == 3
            assert all(isinstance(item, Button) for item in widget)
            assert widget.shortName == "New short name"
            assert widget.description == "Click some of these *cool* links!"
            assert widget.styles == styles

            assert widget[0].text == "/r/redditdev"
            assert widget[0].url == "https://reddit.com/r/redditdev"
            assert widget[2].text == "View source"
            assert widget[2].url == "https://github.com/praw-dev/asyncpraw"

            assert widget[1].text == "View documentation"
            assert widget[1].linkUrl == "https://asyncpraw.readthedocs.io"
            assert widget[1].hoverState["kind"] == "image"
            assert widget[1].hoverState["height"] == 200

            await widget.mod.delete()


class TestCalendar(IntegrationTest):
    async def test_calendar(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets
        with self.use_cassette("TestSubredditWidgets.fetch_widgets"):
            calendar = None
            async for widget in widgets.sidebar():
                if isinstance(widget, Calendar):
                    calendar = widget
                    break
            assert isinstance(calendar, Calendar)
            assert calendar == calendar
            assert calendar.id == calendar
            assert calendar in await self.async_list(widgets.sidebar())

            assert isinstance(calendar.configuration, dict)
            assert hasattr(calendar, "requiresSync")

            assert subreddit == calendar.subreddit

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_create_and_update_and_delete(self, _):
        self.reddit.read_only = False

        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets

        with self.use_cassette():
            styles = {"headerColor": "#123456", "backgroundColor": "#bb0e00"}
            config = {
                "numEvents": 10,
                "showDate": True,
                "showDescription": False,
                "showLocation": False,
                "showTime": True,
                "showTitle": True,
            }
            cal_id = "ccahu0rstno2jrvioq4ccffn78@group.calendar.google.com"
            widget = await widgets.mod.add_calendar(
                "Upcoming Events", cal_id, True, config, styles
            )

            assert isinstance(widget, Calendar)
            assert widget.shortName == "Upcoming Events"
            assert (
                widget.googleCalendarId
                == "ccahu0rstno2jrvioq4ccffn78@group.calendar.google.com"
            )
            assert widget.configuration == config
            assert widget.styles == styles

            widget = await widget.mod.update(shortName="Past Events :(")

            assert isinstance(widget, Calendar)
            assert widget.shortName == "Past Events :("
            assert (
                widget.googleCalendarId
                == "ccahu0rstno2jrvioq4ccffn78@group.calendar.google.com"
            )
            assert widget.configuration == config
            assert widget.styles == styles

            await widget.mod.delete()


class TestCommunityList(IntegrationTest):
    async def test_community_list(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets
        with self.use_cassette("TestSubredditWidgets.fetch_widgets"):
            comm_list = None
            async for widget in widgets.sidebar():
                if isinstance(widget, CommunityList):
                    comm_list = widget
                    break
            assert isinstance(comm_list, CommunityList)
            assert len(comm_list) >= 1
            assert all(isinstance(subreddit, Subreddit) for subreddit in comm_list)
            assert comm_list == comm_list
            assert comm_list.id == comm_list
            assert comm_list in await self.async_list(widgets.sidebar())

            assert comm_list.shortName
            assert comm_list[0] in comm_list

            assert subreddit == comm_list.subreddit

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_create_and_update_and_delete(self, _):
        self.reddit.read_only = False

        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets

        with self.use_cassette():
            styles = {"headerColor": "#123456", "backgroundColor": "#bb0e00"}
            redditdev = await self.reddit.subreddit("redditdev")
            subreddits = ["learnpython", redditdev]
            widget = await widgets.mod.add_community_list(
                "My fav subs", subreddits, styles
            )
            assert isinstance(widget, CommunityList)
            assert widget.shortName == "My fav subs"
            assert widget.styles == styles
            learnpython = await self.reddit.subreddit("learnpython")
            assert learnpython in widget
            assert "redditdev" in widget

            widget = await widget.mod.update(
                shortName="My least fav subs :(",
                data=["redesign"],
            )

            assert isinstance(widget, CommunityList)
            assert widget.shortName == "My least fav subs :("
            assert widget.styles == styles
            redesign = await self.reddit.subreddit("redesign")
            assert redesign in widget

            await widget.mod.delete()


class TestCustomWidget(IntegrationTest):
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_create_and_update_and_delete(self, _):
        self.reddit.read_only = False

        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets

        with self.use_cassette():
            image_dicts = [
                {
                    "width": 0,
                    "height": 0,
                    "name": "a",
                    "url": await widgets.mod.upload_image(image_path("test.png")),
                }
            ]

            styles = {"headerColor": "#123456", "backgroundColor": "#bb0e00"}
            widget = await widgets.mod.add_custom_widget(
                "My widget", "# Hello world!", "/**/", 200, image_dicts, styles
            )

            assert isinstance(widget, CustomWidget)
            assert widget.shortName == "My widget"
            assert widget.text == "# Hello world!"
            assert widget.css == "/**/"
            assert widget.height == 200
            assert widget.styles == styles
            assert len(widget.imageData) == 1
            assert all(isinstance(img, ImageData) for img in widget.imageData)

            # initially, image URLs are incorrect, so we much refresh to get
            # the proper ones.
            await widgets.refresh()
            sidebar = await self.async_list(widgets.sidebar())
            refreshed = sidebar[-1]
            assert refreshed == widget
            widget = refreshed

            new_css = "h1,h2,h3,h4,h5,h6 {color: #00ff00;}"
            widget = await widget.mod.update(css=new_css)

            assert isinstance(widget, CustomWidget)
            assert widget.shortName == "My widget"
            assert widget.text == "# Hello world!"
            assert widget.css == new_css
            assert widget.height == 200
            assert widget.styles == styles
            assert len(widget.imageData) == 1
            assert all(isinstance(img, ImageData) for img in widget.imageData)

            await widget.mod.delete()

    async def test_custom_widget(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets
        with self.use_cassette("TestSubredditWidgets.fetch_widgets"):
            custom = None
            async for widget in widgets.sidebar():
                if isinstance(widget, CustomWidget):
                    custom = widget
                    break
            assert isinstance(custom, CustomWidget)
            assert len(custom.imageData) > 0
            assert all(isinstance(img_data, ImageData) for img_data in custom.imageData)
            assert custom == custom
            assert custom.id == custom
            assert custom in await self.async_list(widgets.sidebar())

            assert 500 >= custom.height >= 50
            assert custom.text
            assert custom.css
            assert custom.shortName

            assert subreddit == custom.subreddit


class TestIDCard(IntegrationTest):
    async def test_id_card(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets
        with self.use_cassette("TestSubredditWidgets.fetch_widgets"):
            card = await widgets.id_card()
            assert isinstance(card, IDCard)
            assert card == card
            assert card.id == card

            assert card.shortName
            assert card.currentlyViewingText
            assert card.subscribersText

            assert subreddit == card.subreddit

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update(self, _):
        self.reddit.read_only = False

        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets
        with self.use_cassette():
            id_card = await widgets.id_card()
            assert id_card.currentlyViewingText != "Users here NOW!"
            assert id_card.subscribersText != "Loyal readers"

            await id_card.mod.update(currentlyViewingText="Users here NOW!")
            await widgets.refresh()
            id_card = await widgets.id_card()

            assert id_card.currentlyViewingText == "Users here NOW!"
            assert id_card.subscribersText != "Loyal readers"

            await id_card.mod.update(subscribersText="Loyal readers")
            await widgets.refresh()
            id_card = await widgets.id_card()

            assert id_card.currentlyViewingText == "Users here NOW!"
            assert id_card.subscribersText == "Loyal readers"


class TestImageWidget(IntegrationTest):
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_create_and_update_and_delete(self, _):
        self.reddit.read_only = False

        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets

        with self.use_cassette():
            image_paths = (image_path(name) for name in ("test.jpg", "test.png"))
            image_dicts = [
                {
                    "width": 10,
                    "height": 10,
                    "linkUrl": "",
                    "url": await widgets.mod.upload_image(img_path),
                }
                for img_path in image_paths
            ]

            styles = {"headerColor": "#123456", "backgroundColor": "#bb0e00"}
            widget = await widgets.mod.add_image_widget(
                short_name="My new pics!", data=image_dicts, styles=styles
            )

            assert isinstance(widget, ImageWidget)
            assert widget.shortName == "My new pics!"
            assert widget.styles == styles
            assert len(widget) == 2
            assert all(isinstance(img, Image) for img in widget)

            widget = await widget.mod.update(
                shortName="My old pics :(", data=image_dicts[:1]
            )

            assert isinstance(widget, ImageWidget)
            assert widget.shortName == "My old pics :("
            assert widget.styles == styles
            assert len(widget) == 1
            assert all(isinstance(img, Image) for img in widget)

            await widget.mod.delete()

    async def test_image_widget(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets
        with self.use_cassette("TestSubredditWidgets.fetch_widgets"):
            img_widget = None
            async for widget in widgets.sidebar():
                if isinstance(widget, ImageWidget):
                    img_widget = widget
                    break
            assert isinstance(img_widget, ImageWidget)
            assert len(img_widget) >= 1
            assert all(isinstance(image, Image) for image in img_widget)
            assert img_widget == img_widget
            assert img_widget.id == img_widget
            assert img_widget in await self.async_list(widgets.sidebar())

            assert img_widget[0].linkUrl
            assert img_widget.shortName

            assert subreddit == img_widget.subreddit


class TestMenu(IntegrationTest):
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_create_and_update_and_delete(self, _):
        self.reddit.read_only = False

        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets

        menu_contents = [
            {"text": "My homepage", "url": "https://example.com"},
            {
                "text": "Python packages",
                "children": [
                    {"text": "PRAW", "url": "https://asyncpraw.readthedocs.io/"},
                    {"text": "requests", "url": "http://python-requests.org"},
                ],
            },
            {"text": "Reddit homepage", "url": "https://reddit.com"},
        ]

        with self.use_cassette():
            widget = await widgets.mod.add_menu(menu_contents)

            assert isinstance(widget, Menu)
            assert len(widget) == 3
            assert all(isinstance(item, (Submenu, MenuLink)) for item in widget)
            assert all(
                all(isinstance(item, MenuLink) for item in subm)
                for subm in widget
                if isinstance(subm, Submenu)
            )

            assert widget[0].text == "My homepage"
            assert widget[0].url == "https://example.com"
            assert widget[2].text == "Reddit homepage"
            assert widget[2].url == "https://reddit.com"

            assert widget[1].text == "Python packages"
            assert widget[1][0].text == "PRAW"
            assert widget[1][0].url == "https://asyncpraw.readthedocs.io/"
            assert widget[1][1].text == "requests"
            assert widget[1][1].url == "http://python-requests.org"

            menu_contents.reverse()
            widget = await widget.mod.update(data=menu_contents)

            assert isinstance(widget, Menu)
            assert len(widget) == 3
            assert all(isinstance(item, (Submenu, MenuLink)) for item in widget)
            assert all(
                all(isinstance(item, MenuLink) for item in subm)
                for subm in widget
                if isinstance(subm, Submenu)
            )

            assert widget[0].text == "Reddit homepage"
            assert widget[0].url == "https://reddit.com"
            assert widget[2].text == "My homepage"
            assert widget[2].url == "https://example.com"

            assert widget[1].text == "Python packages"
            assert widget[1][0].text == "PRAW"
            assert widget[1][0].url == "https://asyncpraw.readthedocs.io/"
            assert widget[1][1].text == "requests"
            assert widget[1][1].url == "http://python-requests.org"

            await widget.mod.delete()

    async def test_menu(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets
        with self.use_cassette("TestSubredditWidgets.fetch_widgets"):
            menu = None
            async for widget in widgets.topbar():
                if isinstance(widget, Menu):
                    menu = widget
                    break
            assert isinstance(menu, Menu)
            assert all(isinstance(item, (MenuLink, Submenu)) for item in menu)
            assert menu == menu
            assert menu.id == menu
            assert menu in await self.async_list(widgets.topbar())
            assert len(menu) >= 1
            assert menu[0].text

            assert subreddit == menu.subreddit

            submenu = None
            for child in menu:
                if isinstance(child, Submenu):
                    submenu = child
                    break
            assert isinstance(submenu, Submenu)
            assert len(submenu) >= 0
            assert all(isinstance(child, MenuLink) for child in submenu)
            assert submenu[0].text
            assert submenu[0].url


class TestModeratorsWidget(IntegrationTest):
    async def test_moderators_widget(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets
        with self.use_cassette("TestSubredditWidgets.fetch_widgets"):
            mods = await widgets.moderators_widget()
            assert isinstance(mods, ModeratorsWidget)
            assert all(isinstance(mod, Redditor) for mod in mods)
            assert mods == mods
            assert mods.id == mods

            assert len(mods) >= 1
            assert isinstance(mods[0], Redditor)

            assert subreddit == mods.subreddit

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update(self, _):
        self.reddit.read_only = False

        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets
        new_styles = {"backgroundColor": "#bababa", "headerColor": "#407bee"}
        with self.use_cassette():
            mod_widget = await widgets.moderators_widget()
            assert mod_widget.styles != new_styles
            await mod_widget.mod.update(styles=new_styles)
            await widgets.refresh()
            mod_widget = await widgets.moderators_widget()

            assert mod_widget.styles == new_styles


class TestPostFlairWidget(IntegrationTest):
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_create_and_update_and_delete(self, _):
        self.reddit.read_only = False

        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets

        with self.use_cassette():
            flairs = [f["id"] async for f in subreddit.flair.link_templates][:30]

            styles = {"headerColor": "#123456", "backgroundColor": "#bb0e00"}
            widget = await widgets.mod.add_post_flair_widget(
                "Some flairs", "list", flairs, styles
            )

            assert isinstance(widget, PostFlairWidget)
            assert widget.shortName == "Some flairs"
            assert widget.display == "list"
            assert widget.order == flairs
            assert widget.styles == styles
            assert len(widget) == len(flairs)
            assert all(flair_id in widget.templates for flair_id in widget)

            widget = await widget.mod.update(display="cloud")

            assert isinstance(widget, PostFlairWidget)
            assert widget.shortName == "Some flairs"
            assert widget.display == "cloud"
            assert widget.order == flairs
            assert widget.styles == styles
            assert len(widget) == len(flairs)
            assert all(flair_id in widget.templates for flair_id in widget)

            widget = await widget.mod.update(order=widget.order[:1])

            assert isinstance(widget, PostFlairWidget)
            assert widget.shortName == "Some flairs"
            assert widget.display == "cloud"
            assert widget.order == flairs[:1]
            assert widget.styles == styles
            assert len(widget) == 1
            assert all(flair_id in widget.templates for flair_id in widget)

            await widget.mod.delete()

    async def test_post_flair_widget(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets
        with self.use_cassette("TestSubredditWidgets.fetch_widgets"):
            pf_widget = None
            async for widget in widgets.sidebar():
                if isinstance(widget, PostFlairWidget):
                    pf_widget = widget
                    break
            assert isinstance(pf_widget, PostFlairWidget)
            assert len(pf_widget) >= 1
            assert all(flair_id in widget.templates for flair_id in widget)
            assert pf_widget == pf_widget
            assert pf_widget.id == pf_widget
            assert pf_widget in await self.async_list(widgets.sidebar())

            assert pf_widget.shortName
            assert all(flair in pf_widget for flair in pf_widget)

            assert subreddit == pf_widget.subreddit


class TestRulesWidget(IntegrationTest):
    async def test_rules_widget(self):

        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets
        with self.use_cassette("TestSubredditWidgets.fetch_widgets"):
            rules = None
            async for widget in widgets.sidebar():
                if isinstance(widget, RulesWidget):
                    rules = widget
                    break
            assert isinstance(rules, RulesWidget)
            assert rules == rules
            assert rules.id == rules

            assert rules.display

            assert len(rules) > 0
            assert subreddit == rules.subreddit

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update(self, _):
        self.reddit.read_only = False

        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets
        new_styles = {"backgroundColor": "#fedcba", "headerColor": "#012345"}
        with self.use_cassette():
            rules = None
            async for widget in widgets.sidebar():
                if isinstance(widget, RulesWidget):
                    rules = widget
                    break
            assert isinstance(rules, RulesWidget)

            assert rules.shortName != "Our regulations"
            assert rules.styles != new_styles

            rules = await rules.mod.update(
                display="compact",
                shortName="Our regulations",
                styles=new_styles,
            )

            assert rules.display == "compact"
            assert rules.shortName == "Our regulations"
            assert rules.styles == new_styles


class TestSubredditWidgets(IntegrationTest):
    async def test_bad_attribute(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets
        with self.use_cassette("TestSubredditWidgets.fetch_widgets"):
            with pytest.raises(AttributeError):
                widgets.nonexistant_attribute

    async def test_items(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets
        with self.use_cassette("TestSubredditWidgets.fetch_widgets"):
            assert isinstance(await widgets.items(), dict)

    # async def test_progressive_images(self): # FIXME: not currently working; same with praw
    #     subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
    #     widgets = subreddit.widgets
    #
    #     async def has_progressive(widgets_):
    #         # best way I could figure if an image is progressive
    #         sign = "fm=pjpg"
    #
    #         async for widget in widgets_.sidebar():
    #             if isinstance(widget, ImageWidget):
    #                 for image in widget:
    #                     if sign in image.url:
    #                         return True
    #             elif isinstance(widget, CustomWidget):
    #                 for image_data in widget.imageData:
    #                     if sign in image_data.url:
    #                         return True
    #
    #         return False
    #
    #     with self.use_cassette():
    #         widgets.progressive_images = True
    #         assert await has_progressive(widgets)
    #         widgets.progressive_images = False
    #         await widgets.refresh()
    #         assert not await has_progressive(widgets)
    #         widgets.progressive_images = True
    #         await widgets.refresh()
    #         assert await has_progressive(widgets)

    async def test_refresh(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets
        with self.use_cassette():
            assert await self.async_list(widgets.sidebar())  # to fetch
            old_sidebar = await self.async_list(
                widgets.sidebar()
            )  # reference, not value
            await widgets.refresh()
            new_sidebar = await self.async_list(widgets.sidebar())
            assert old_sidebar is not new_sidebar  # should be new list

    async def test_repr(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets
        assert (
            f"SubredditWidgets(subreddit=Subreddit(display_name='{pytest.placeholders.test_subreddit}'))"
            == repr(widgets)
        )

    async def test_sidebar(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets
        with self.use_cassette("TestSubredditWidgets.fetch_widgets"):
            sidebar = [
                isinstance(widget, Widget) and type(widget) != Widget
                async for widget in widgets.sidebar()
            ]
            assert all(sidebar)

    async def test_specials(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets
        with self.use_cassette():
            assert isinstance(await widgets.id_card(), IDCard)
            assert isinstance(await widgets.moderators_widget(), ModeratorsWidget)

    async def test_topbar(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets
        with self.use_cassette():
            assert 1 <= len(await self.async_list(widgets.topbar()))
            assert all(
                [
                    isinstance(widget, Widget) and type(widget) != Widget
                    async for widget in widgets.topbar()
                ]
            )


class TestSubredditWidgetsModeration(IntegrationTest):
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_reorder(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets

        with self.use_cassette():
            old_order = await self.async_list(widgets.sidebar())
            new_order = list(reversed(old_order))

            await widgets.mod.reorder(new_order)
            await widgets.refresh()
            order = await self.async_list(widgets.sidebar())
            assert order == new_order

            old_order = await self.async_list(widgets.sidebar())
            new_order = list(reversed(old_order))

            await widgets.mod.reorder(new_order)
            await widgets.refresh()
            order = await self.async_list(widgets.sidebar())
            assert order == new_order

            mixed_types = [
                thing if i % 2 == 0 else thing.id for i, thing in enumerate(new_order)
            ]
            # mixed_types has some str and some Widget.
            assert any(isinstance(thing, str) for thing in mixed_types)
            assert any(isinstance(thing, Widget) for thing in mixed_types)

            await widgets.mod.reorder(mixed_types)
            await widgets.refresh()
            order = await self.async_list(widgets.sidebar())
            assert order == new_order

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_upload_image(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets

        with self.use_cassette():
            for image in ("test.jpg", "test.png"):
                image_url = await widgets.mod.upload_image(image_path(image))
                assert image_url


class TestTextArea(IntegrationTest):
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_create_and_update_and_delete(self, _):
        self.reddit.read_only = False

        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets

        with self.use_cassette():
            styles = {"headerColor": "#123456", "backgroundColor": "#bb0e00"}
            widget = await widgets.mod.add_text_area(
                short_name="My new widget!", text="Hello world!", styles=styles
            )

            assert isinstance(widget, TextArea)
            assert widget.shortName == "My new widget!"
            assert widget.styles == styles
            assert widget.text == "Hello world!"

            widget = await widget.mod.update(
                shortName="My old widget :(", text="Feed me"
            )

            assert isinstance(widget, TextArea)
            assert widget.shortName == "My old widget :("
            assert widget.styles == styles
            assert widget.text == "Feed me"

            await widget.mod.delete()

    async def test_text_area(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets
        with self.use_cassette("TestSubredditWidgets.fetch_widgets"):
            text = None
            async for widget in widgets.sidebar():
                if isinstance(widget, TextArea):
                    text = widget
                    break
            assert isinstance(text, TextArea)
            assert text == text
            assert text.id == text
            side_bar = await self.async_list(widgets.sidebar())
            assert text in side_bar

            assert text.shortName
            assert text.text

            assert subreddit == text.subreddit


class TestWidget(IntegrationTest):
    async def test_inequality(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        widgets = subreddit.widgets
        with self.use_cassette("TestSubredditWidgets.fetch_widgets"):
            sidebar = await self.async_list(widgets.sidebar())
            assert len(sidebar) >= 2
        assert sidebar[0] != sidebar[1]
        assert sidebar[0] != sidebar[1].id
