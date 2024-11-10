import json

import niquests
import pytest

from unittest import mock
from unittest.mock import AsyncMock, MagicMock

from asyncpraw.exceptions import ClientException, MediaPostFailed
from asyncpraw.models import InlineGif, InlineImage, InlineVideo, Subreddit, WikiPage
from asyncpraw.models.reddit.subreddit import SubredditFlairTemplates

from ... import UnitTest


class TestSubreddit(UnitTest):
    def test_construct_failure(self, reddit):
        message = "Either 'display_name' or '_data' must be provided."
        with pytest.raises(TypeError) as excinfo:
            Subreddit(reddit)
        assert str(excinfo.value) == message

        with pytest.raises(TypeError) as excinfo:
            Subreddit(reddit, "dummy", {"id": "dummy"})
        assert str(excinfo.value) == message

        with pytest.raises(ValueError):
            Subreddit(reddit, "")

    def test_equality(self, reddit):
        subreddit1 = Subreddit(reddit, _data={"display_name": "dummy1", "n": 1})
        subreddit2 = Subreddit(reddit, _data={"display_name": "Dummy1", "n": 2})
        subreddit3 = Subreddit(reddit, _data={"display_name": "dummy3", "n": 2})
        assert subreddit1 == subreddit1
        assert subreddit2 == subreddit2
        assert subreddit3 == subreddit3
        assert subreddit1 == subreddit2
        assert subreddit2 != subreddit3
        assert subreddit1 != subreddit3
        assert "dummy1" == subreddit1
        assert subreddit2 == "dummy1"

    def test_fullname(self, reddit):
        subreddit = Subreddit(reddit, _data={"display_name": "name", "id": "dummy"})
        assert subreddit.fullname == "t5_dummy"

    def test_hash(self, reddit):
        subreddit1 = Subreddit(reddit, _data={"display_name": "dummy1", "n": 1})
        subreddit2 = Subreddit(reddit, _data={"display_name": "Dummy1", "n": 2})
        subreddit3 = Subreddit(reddit, _data={"display_name": "dummy3", "n": 2})
        assert hash(subreddit1) == hash(subreddit1)
        assert hash(subreddit2) == hash(subreddit2)
        assert hash(subreddit3) == hash(subreddit3)
        assert hash(subreddit1) == hash(subreddit2)
        assert hash(subreddit2) != hash(subreddit3)
        assert hash(subreddit1) != hash(subreddit3)

    @mock.patch(
        "asyncpraw.Reddit.post",
        new=AsyncMock(return_value={"json": {"data": {"websocket_url": ""}}}),
    )
    @mock.patch(
        "asyncpraw.models.Subreddit._upload_media",
        new=AsyncMock(
            return_value=("fake_media_url", "fake_websocket_url"),
        ),
    )
    @mock.patch("niquests.AsyncSession.get")
    async def test_invalid_media(self, connection_mock, reddit):
        reddit._core._requestor._http = niquests.AsyncSession()
        connection_mock.return_value = AsyncMock(
            status_code=101,
            extension=MagicMock(
                next_payload=AsyncMock(
                    return_value=json.dumps({"payload": {}, "type": "failed"})
                )
            ),
        )

        with pytest.raises(MediaPostFailed):
            await Subreddit(reddit, display_name="test").submit_image(
                "Test", "dummy path"
            )
        await reddit._core._requestor._http.close()

    @mock.patch("niquests.AsyncSession.get", new=AsyncMock())
    @mock.patch(
        "asyncpraw.Reddit.post",
        new=AsyncMock(
            return_value={
                "json": {"data": {"websocket_url": ""}},
                "args": {"action": "", "fields": []},
            },
        ),
    )
    @mock.patch("asyncpraw.models.Subreddit._read_and_post_media")
    async def test_media_upload_500(self, mock_method, reddit):
        from prawcore.exceptions import ServerError
        from niquests.exceptions import HTTPError

        response = MagicMock()
        response.status_code = 201
        response.raise_for_status = MagicMock(
            side_effect=HTTPError(f"Server Error", response=response)
        )
        mock_method.return_value = response
        with pytest.raises(ServerError):
            await Subreddit(reddit, display_name="test").submit_image(
                "Test", "/dev/null"
            )

    async def test_notes_delete__invalid_args(self):
        with pytest.raises(TypeError) as excinfo:
            await Subreddit(None, "SubTestBot1").mod.notes.delete(note_id="111")
        assert excinfo.value.args[0] == (
            "Either the 'redditor' parameter must be provided or this method must be"
            " called from a Redditor instance (e.g., 'redditor.notes')."
        )

    def test_repr(self, reddit):
        subreddit = Subreddit(reddit, display_name="name")
        assert repr(subreddit) == "Subreddit(display_name='name')"

    async def test_search__params_not_modified(self, reddit):
        params = {"dummy": "value"}
        subreddit = Subreddit(reddit, display_name="name")
        generator = subreddit.search(None, params=params)
        assert generator.params["dummy"] == "value"
        assert params == {"dummy": "value"}

    def test_str(self, reddit):
        subreddit = Subreddit(reddit, _data={"display_name": "name", "id": "dummy"})
        assert str(subreddit) == "name"

    async def test_submit__failure(self, reddit):
        message = "Either 'selftext' or 'url' must be provided."
        subreddit = Subreddit(reddit, display_name="name")

        with pytest.raises(TypeError) as excinfo:
            await subreddit.submit("Cool title")
        assert str(excinfo.value) == message

        with pytest.raises(TypeError) as excinfo:
            await subreddit.submit("Cool title", selftext="a", url="b")
        assert str(excinfo.value) == message

        with pytest.raises(TypeError) as excinfo:
            await subreddit.submit("Cool title", selftext="", url="b")
        assert str(excinfo.value) == message

    async def test_submit_gallery__invalid_path(self, reddit):
        message = "'invalid_image_path' is not a valid image path."
        subreddit = Subreddit(reddit, display_name="name")

        with pytest.raises(TypeError) as excinfo:
            await subreddit.submit_gallery(
                "Cool title", [{"image_path": "invalid_image_path"}]
            )
        assert str(excinfo.value) == message

    async def test_submit_gallery__missing_path(self, reddit):
        message = "'image_path' is required."
        subreddit = Subreddit(reddit, display_name="name")

        with pytest.raises(TypeError) as excinfo:
            await subreddit.submit_gallery(
                "Cool title", [{"caption": "caption"}, {"caption": "caption2"}]
            )
        assert str(excinfo.value) == message

    async def test_submit_gallery__too_long_caption(self, reddit):
        message = "Caption must be 180 characters or less."
        subreddit = Subreddit(reddit, display_name="name")
        caption = (
            "wayyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy"
            "yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy"
            "yyyyyyyyyyyyyyyy too long caption"
        )
        with pytest.raises(TypeError) as excinfo:
            await subreddit.submit_gallery(
                "Cool title", [{"image_path": __file__, "caption": caption}]
            )
        assert str(excinfo.value) == message

    async def test_submit_image__bad_filetype(self, image_path, reddit):
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        for file_name in ("test.mov", "test.mp4"):
            image = image_path(file_name)
            with pytest.raises(ClientException):
                await subreddit.submit_image("Test Title", image)

    async def test_submit_inline_media__invalid_path(self, reddit):
        message = "'invalid_image_path' is not a valid file path."
        subreddit = Subreddit(reddit, display_name="name")
        gif = InlineGif("invalid_image_path", "optional caption")
        image = InlineImage("invalid_image_path", "optional caption")
        video = InlineVideo("invalid_image_path", "optional caption")
        selftext = "Text with {gif1}, {image1}, and {video1} inline"
        media = {"gif1": gif, "image1": image, "video1": video}
        with pytest.raises(ValueError) as excinfo:
            await subreddit.submit("title", inline_media=media, selftext=selftext)
        assert str(excinfo.value) == message

    async def test_submit_video__bad_filetype(self, image_path, reddit):
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        for file_name in ("test.jpg", "test.png", "test.gif"):
            video = image_path(file_name)
            with pytest.raises(ClientException):
                await subreddit.submit_video("Test Title", video)

    async def test_upload_banner_additional_image(self, reddit):
        subreddit = Subreddit(reddit, display_name="name")
        with pytest.raises(ValueError):
            await subreddit.stylesheet.upload_banner_additional_image(
                "dummy_path", align="asdf"
            )


class TestSubredditFlair(UnitTest):
    async def test_set(self, reddit):
        subreddit = Subreddit(reddit, pytest.placeholders.test_subreddit)
        with pytest.raises(TypeError):
            await subreddit.flair.set(
                "a_redditor", css_class="myCSS", flair_template_id="gibberish"
            )


class TestSubredditFlairTemplates(UnitTest):
    async def test_not_implemented(self, reddit):
        with pytest.raises(NotImplementedError):
            await SubredditFlairTemplates(
                Subreddit(reddit, pytest.placeholders.test_subreddit)
            ).__aiter__()


class TestSubredditModmailConversationsStream(UnitTest):
    async def test_conversation_stream_capitalization(self, reddit):
        submodstream = Subreddit(reddit, display_name="Mod").mod.stream
        submodstream.modmail_conversations()
        assert submodstream.subreddit == "all"

    async def test_conversation_stream_init(self, reddit):
        submodstream = Subreddit(reddit, display_name="mod").mod.stream
        submodstream.modmail_conversations()
        assert submodstream.subreddit == "all"


class TestSubredditWiki(UnitTest):
    async def test__getitem(self, reddit):
        subreddit = Subreddit(reddit, display_name="name")
        wikipage = await subreddit.wiki.get_page("Foo", fetch=False)
        assert isinstance(wikipage, WikiPage)
        assert "foo" == wikipage.name
