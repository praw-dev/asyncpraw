"""Test asyncpraw.models.subreddit."""
import socket
import sys
from asyncio import TimeoutError
from os.path import abspath, dirname, join

import pytest
from aiohttp import ClientResponse
from aiohttp.http_websocket import WebSocketError
from asyncprawcore import BadRequest, Forbidden, NotFound, TooLarge
from asynctest import mock

from asyncpraw.const import PNG_HEADER
from asyncpraw.exceptions import (
    ClientException,
    InvalidFlairTemplateID,
    RedditAPIException,
    TooLargeMediaException,
    WebSocketException,
)
from asyncpraw.models import (
    Comment,
    InlineGif,
    InlineImage,
    InlineVideo,
    ListingGenerator,
    ModAction,
    ModmailAction,
    ModmailConversation,
    ModmailMessage,
    Redditor,
    Stylesheet,
    Submission,
    Subreddit,
    SubredditMessage,
    WikiPage,
)

from ... import IntegrationTest


def image_path(name):
    test_dir = abspath(dirname(sys.modules[__name__].__file__))
    return abspath(join(test_dir, "..", "..", "files", name))


class WebsocketMock:
    POST_URL = "https://reddit.com/r/<TEST_SUBREDDIT>/comments/{}/test_title/"

    @classmethod
    def make_dict(cls, post_id):
        return {"payload": {"redirect": cls.POST_URL.format(post_id)}}

    def __init__(self, *post_ids):
        self.post_ids = post_ids
        self.i = -1

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def receive_json(self):
        if not self.post_ids:
            raise WebSocketError(None, None)
        assert 0 <= self.i + 1 < len(self.post_ids)
        self.i += 1
        return self.make_dict(self.post_ids[self.i])


class TestSubreddit(IntegrationTest):
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_create(self, _):
        self.reddit.read_only = False
        new_name = pytest.placeholders.test_subreddit
        with self.use_cassette():
            subreddit = await self.reddit.subreddit.create(
                name=new_name,
                title="Sub",
                link_type="any",
                subreddit_type="public",
                wikimode="disabled",
                wiki_edit_age=0,
                wiki_edit_karma=0,
                comment_score_hide_mins=0,
            )
            assert subreddit.display_name == new_name
            assert subreddit.submission_type == "any"

    async def test_create__exists(self):
        self.reddit.read_only = False
        with self.use_cassette():
            with pytest.raises(RedditAPIException) as excinfo:
                await self.reddit.subreddit.create(
                    "redditdev",
                    title="redditdev",
                    link_type="any",
                    subreddit_type="public",
                    wikimode="disabled",
                )
            assert excinfo.value.items[0].error_type == "SUBREDDIT_EXISTS"

    async def test_create__invalid_parameter(self):
        self.reddit.read_only = False
        with self.use_cassette():
            with pytest.raises(RedditAPIException) as excinfo:
                # Supplying invalid setting for link_type
                await self.reddit.subreddit.create(
                    name="PRAW_iavynavff2",
                    title="sub",
                    link_type="abcd",
                    subreddit_type="public",
                    wikimode="disabled",
                )
            assert excinfo.value.items[0].error_type == "INVALID_OPTION"

    async def test_create__missing_parameter(self):
        self.reddit.read_only = False
        with self.use_cassette():
            with pytest.raises(RedditAPIException) as excinfo:
                # Not supplying required field wiki_edit_age.
                await self.reddit.subreddit.create(
                    name="PRAW_iavynavff3",
                    title=None,
                    link_type="any",
                    subreddit_type="public",
                    wikimode="disabled",
                    wiki_edit_karma=0,
                    comment_score_hide_mins=0,
                )
            assert excinfo.value.items[0].error_type == "BAD_NUMBER"

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_message(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            await subreddit.message("Test from Async PRAW", message="Test content")

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_post_requirements(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            data = await subreddit.post_requirements()
            tags = [
                "domain_blacklist",
                "body_restriction_policy",
                "domain_whitelist",
                "title_regexes",
                "body_blacklisted_strings",
                "body_required_strings",
                "title_text_min_length",
                "is_flair_required",
                "title_text_max_length",
                "body_regexes",
                "link_repost_age",
                "body_text_min_length",
                "link_restriction_policy",
                "body_text_max_length",
                "title_required_strings",
                "title_blacklisted_strings",
                "guidelines_text",
                "guidelines_display_policy",
            ]
            assert list(data) == tags

    async def test_random(self):
        with self.use_cassette():
            subreddit = await self.reddit.subreddit("pics")
            submissions = [
                await subreddit.random(),
                await subreddit.random(),
                await subreddit.random(),
                await subreddit.random(),
            ]
        assert len(submissions) == len(set(submissions))

    async def test_random__returns_none(self):
        with self.use_cassette():
            subreddit = await self.reddit.subreddit("wallpapers")
            assert await subreddit.random() is None

    async def test_sticky(self):
        subreddit = await self.reddit.subreddit("pics")
        with self.use_cassette():
            submission = await subreddit.sticky()
            assert isinstance(submission, Submission)

    async def test_sticky__not_set(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            with pytest.raises(NotFound):
                await subreddit.sticky(2)

    async def test_search(self):
        with self.use_cassette():
            subreddit = await self.reddit.subreddit("all")
            async for item in subreddit.search(
                "praw oauth search", limit=None, syntax="cloudsearch"
            ):
                assert isinstance(item, Submission)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_submit__flair(self, _):
        flair_id = "94f13282-e2e8-11e8-8291-0eae4e167256"
        flair_text = "AF"
        flair_class = ""
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            submission = await subreddit.submit(
                "Test Title",
                selftext="Test text.",
                flair_id=flair_id,
                flair_text=flair_text,
            )
            await submission.load()
            assert submission.link_flair_css_class == flair_class
            assert submission.link_flair_text == flair_text

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_submit__selftext(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            submission = await subreddit.submit("Test Title", selftext="Test text.")
            await submission.load()
            assert submission.author == pytest.placeholders.username
            assert submission.selftext == "Test text."
            assert submission.title == "Test Title"

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_submit__selftext_blank(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            submission = await subreddit.submit("Test Title", selftext="")
            await submission.load()
            assert submission.author == pytest.placeholders.username
            assert submission.selftext == ""
            assert submission.title == "Test Title"

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_submit__selftext_inline_media(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            gif = InlineGif(image_path("test.gif"), "optional caption")
            image = InlineImage(image_path("test.png"), "optional caption")
            video = InlineVideo(image_path("test.mp4"), "optional caption")
            selftext = (
                "Text with a gif {gif1} an image {image1} and a video {video1} inline"
            )
            media = {"gif1": gif, "image1": image, "video1": video}
            submission = await subreddit.submit(
                "title", selftext=selftext, inline_media=media
            )
            await submission.load()
            assert submission.author == pytest.placeholders.username
            assert (
                submission.selftext
                == "Text with a gif\n\n[optional caption](https://i.redd.it/s1i7ejqkgdc61.gif)\n\nan image\n\n[optional caption](https://preview.redd.it/95pza2skgdc61.png?width=128&format=png&auto=webp&s=c81d303645d9792afcdb9c47f0a6039708714274)\n\nand a video\n\n[optional caption](https://reddit.com/link/l0vyxc/video/qeg2azskgdc61/player)\n\ninline"
            )
            assert submission.title == "title"

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_submit_live_chat(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            submission = await subreddit.submit(
                "Test Title", selftext="", discussion_type="CHAT"
            )
            await submission.load()
            assert submission.discussion_type == "CHAT"

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_submit__url(self, _):
        url = "https://asyncpraw.readthedocs.org/en/stable/"
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            submission = await subreddit.submit("Test Title", url=url)
            await submission.load()
            assert submission.author == pytest.placeholders.username
            assert submission.url == url
            assert submission.title == "Test Title"

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_submit__nsfw(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            submission = await subreddit.submit(
                "Test Title", selftext="Test text.", nsfw=True
            )
            await submission.load()
            assert submission.over_18 is True

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_submit__spoiler(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            submission = await subreddit.submit(
                "Test Title", selftext="Test text.", spoiler=True
            )
            await submission.load()
            assert submission.spoiler is True

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_submit__verify_invalid(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            self.reddit.validate_on_submit = True
            with pytest.raises(
                (RedditAPIException, BadRequest)
            ):  # waiting for prawcore fix
                await subreddit.submit("dfgfdgfdgdf", url="https://www.google.com")

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_submit_poll(self, _):
        options = ["Yes", "No", "3", "4", "5", "6"]
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            submission = await subreddit.submit_poll(
                "Test Poll",
                selftext="Test poll text.",
                options=options,
                duration=6,
            )
            await submission.load()
            assert submission.author == pytest.placeholders.username
            assert submission.selftext.startswith("Test poll text.")
            assert submission.title == "Test Poll"
            assert [str(option) for option in submission.poll_data.options] == options
            assert submission.poll_data.voting_end_timestamp > submission.created_utc

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_submit_poll__flair(self, _):
        flair_id = "94f13282-e2e8-11e8-8291-0eae4e167256"
        flair_text = "AF"
        flair_class = ""
        options = ["Yes", "No"]
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            submission = await subreddit.submit_poll(
                "Test Poll",
                selftext="Test poll text.",
                flair_id=flair_id,
                flair_text=flair_text,
                options=options,
                duration=6,
            )
            await submission.load()
            assert submission.link_flair_text == flair_text
            assert submission.link_flair_css_class == flair_class

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_submit_poll__live_chat(self, _):
        options = ["Yes", "No"]
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            submission = await subreddit.submit_poll(
                "Test Poll",
                selftext="",
                discussion_type="CHAT",
                options=options,
                duration=2,
            )
            await submission.load()
            assert submission.discussion_type == "CHAT"

    async def test_submit_gallery(self):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            images = [
                {"image_path": image_path("test.png")},
                {"image_path": image_path("test.jpg"), "caption": "test.jpg"},
                {
                    "image_path": image_path("test.gif"),
                    "outbound_url": "https://example.com",
                },
                {
                    "image_path": image_path("test.png"),
                    "caption": "test.png",
                    "outbound_url": "https://example.com",
                },
            ]

            submission = await subreddit.submit_gallery("Test Title", images)
            assert submission.author == pytest.placeholders.username
            assert submission.is_gallery
            assert submission.title == "Test Title"
            items = submission.gallery_data["items"]
            assert isinstance(submission.gallery_data["items"], list)
            for i, item in enumerate(items):
                test_data = images[i]
                test_data.pop("image_path")
                item.pop("id")
                item.pop("media_id")
                assert item == test_data

    async def test_submit_gallery_disabled(self):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            images = [
                {"image_path": image_path("test.png")},
                {"image_path": image_path("test.jpg"), "caption": "test.jpg"},
                {
                    "image_path": image_path("test.gif"),
                    "outbound_url": "https://example.com",
                },
                {
                    "image_path": image_path("test.png"),
                    "caption": "test.png",
                    "outbound_url": "https://example.com",
                },
            ]

            with pytest.raises(RedditAPIException):
                await subreddit.submit_gallery("Test Title", images)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_submit_gallery__flair(self, _):
        flair_id = "6fc213da-cae7-11ea-9274-0e2407099e45"
        flair_text = "test"
        flair_class = "test-flair-class"
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            images = [
                {"image_path": image_path("test.png")},
                {"image_path": image_path("test.jpg"), "caption": "test.jpg"},
                {
                    "image_path": image_path("test.gif"),
                    "outbound_url": "https://example.com",
                },
                {
                    "image_path": image_path("test.png"),
                    "caption": "test.png",
                    "outbound_url": "https://example.com",
                },
            ]
            submission = await subreddit.submit_gallery(
                "Test Title", images, flair_id=flair_id, flair_text=flair_text
            )
            assert submission.link_flair_css_class == flair_class
            assert submission.link_flair_text == flair_text

    @mock.patch(
        "aiohttp.client.ClientSession.ws_connect",
        return_value=WebsocketMock(
            "l6eqw6", "l6er3r", "l6erfu"  # update with cassette
        ),
    )
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_submit_image(self, _, __):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            for i, file_name in enumerate(("test.png", "test.jpg", "test.gif")):
                image = image_path(file_name)
                submission = await subreddit.submit_image(f"Test Title {i}", image)
                await submission.load()
                assert submission.author == pytest.placeholders.username
                assert submission.is_reddit_media_domain
                assert submission.title == f"Test Title {i}"

    @pytest.mark.usefixtures("tmp_path")
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_submit_image__large(self, _):
        reddit = self.reddit
        reddit.read_only = False
        mock_data = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<Error>"
            "<Code>EntityTooLarge</Code>"
            "<Message>Your proposed upload exceeds the maximum allowed size</Message>"
            "<ProposedSize>20971528</ProposedSize>"
            "<MaxSizeAllowed>20971520</MaxSizeAllowed>"
            "<RequestId>23F056D6990D87E0</RequestId>"
            "<HostId>iYEVOuRfbLiKwMgHt2ewqQRIm0NWL79uiC2rPLj9P0PwW55MhjY2/O8d9JdKTf1iwzLjwWMnGQ=</HostId>"
            "</Error>"
        )
        _post = reddit._core._requestor._http.post

        async def patch_request(url, *args, **kwargs):
            """Patch requests to return mock data on specific url."""
            if "https://reddit-uploaded-media.s3-accelerate.amazonaws.com" in url:
                response = ClientResponse
                response.text = mock_data
                response.status = 400
                return response
            return await _post(url, *args, **kwargs)

        reddit._core._requestor._http.post = patch_request

        fake_png = PNG_HEADER + b"\x1a" * 10  # Normally 1024 ** 2 * 20 (20 MB)
        with open(self.tmp_path.joinpath("fake_img.png"), "wb") as tempfile:
            tempfile.write(fake_png)
        with self.use_cassette():
            with pytest.raises(TooLargeMediaException):
                subreddit = await reddit.subreddit("test")
                await subreddit.submit_image("test", tempfile.name)

    @mock.patch("asyncio.sleep", return_value=None)
    @mock.patch("aiohttp.client.ClientSession.ws_connect", return_value=WebsocketMock())
    async def test_submit_image__bad_websocket(self, _, __):
        self.reddit.read_only = False
        with self.use_cassette("TestSubreddit.test_submit_image"):
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            for file_name in ("test.png", "test.jpg"):
                image = image_path(file_name)
                with pytest.raises(ClientException):
                    await subreddit.submit_image("Test Title", image)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_submit_image__bad_filetype(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            for file_name in ("test.mov", "test.mp4"):
                image = image_path(file_name)
                with pytest.raises(ClientException):
                    await subreddit.submit_image("Test Title", image)

    @mock.patch("asyncio.sleep", return_value=None)
    @mock.patch(
        "aiohttp.client.ClientSession.ws_connect", return_value=WebsocketMock("l6evpd")
    )  # update with cassette
    async def test_submit_image__flair(self, _, __):
        flair_id = "6fc213da-cae7-11ea-9274-0e2407099e45"
        flair_text = "Test flair text"
        flair_class = ""
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            image = image_path("test.jpg")
            submission = await subreddit.submit_image(
                "Test Title", image, flair_id=flair_id, flair_text=flair_text
            )
            await submission.load()
            assert submission.link_flair_css_class == flair_class
            assert submission.link_flair_text == flair_text

    @mock.patch("asyncio.sleep", return_value=None)
    @mock.patch(
        "aiohttp.client.ClientSession.ws_connect", return_value=WebsocketMock("l6ey7j")
    )  # update with cassette
    async def test_submit_image_chat(self, _, __):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            image = image_path("test.jpg")
            submission = await subreddit.submit_image(
                "Test Title", image, discussion_type="CHAT"
            )
            await submission.load()
            assert submission.discussion_type == "CHAT"

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_submit_image_verify_invalid(self, _):
        self.reddit.read_only = False
        self.reddit.validate_on_submit = True
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            image = image_path("test.jpg")
            with pytest.raises(
                (RedditAPIException, BadRequest)
            ):  # waiting for prawcore fix
                await subreddit.submit_image(
                    "gdfgfdgdgdgfgfdgdfgfdgfdg", image, without_websockets=True
                )

    @mock.patch("asyncio.sleep", return_value=None)
    @mock.patch(
        "aiohttp.client.ClientSession.ws_connect", side_effect=BlockingIOError
    )  # happens with timeout=0
    async def test_submit_image__timeout_1(self, _, __):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            image = image_path("test.jpg")
            with pytest.raises(WebSocketException):
                await subreddit.submit_image("Test Title", image)

    @mock.patch("asyncio.sleep", return_value=None)
    @mock.patch(
        "aiohttp.client.ClientSession.ws_connect",
        side_effect=socket.timeout
        # happens with timeout=0.00001
    )
    async def test_submit_image__timeout_2(self, _, __):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            image = image_path("test.jpg")
            with pytest.raises(WebSocketException):
                await subreddit.submit_image("Test Title", image)

    @mock.patch("asyncio.sleep", return_value=None)
    @mock.patch(
        "aiohttp.client.ClientSession.ws_connect",
        side_effect=TimeoutError,
        # could happen but Async PRAW should handle it
    )
    async def test_submit_image__timeout_3(self, _, __):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            image = image_path("test.jpg")
            with pytest.raises(WebSocketException):
                await subreddit.submit_image("Test Title", image)

    @mock.patch("asyncio.sleep", return_value=None)
    @mock.patch(
        "aiohttp.client.ClientSession.ws_connect",
        side_effect=WebSocketError(None, None),
        # could happen but Async PRAW should handle it
    )
    async def test_submit_image__timeout_4(self, _, __):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            image = image_path("test.jpg")
            with pytest.raises(WebSocketException):
                await subreddit.submit_image("Test Title", image)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_submit_image__without_websockets(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            for file_name in ("test.png", "test.jpg", "test.gif"):
                image = image_path(file_name)
                submission = await subreddit.submit_image(
                    "Test Title", image, without_websockets=True
                )
                assert submission is None

    @mock.patch("asyncio.sleep", return_value=None)
    @mock.patch(
        "aiohttp.client.ClientSession.ws_connect",
        return_value=WebsocketMock("l6g58s", "l6g5al"),  # update with cassette
    )
    async def test_submit_video(self, _, __):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            for i, file_name in enumerate(("test.mov", "test.mp4")):
                video = image_path(file_name)
                submission = await subreddit.submit_video(f"Test Title {i}", video)
                await submission.load()
                assert submission.author == pytest.placeholders.username
                # assert submission.is_reddit_media_domain
                # for some reason returns false
                assert submission.title == f"Test Title {i}"

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_submit_video__bad_filetype(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            for file_name in ("test.jpg", "test.png", "test.gif"):
                video = image_path(file_name)
                with pytest.raises(ClientException):
                    await subreddit.submit_video("Test Title", video)

    @mock.patch("asyncio.sleep", return_value=None)
    @mock.patch("aiohttp.client.ClientSession.ws_connect", return_value=WebsocketMock())
    async def test_submit_video__bad_websocket(self, _, __):
        self.reddit.read_only = False
        with self.use_cassette("TestSubreddit.test_submit_video"):
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            for file_name in ("test.mov", "test.mp4"):
                video = image_path(file_name)
                with pytest.raises(ClientException):
                    await subreddit.submit_video("Test Title", video)

    @mock.patch("asyncio.sleep", return_value=None)
    @mock.patch(
        "aiohttp.client.ClientSession.ws_connect", return_value=WebsocketMock("l6g771")
    )  # update with cassette
    async def test_submit_video__flair(self, _, __):
        flair_id = "6fc213da-cae7-11ea-9274-0e2407099e45"
        flair_text = "Test flair text"
        flair_class = ""
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            image = image_path("test.mov")
            submission = await subreddit.submit_video(
                "Test Title", image, flair_id=flair_id, flair_text=flair_text
            )
            assert submission.link_flair_css_class == flair_class
            assert submission.link_flair_text == flair_text

    @mock.patch("asyncio.sleep", return_value=None)
    @mock.patch(
        "aiohttp.client.ClientSession.ws_connect", return_value=WebsocketMock("l6gocy")
    )  # update with cassette
    async def test_submit_video_chat(self, _, __):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            image = image_path("test.mov")
            submission = await subreddit.submit_video(
                "Test Title", image, discussion_type="CHAT"
            )
            await submission.load()
            assert submission.discussion_type == "CHAT"

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_submit_video_verify_invalid(self, _):
        self.reddit.read_only = False
        self.reddit.validate_on_submit = True
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            image = image_path("test.mov")
            with pytest.raises(
                (RedditAPIException, BadRequest)
            ):  # waiting for prawcore fix
                await subreddit.submit_video(
                    "gdfgfdgdgdgfgfdgdfgfdgfdg", image, without_websockets=True
                )

    @mock.patch("asyncio.sleep", return_value=None)
    @mock.patch(
        "aiohttp.client.ClientSession.ws_connect",
        return_value=WebsocketMock("l6gvvi", "l6gvx7"),  # update with cassette
    )
    async def test_submit_video__thumbnail(self, _, __):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            for video_name, thumb_name in (
                ("test.mov", "test.jpg"),
                ("test.mp4", "test.png"),
            ):
                video = image_path(video_name)
                thumb = image_path(thumb_name)
                submission = await subreddit.submit_video(
                    "Test Title", video, thumbnail_path=thumb
                )
                await submission.load()
                assert submission.author == pytest.placeholders.username
                assert submission.is_video
                assert submission.title == "Test Title"

    @mock.patch("asyncio.sleep", return_value=None)
    @mock.patch(
        "aiohttp.client.ClientSession.ws_connect", side_effect=BlockingIOError
    )  # happens with timeout=0
    async def test_submit_video__timeout_1(self, _, __):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            video = image_path("test.mov")
            with pytest.raises(WebSocketException):
                await subreddit.submit_video("Test Title", video)

    @mock.patch("asyncio.sleep", return_value=None)
    @mock.patch(
        "aiohttp.client.ClientSession.ws_connect",
        side_effect=socket.timeout
        # happens with timeout=0.00001
    )
    async def test_submit_video__timeout_2(self, _, __):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            video = image_path("test.mov")
            with pytest.raises(WebSocketException):
                await subreddit.submit_video("Test Title", video)

    @mock.patch("asyncio.sleep", return_value=None)
    @mock.patch(
        "aiohttp.client.ClientSession.ws_connect",
        side_effect=TimeoutError,
        # could happen but Async PRAW should handle it
    )
    async def test_submit_video__timeout_3(self, _, __):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            video = image_path("test.mov")
            with pytest.raises(WebSocketException):
                await subreddit.submit_video("Test Title", video)

    @mock.patch("asyncio.sleep", return_value=None)
    @mock.patch(
        "aiohttp.client.ClientSession.ws_connect",
        side_effect=WebSocketError(None, None),
        # could happen but Async PRAW should handle it
    )
    async def test_submit_video__timeout_4(self, _, __):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            video = image_path("test.mov")
            with pytest.raises(WebSocketException):
                await subreddit.submit_video("Test Title", video)

    @mock.patch("asyncio.sleep", return_value=None)
    @mock.patch(
        "aiohttp.client.ClientSession.ws_connect",
        return_value=WebsocketMock("l6gtwa", "l6gty1"),  # update with cassette
    )
    async def test_submit_video__videogif(self, _, __):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            for file_name in ("test.mov", "test.mp4"):
                video = image_path(file_name)
                submission = await subreddit.submit_video(
                    "Test Title", video, videogif=True
                )
                assert submission.author == pytest.placeholders.username
                assert submission.is_video
                assert submission.title == "Test Title"

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_submit_video__without_websockets(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            for file_name in ("test.mov", "test.mp4"):
                video = image_path(file_name)
                submission = await subreddit.submit_video(
                    "Test Title", video, without_websockets=True
                )
                assert submission is None

    async def test_subscribe(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await subreddit.subscribe()

    async def test_subscribe__multiple(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await subreddit.subscribe(
                ["redditdev", await self.reddit.subreddit("iama")]
            )

    async def test_traffic(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            traffic = await subreddit.traffic()
            assert isinstance(traffic, dict)

    async def test_traffic__not_public(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit("announcements")
        with self.use_cassette():
            with pytest.raises(NotFound):
                await subreddit.traffic()

    async def test_unsubscribe(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await subreddit.unsubscribe()

    async def test_unsubscribe__multiple(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await subreddit.unsubscribe(
                ["redditdev", await self.reddit.subreddit("iama")]
            )


class TestSubredditFilters(IntegrationTest):
    @mock.patch("asyncio.sleep", return_value=None)
    async def test__aiter__all(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit("all")
            filters = await self.async_list(subreddit.filters)
        assert len(filters) > 0
        assert all(isinstance(x, Subreddit) for x in filters)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test__aiter__mod(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit("mod")
        with self.use_cassette():
            filters = await self.async_list(subreddit.filters)
        assert len(filters) > 0
        assert all(isinstance(x, Subreddit) for x in filters)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_add(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit("all")
            await subreddit.filters.add("redditdev")

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_add__subreddit_model(self, _):
        self.reddit.read_only = False
        with self.use_cassette("TestSubredditFilters.test_add"):
            subreddit = await self.reddit.subreddit("all")
            await subreddit.filters.add(await self.reddit.subreddit("redditdev"))

    # @mock.patch("asyncio.sleep", return_value=None) # FIXME: no longer raises not found; same with praw
    # async def test_add__non_special(self, _):
    #     self.reddit.read_only = False
    #     with self.use_cassette():
    #         with pytest.raises(NotFound):
    #             subreddit = await self.reddit.subreddit("redditdev")
    #             await subreddit.filters.add("redditdev")

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_remove(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit("mod")
            await subreddit.filters.remove("redditdev")

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_remove__subreddit_model(self, _):
        self.reddit.read_only = False
        with self.use_cassette("TestSubredditFilters.test_remove"):
            subreddit = await self.reddit.subreddit("mod")
            await subreddit.filters.remove(await self.reddit.subreddit("redditdev"))

    # @mock.patch("asyncio.sleep", return_value=None) # FIXME: no longer rases not found; same with praw
    # async def test_remove__non_special(self, _):
    #     self.reddit.read_only = False
    #     with self.use_cassette():
    #         with pytest.raises(NotFound):
    #             subreddit = await self.reddit.subreddit("redditdev")
    #             await subreddit.filters.remove("redditdev")


class TestSubredditFlair(IntegrationTest):
    REDDITOR = pytest.placeholders.username

    async def test__call(self):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            mapping = subreddit.flair()
            assert len(await self.async_list(mapping)) > 0
            assert all([isinstance(x["user"], Redditor) async for x in mapping])

    async def test__call__user_filter(self):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            mapping = subreddit.flair(redditor=self.REDDITOR)
            assert len(await self.async_list(mapping)) == 1

    async def test_configure(self):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            await subreddit.flair.configure(
                position=None,
                self_assign=True,
                link_position=None,
                link_self_assign=True,
            )

    async def test_configure__defaults(self):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            await subreddit.flair.configure()

    async def test_delete(self):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            await subreddit.flair.delete(pytest.placeholders.username)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_delete_all(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            response = await subreddit.flair.delete_all()
            assert len(response) == 5
            assert all("removed" in x["status"] for x in response)

    async def test_set__flair_id(self):
        self.reddit.read_only = False
        with self.use_cassette():
            redditor = await self.reddit.redditor(pytest.placeholders.username)
            flair = "c99ff6d0-c559-11ea-b93b-0ef0f80279f1"
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            await subreddit.flair.set(
                redditor, "redditor flair", flair_template_id=flair
            )

    async def test_set__flair_id_default_text(self):
        self.reddit.read_only = False
        with self.use_cassette():
            redditor = await self.reddit.redditor(pytest.placeholders.username)
            flair = "c99ff6d0-c559-11ea-b93b-0ef0f80279f1"
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            await subreddit.flair.set(redditor, flair_template_id=flair)

    async def test_set__redditor(self):
        self.reddit.read_only = False
        with self.use_cassette():
            redditor = await self.reddit.redditor(pytest.placeholders.username)
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            await subreddit.flair.set(redditor, "redditor flair")

    async def test_set__redditor_css_only(self):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            await subreddit.flair.set(
                pytest.placeholders.username, css_class="some class"
            )

    async def test_set__redditor_string(self):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            await subreddit.flair.set(
                pytest.placeholders.username, "new flair", "some class"
            )

    async def test_update(self):
        self.reddit.read_only = False
        with self.use_cassette():
            redditor = await self.reddit.redditor(pytest.placeholders.username)
            flair_list = [
                redditor,
                "spez",
                {"user": "bsimpson"},
                {"user": "spladug", "flair_text": "", "flair_css_class": ""},
            ]
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            response = await subreddit.flair.update(
                flair_list, css_class="async default"
            )
        assert all(x["ok"] for x in response)
        assert not any(x["errors"] for x in response)
        assert not any(x["warnings"] for x in response)
        assert len([x for x in response if "added" in x["status"]]) == 3
        assert len([x for x in response if "removed" in x["status"]]) == 1
        for i, name in enumerate([str(redditor), "spez", "bsimpson", "spladug"]):
            assert name in response[i]["status"]

    async def test_update__comma_in_text(self):
        self.reddit.read_only = False
        flair_list = [
            {"user": "bsimpson"},
            {"user": "spladug", "flair_text": "a,b"},
        ]
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            response = await subreddit.flair.update(
                flair_list, css_class="async default"
            )
            assert all(x["ok"] for x in response)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update_quotes(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            redditor = await self.reddit.user.me()
            response = await subreddit.flair.update(
                [redditor], text='"testing"', css_class="testing"
            )
            assert all(x["ok"] for x in response)
            flair = await self.async_next(subreddit.flair(redditor))
            assert flair["flair_text"] == '"testing"'
            assert flair["flair_css_class"] == "testing"


class TestSubredditFlairTemplates(IntegrationTest):
    async def test__aiter(self):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            templates = await self.async_list(subreddit.flair.templates)
        assert len(templates) == 1

        for flair_template in templates:
            assert flair_template["id"]

    async def test_add(self):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            await subreddit.flair.templates.add(
                "PRAW", css_class="myCSS", background_color="#ABCDEF"
            )

    async def test_clear(self):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            await subreddit.flair.templates.clear()

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_delete(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            template = await self.async_next(subreddit.flair.templates)
            await subreddit.flair.templates.delete(template["id"])

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            template = await self.async_next(subreddit.flair.templates)
            await subreddit.flair.templates.update(
                template["id"],
                "PRAW updated",
                css_class="myCSS",
                text_color="dark",
                background_color="#00FFFF",
            )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update_invalid(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            with pytest.raises(InvalidFlairTemplateID):
                subreddit = await self.reddit.subreddit(
                    pytest.placeholders.test_subreddit
                )
                await subreddit.flair.templates.update(
                    "fake id",
                    "PRAW updated",
                    css_class="myCSS",
                    text_color="dark",
                    background_color="#00FFFF",
                    fetch=True,
                )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update_fetch(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            template = await self.async_next(subreddit.flair.templates)
            await subreddit.flair.templates.update(
                template["id"],
                "PRAW updated",
                css_class="myCSS",
                text_color="dark",
                background_color="#00FFFF",
                fetch=True,
            )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update_fetch_no_css_class(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            template = await self.async_next(subreddit.flair.templates)
            await subreddit.flair.templates.update(
                template["id"],
                "PRAW updated",
                text_color="dark",
                background_color="#00FFFF",
                fetch=True,
            )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update_fetch_no_text(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            template = await self.async_next(subreddit.flair.templates)
            await subreddit.flair.templates.update(
                template["id"],
                css_class="myCSS",
                text_color="dark",
                background_color="#00FFFF",
                fetch=True,
            )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update_fetch_no_text_or_css_class(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            template = await self.async_next(subreddit.flair.templates)
            await subreddit.flair.templates.update(
                template["id"],
                text_color="dark",
                background_color="#00FFFF",
                fetch=True,
            )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update_fetch_only(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            template = await self.async_next(subreddit.flair.templates)
            await subreddit.flair.templates.update(template["id"], fetch=True)
            newtemplate = list(
                filter(
                    lambda _template: _template["id"] == template["id"],
                    [flair async for flair in subreddit.flair.templates],
                )
            )[0]
            assert newtemplate == template

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update_false(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            template = await self.async_next(subreddit.flair.templates)
            await subreddit.flair.templates.update(
                template["id"], text_editable=True, fetch=True
            )
            await subreddit.flair.templates.update(
                template["id"], text_editable=False, fetch=True
            )
            newtemplate = list(
                filter(
                    lambda _template: _template["id"] == template["id"],
                    [flair async for flair in subreddit.flair.templates],
                )
            )[0]
            assert newtemplate["text_editable"] is False


class TestSubredditLinkFlairTemplates(IntegrationTest):
    async def test__aiter(self):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            templates = await self.async_list(subreddit.flair.link_templates)
        assert len(templates) == 2

        for template in templates:
            assert template["id"]
            assert isinstance(template["richtext"], list)
            assert all(isinstance(item, dict) for item in template["richtext"])

    async def test_add(self):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            await subreddit.flair.link_templates.add(
                "PRAW", css_class="myCSS", text_color="light"
            )

    async def test_clear(self):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            await subreddit.flair.link_templates.clear()


class TestSubredditListings(IntegrationTest):
    async def test_comments(self):
        with self.use_cassette():
            subreddit = await self.reddit.subreddit("askreddit")
            comments = await self.async_list(subreddit.comments())
        assert len(comments) == 100

    async def test_controversial(self):
        with self.use_cassette():
            subreddit = await self.reddit.subreddit("askreddit")
            submissions = await self.async_list(subreddit.controversial())
        assert len(submissions) == 100

    async def test_gilded(self):
        with self.use_cassette():
            subreddit = await self.reddit.subreddit("askreddit")
            submissions = await self.async_list(subreddit.gilded())
        assert len(submissions) >= 50

    async def test_hot(self):
        with self.use_cassette():
            subreddit = await self.reddit.subreddit("askreddit")
            submissions = await self.async_list(subreddit.hot())
        assert len(submissions) == 100

    async def test_new(self):
        with self.use_cassette():
            subreddit = await self.reddit.subreddit("askreddit")
            submissions = await self.async_list(subreddit.new())
        assert len(submissions) == 100

    async def test_random_rising(self):
        with self.use_cassette():
            subreddit = await self.reddit.subreddit("askreddit")
            submissions = await self.async_list(subreddit.random_rising())
        assert len(submissions) == 91

    async def test_rising(self):
        with self.use_cassette():
            subreddit = await self.reddit.subreddit("askreddit")
            submissions = await self.async_list(subreddit.rising())
        assert len(submissions) == 100

    async def test_top(self):
        with self.use_cassette():
            subreddit = await self.reddit.subreddit("askreddit")
            submissions = await self.async_list(subreddit.top())
        assert len(submissions) == 100


class TestSubredditModeration(IntegrationTest):
    async def test_accept_invite__no_invite(self):
        self.reddit.read_only = False
        with self.use_cassette():
            with pytest.raises(RedditAPIException) as excinfo:
                subreddit = await self.reddit.subreddit(
                    pytest.placeholders.test_subreddit
                )
                await subreddit.mod.accept_invite()
            assert excinfo.value.items[0].error_type == "NO_INVITE_FOUND"

    async def test_edited(self):
        self.reddit.read_only = False
        with self.use_cassette():
            count = 0
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            async for item in subreddit.mod.edited():
                assert isinstance(item, (Comment, Submission))
                count += 1
            assert count == 100

    async def test_edited__only_comments(self):
        self.reddit.read_only = False
        with self.use_cassette():
            count = 0
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            async for item in subreddit.mod.edited(only="comments"):
                assert isinstance(item, Comment)
                count += 1
            assert count == 100

    async def test_edited__only_submissions(self):
        self.reddit.read_only = False
        with self.use_cassette():
            count = 0
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            async for item in subreddit.mod.edited(only="submissions"):
                assert isinstance(item, Submission)
                count += 1
            assert count > 0

    async def test_inbox(self):
        self.reddit.read_only = False
        with self.use_cassette():
            count = 0
            subreddit = await self.reddit.subreddit("all")
            async for item in subreddit.mod.inbox():
                assert isinstance(item, SubredditMessage)
                count += 1
            assert count == 100

    async def test_log(self):
        self.reddit.read_only = False
        with self.use_cassette():
            count = 0
            subreddit = await self.reddit.subreddit("mod")
            async for item in subreddit.mod.log():
                assert isinstance(item, ModAction)
                count += 1
            assert count == 100

    async def test_log__filters(self):
        self.reddit.read_only = False
        with self.use_cassette():
            count = 0
            redditor = await self.reddit.user.me()
            subreddit = await self.reddit.subreddit("mod")
            async for item in subreddit.mod.log(action="invitemoderator", mod=redditor):
                assert isinstance(item, ModAction)
                assert item.action == "invitemoderator"
                assert isinstance(item.mod, Redditor)
                assert item.mod == pytest.placeholders.username
                count += 1
            assert count > 0

    async def test_modqueue(self):
        self.reddit.read_only = False
        with self.use_cassette():
            count = 0
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            async for item in subreddit.mod.modqueue():
                assert isinstance(item, (Comment, Submission))
                count += 1
            assert count > 0

    async def test_modqueue__only_comments(self):
        self.reddit.read_only = False
        with self.use_cassette():
            count = 0
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            async for item in subreddit.mod.modqueue(only="comments"):
                assert isinstance(item, Comment)
                count += 1
            assert count > 0

    async def test_modqueue__only_submissions(self):
        self.reddit.read_only = False
        with self.use_cassette():
            count = 0
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            async for item in subreddit.mod.modqueue(only="submissions"):
                assert isinstance(item, Submission)
                count += 1
            assert count > 0

    async def test_reports(self):
        self.reddit.read_only = False
        with self.use_cassette():
            count = 0
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            async for item in subreddit.mod.reports():
                assert isinstance(item, (Comment, Submission))
                count += 1
            assert count == 100

    async def test_reports__only_comments(self):
        self.reddit.read_only = False
        with self.use_cassette():
            count = 0
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            async for item in subreddit.mod.reports(only="comments"):
                assert isinstance(item, Comment)
                count += 1
            assert count > 0

    async def test_reports__only_submissions(self):
        self.reddit.read_only = False
        with self.use_cassette():
            count = 0
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            async for item in subreddit.mod.reports(only="submissions"):
                assert isinstance(item, Submission)
                count += 1
            assert count == 100

    async def test_spam(self):
        self.reddit.read_only = False
        with self.use_cassette():
            count = 0
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            async for item in subreddit.mod.spam():
                assert isinstance(item, (Comment, Submission))
                count += 1
            assert count > 0

    async def test_spam__only_comments(self):
        self.reddit.read_only = False
        with self.use_cassette():
            count = 0
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            async for item in subreddit.mod.spam(only="comments"):
                assert isinstance(item, Comment)
                count += 1
            assert count > 0

    async def test_spam__only_submissions(self):
        self.reddit.read_only = False
        with self.use_cassette():
            count = 0
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            async for item in subreddit.mod.spam(only="submissions"):
                assert isinstance(item, Submission)
                count += 1
            assert count > 0

    async def test_unmoderated(self):
        self.reddit.read_only = False
        with self.use_cassette():
            count = 0
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            async for item in subreddit.mod.unmoderated():
                assert isinstance(item, (Comment, Submission))
                count += 1
            assert count > 0

    async def test_unread(self):
        self.reddit.read_only = False
        with self.use_cassette():
            count = 0
            subreddit = await self.reddit.subreddit("all")
            async for item in subreddit.mod.unread():
                assert isinstance(item, SubredditMessage)
                count += 1
            assert count > 0

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_update(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            before_settings = await subreddit.mod.settings()
            new_title = f"{before_settings['title']}x"
            new_title = (
                "x"
                if (len(new_title) >= 20 and "placeholder" not in new_title)
                else new_title
            )
            await subreddit.mod.update(title=new_title)
            await subreddit.load()
            assert subreddit.title == new_title
            after_settings = await subreddit.mod.settings()

            # Ensure that nothing has changed besides what was specified.
            before_settings["title"] = new_title
            assert before_settings == after_settings


class TestSubredditModmail(IntegrationTest):
    async def test_bulk_read(self):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            conversations = await subreddit.modmail.bulk_read(state="new")
            for conversation in conversations:
                assert isinstance(conversation, ModmailConversation)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_call(self, _):
        self.reddit.read_only = False
        conversation_id = "fjhla"
        subreddit = await self.reddit.subreddit("all")
        with self.use_cassette():
            conversation = await subreddit.modmail(conversation_id)
            assert isinstance(conversation.user, Redditor)
            for message in conversation.messages:
                assert isinstance(message, ModmailMessage)
            for action in conversation.mod_actions:
                assert isinstance(action, ModmailAction)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_call__internal(self, _):
        self.reddit.read_only = False
        conversation_id = "ff1r8"
        subreddit = await self.reddit.subreddit("all")
        with self.use_cassette():
            conversation = await subreddit.modmail(conversation_id)
            for message in conversation.messages:
                assert isinstance(message, ModmailMessage)
            for action in conversation.mod_actions:
                assert isinstance(action, ModmailAction)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_call__mark_read(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit("all")
        with self.use_cassette():
            conversation = await subreddit.modmail("fccdg", mark_read=True)
            assert conversation.last_unread is None

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_conversations(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit("all")
        with self.use_cassette():
            async for conversation in subreddit.modmail.conversations():
                assert isinstance(conversation, ModmailConversation)
                assert isinstance(conversation.authors[0], Redditor)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_conversations__params(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit("all")
        with self.use_cassette():
            async for conversation in subreddit.modmail.conversations(state="mod"):
                assert conversation.is_internal

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_conversations__other_subreddits(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            conversations = await self.async_list(
                subreddit.modmail.conversations(other_subreddits=["dankmemes"])
            )
            assert len(set(conversation.owner for conversation in conversations)) > 1

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_create(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            redditor = await self.reddit.redditor(pytest.placeholders.username)
            conversation = await subreddit.modmail.create("Subject", "Body", redditor)
        assert isinstance(conversation, ModmailConversation)

    async def test_subreddits(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            async for subreddit in subreddit.modmail.subreddits():
                assert isinstance(subreddit, Subreddit)

    async def test_unread_count(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            assert isinstance(await subreddit.modmail.unread_count(), dict)


class TestSubredditQuarantine(IntegrationTest):
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_opt_in(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit("tiananmenaquarefalse")
        with self.use_cassette():
            with pytest.raises(Forbidden):
                await self.async_next(subreddit.top())
            await subreddit.quaran.opt_in()
            assert isinstance(await self.async_next(subreddit.top()), Submission)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_opt_out(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit("tiananmenaquarefalse")
        with self.use_cassette():
            await subreddit.quaran.opt_out()
            with pytest.raises(Forbidden):
                await self.async_next(subreddit.new())


class TestSubredditRelationships(IntegrationTest):
    REDDITOR = "pyapitestuser3"

    async def add_remove(self, base, user, relationship):
        relationship = getattr(base, relationship)
        await relationship.add(user)
        relationships = await self.async_list(relationship())
        assert user in relationships
        redditor = relationships[relationships.index(user)]
        assert isinstance(redditor, Redditor)
        assert hasattr(redditor, "date")
        await relationship.remove(user)
        assert user not in await self.async_list(relationship())

    async def test_banned(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await self.add_remove(subreddit, self.REDDITOR, "banned")

    async def test_banned__user_filter(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        banned = subreddit.banned(redditor="pyapitestuser3")
        with self.use_cassette():
            assert len(await self.async_list(banned)) == 1

    async def test_contributor(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await self.add_remove(subreddit, self.REDDITOR, "contributor")

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_contributor_leave(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await subreddit.contributor.leave()

    async def test_contributor__user_filter(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        contributor = subreddit.contributor(redditor="pyapitestuser3")
        with self.use_cassette():
            assert len(await self.async_list(contributor)) == 1

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_moderator(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            # Moderators can only be invited.
            # As of 2016-03-18 there is no API endpoint to get the moderator
            # invite list.
            await subreddit.moderator.add(self.REDDITOR)
            assert self.REDDITOR not in await subreddit.moderator()

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_moderator_aiter(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            async for moderator in subreddit.moderator:
                assert isinstance(moderator, Redditor)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_moderator__limited_permissions(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            # Moderators can only be invited.
            # As of 2016-03-18 there is no API endpoint to get the moderator
            # invite list.
            await subreddit.moderator.add(self.REDDITOR, permissions=["access", "wiki"])
            assert self.REDDITOR not in await subreddit.moderator()

    async def test_moderator_invite__invalid_perm(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            with pytest.raises(RedditAPIException) as excinfo:
                await subreddit.moderator.invite(self.REDDITOR, permissions=["a"])
            assert excinfo.value.items[0].error_type == "INVALID_PERMISSIONS"

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_moderator_invite__no_perms(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            # Moderators can only be invited.
            # As of 2016-03-18 there is no API endpoint to get the moderator
            # invite list.
            await subreddit.moderator.invite(self.REDDITOR, permissions=[])
            assert self.REDDITOR not in await subreddit.moderator()

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_moderator_invited_moderators(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            invited = subreddit.moderator.invited()
            assert isinstance(invited, ListingGenerator)
            async for moderator in invited:
                assert isinstance(moderator, Redditor)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_moderator_leave(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await subreddit.moderator.leave()

    async def test_moderator_update(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await subreddit.moderator.update(
                pytest.placeholders.username, permissions=["config"]
            )

    async def test_moderator_update_invite(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await subreddit.moderator.update_invite(self.REDDITOR, permissions=["mail"])

    async def test_moderator__user_filter(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            moderator = await subreddit.moderator(redditor=pytest.placeholders.username)
        assert len(moderator) == 1
        assert "mod_permissions" in moderator[0].__dict__

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_muted(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await self.add_remove(subreddit, self.REDDITOR, "muted")

    async def test_moderator_remove_invite(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await subreddit.moderator.remove_invite(self.REDDITOR)

    async def test_wiki_banned(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await self.add_remove(subreddit.wiki, self.REDDITOR, "banned")

    async def test_wiki_contributor(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await self.add_remove(subreddit.wiki, self.REDDITOR, "contributor")


class TestSubredditStreams(IntegrationTest):
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_comments(self, _):
        subreddit = await self.reddit.subreddit("all")
        with self.use_cassette():
            generator = subreddit.stream.comments()
            for i in range(400):
                assert isinstance(await self.async_next(generator), Comment)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_comments__with_pause(self, _):
        subreddit = await self.reddit.subreddit("askreddit")
        with self.use_cassette():
            comment_stream = subreddit.stream.comments(pause_after=0)
            comment_count = 1
            pause_count = 1
            comment = await self.async_next(comment_stream)
            while comment is not None:
                comment_count += 1
                comment = await self.async_next(comment_stream)
            while comment is None:
                pause_count += 1
                comment = await self.async_next(comment_stream)
            assert comment_count == 108
            assert pause_count == 3

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_comments__with_skip_existing(self, _):
        with self.use_cassette("TestSubredditStreams.test_comments__with_pause"):
            subreddit = await self.reddit.subreddit("askreddit")
            generator = subreddit.stream.comments(skip_existing=True)
            count = 0
            try:
                async for comment in generator:
                    count += 1
            except TypeError:
                pass
            # This test uses the same cassette as test_comments which shows
            # that there are at least 100 comments in the stream.
            assert count < 102

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_submissions(self, _):
        with self.use_cassette():
            subreddit = await self.reddit.subreddit("all")
            generator = subreddit.stream.submissions()
            for i in range(101):
                assert isinstance(await self.async_next(generator), Submission)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_submissions__with_pause(self, _):
        with self.use_cassette("TestSubredditStreams.test_submissions"):
            subreddit = await self.reddit.subreddit("all")
            generator = subreddit.stream.submissions(pause_after=-1)
            submission = await self.async_next(generator)
            submission_count = 0
            while submission is not None:
                submission_count += 1
                submission = await self.async_next(generator)
            assert submission_count == 100

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_submissions__with_pause_and_skip_after(self, _):
        with self.use_cassette("TestSubredditStreams.test_submissions"):
            subreddit = await self.reddit.subreddit("all")
            generator = subreddit.stream.submissions(pause_after=-1, skip_existing=True)
            submission = await self.async_next(generator)
            assert submission is None  # The first thing yielded should be None
            submission_count = 0
            submission = await self.async_next(generator)
            while submission is not None:
                submission_count += 1
                submission = await self.async_next(generator)
            assert submission_count < 100


class TestSubredditModerationStreams(IntegrationTest):
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_edited(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit("mod")
        with self.use_cassette():
            generator = subreddit.mod.stream.edited()
            for i in range(101):
                assert isinstance(
                    await self.async_next(generator), (Comment, Submission)
                )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_log(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit("mod")
        with self.use_cassette():
            generator = subreddit.mod.stream.log()
            for i in range(101):
                assert isinstance(await self.async_next(generator), ModAction)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_modmail_conversations(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit("mod")
        with self.use_cassette():
            generator = subreddit.mod.stream.modmail_conversations()
            for i in range(10):
                assert isinstance(await self.async_next(generator), ModmailConversation)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_modqueue(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit("mod")
        with self.use_cassette():
            generator = subreddit.mod.stream.modqueue()
            for i in range(10):
                assert isinstance(
                    await self.async_next(generator), (Comment, Submission)
                )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_spam(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit("mod")
        with self.use_cassette():
            generator = subreddit.mod.stream.spam()
            for i in range(101):
                assert isinstance(
                    await self.async_next(generator), (Comment, Submission)
                )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_reports(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit("mod")
        with self.use_cassette():
            generator = subreddit.mod.stream.reports()
            for i in range(10):
                assert isinstance(
                    await self.async_next(generator), (Comment, Submission)
                )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_unmoderated(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit("mod")
        with self.use_cassette():
            generator = subreddit.mod.stream.unmoderated()
            for i in range(101):
                assert isinstance(
                    await self.async_next(generator), (Comment, Submission)
                )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_unread(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit("mod")
        with self.use_cassette():
            generator = subreddit.mod.stream.unread()
            for i in range(2):
                assert isinstance(await self.async_next(generator), SubredditMessage)


class TestSubredditStylesheet(IntegrationTest):
    async def test_call(self):
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            stylesheet = await subreddit.stylesheet()
        assert isinstance(stylesheet, Stylesheet)
        assert len(stylesheet.images) > 0
        assert stylesheet.stylesheet != ""

    async def test_delete_banner(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await subreddit.stylesheet.delete_banner()

    async def test_delete_banner_additional_image(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await subreddit.stylesheet.delete_banner_additional_image()

    async def test_delete_banner_hover_image(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await subreddit.stylesheet.delete_banner_hover_image()

    async def test_delete_header(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await subreddit.stylesheet.delete_header()

    async def test_delete_image(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await subreddit.stylesheet.delete_image("praw")

    async def test_delete_mobile_header(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await subreddit.stylesheet.delete_mobile_header()

    async def test_delete_mobile_icon(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await subreddit.stylesheet.delete_mobile_icon()

    async def test_update(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await subreddit.stylesheet.update("p { color: red; }")

    async def test_update__with_reason(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await subreddit.stylesheet.update("div { color: red; }", reason="use div")

    async def test_upload(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            response = await subreddit.stylesheet.upload(
                "asyncpraw", image_path("white-square.png")
            )
        assert response["img_src"].endswith(".png")

    async def test_upload__invalid(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            with pytest.raises(RedditAPIException) as excinfo:
                await subreddit.stylesheet.upload(
                    "asyncpraw", image_path("invalid.jpg")
                )
        assert excinfo.value.items[0].error_type == "IMAGE_ERROR"

    async def test_upload__invalid_ext(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            with pytest.raises(RedditAPIException) as excinfo:
                await subreddit.stylesheet.upload(
                    "asyncpraw", image_path("white-square.png")
                )
        assert excinfo.value.items[0].error_type == "BAD_CSS_NAME"

    async def test_upload__too_large(self):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            with pytest.raises(TooLarge):
                await subreddit.stylesheet.upload(
                    "asyncpraw", image_path("too_large.jpg")
                )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_upload_banner__jpg(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await subreddit.stylesheet.upload_banner(image_path("white-square.jpg"))

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_upload_banner__png(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await subreddit.stylesheet.upload_banner(image_path("white-square.png"))

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_upload_banner_additional_image__jpg(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await subreddit.stylesheet.upload_banner_additional_image(
                image_path("white-square.jpg")
            )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_upload_banner_additional_image__png(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await subreddit.stylesheet.upload_banner_additional_image(
                image_path("white-square.png")
            )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_upload_banner_additional_image__align(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            for alignment in ("left", "centered", "right"):
                await subreddit.stylesheet.upload_banner_additional_image(
                    image_path("white-square.png"), align=alignment
                )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_upload_banner_hover_image__jpg(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await subreddit.stylesheet.upload_banner_additional_image(
                image_path("white-square.png")
            )
            await subreddit.stylesheet.upload_banner_hover_image(
                image_path("white-square.jpg")
            )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_upload_banner_hover_image__png(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            await subreddit.stylesheet.upload_banner_additional_image(
                image_path("white-square.jpg")
            )
            await subreddit.stylesheet.upload_banner_hover_image(
                image_path("white-square.png")
            )

    async def test_upload_header__jpg(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            response = await subreddit.stylesheet.upload_header(
                image_path("white-square.jpg")
            )
        assert response["img_src"].endswith(".jpg")

    async def test_upload_header__png(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            response = await subreddit.stylesheet.upload_header(
                image_path("white-square.png")
            )
        assert response["img_src"].endswith(".png")

    async def test_upload_mobile_header(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            response = await subreddit.stylesheet.upload_mobile_header(
                image_path("header.jpg")
            )
        assert response["img_src"].endswith(".jpg")

    async def test_upload_mobile_icon(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            response = await subreddit.stylesheet.upload_mobile_icon(
                image_path("icon.jpg")
            )
        assert response["img_src"].endswith(".jpg")

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_upload__others_invalid(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            for method in [
                "upload_header",
                "upload_mobile_header",
                "upload_mobile_icon",
            ]:
                with pytest.raises(RedditAPIException) as excinfo:
                    await getattr(subreddit.stylesheet, method)(
                        image_path("invalid.jpg")
                    )
                assert excinfo.value.items[0].error_type == "IMAGE_ERROR"

    async def test_upload__others_too_large(self):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            for method in [
                "upload_header",
                "upload_mobile_header",
                "upload_mobile_icon",
            ]:
                with pytest.raises(TooLarge):
                    await getattr(
                        subreddit.stylesheet,
                        method,
                    )(image_path("too_large.jpg"))


class TestSubredditWiki(IntegrationTest):
    @mock.patch("asyncio.sleep", return_value=None)
    async def test__aiter(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
        with self.use_cassette():
            count = 0
            async for wikipage in subreddit.wiki:
                assert isinstance(wikipage, WikiPage)
                count += 1
            assert count > 0

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_create(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)

        with self.use_cassette():
            wikipage = await subreddit.wiki.create(
                "Async PRAW New Page", "This is the new wiki page"
            )
            await wikipage.load()
            assert wikipage.name == "async_praw_new_page"
            assert wikipage.content_md == "This is the new wiki page"

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_revisions(self, _):
        self.reddit.read_only = False
        subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)

        with self.use_cassette():
            count = 0
            async for revision in subreddit.wiki.revisions(limit=2):
                count += 1
                assert isinstance(revision["author"], Redditor)
                assert isinstance(revision["page"], WikiPage)
            assert count == 2
