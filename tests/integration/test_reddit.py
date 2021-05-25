"""Test asyncpraw.reddit."""
from base64 import urlsafe_b64encode

import pytest
from asyncprawcore.exceptions import BadRequest, ServerError
from asynctest import mock

from asyncpraw.exceptions import RedditAPIException
from asyncpraw.models import LiveThread
from asyncpraw.models.reddit.base import RedditBase
from asyncpraw.models.reddit.submission import Submission
from asyncpraw.models.reddit.subreddit import Subreddit

from . import IntegrationTest


class TestReddit(IntegrationTest):
    async def test_bad_request_without_json_text_plain_response(self):
        with open("tests/integration/files/too_large.jpg", "rb") as fp:
            junk = urlsafe_b64encode(fp.read()).decode()
        with self.use_cassette():
            with pytest.raises(RedditAPIException) as excinfo:
                await self.reddit.request(
                    "GET",
                    f"/api/morechildren?link_id=t3_n7r3uz&children={junk}",
                )
            assert str(excinfo.value) == "Bad Request"

    async def test_bad_request_without_json_text_html_response(self):
        with open("tests/integration/files/comment_ids.txt") as fp:
            ids = fp.read()[:8000]
        with self.use_cassette():
            with pytest.raises(RedditAPIException) as excinfo:
                await self.reddit.request(
                    "GET",
                    f"/api/morechildren?link_id=t3_n7r3uz&children={ids}",
                )
            assert (
                str(excinfo.value)
                == "<html><body><h1>400 Bad request</h1>\nYour browser sent an invalid request.\n</body></html>\n"
            )

    async def test_bare_badrequest(self):
        data = {
            "sr": "AskReddit",
            "field": "link",
            "kind": "link",
            "title": "l",
            "text": "lol",
            "show_error_list": True,
        }
        self.reddit.read_only = False
        with self.use_cassette():
            with pytest.raises(BadRequest):
                await self.reddit.post("/api/validate_submission_field", data=data)

    async def test_info(self):
        bases = ["t1_d7ltv", "t3_5dec", "t5_2qk"]
        items = []
        for i in range(100):
            for base in bases:
                items.append(f"{base}{i:02d}")

        with self.use_cassette():
            results = await self.async_list(self.reddit.info(items))
        assert len(results) > 100
        for item in results:
            assert isinstance(item, RedditBase)

    async def test_info_url(self):
        with self.use_cassette():
            results = await self.async_list(self.reddit.info(url="youtube.com"))
        assert len(results) > 0
        for item in results:
            assert isinstance(item, Submission)

    async def test_info_sr_names(self):
        items = [await self.reddit.subreddit("redditdev"), "reddit.com", "t:1337", "nl"]
        item_generator = self.reddit.info(subreddits=items)
        with self.use_cassette():
            results = await self.async_list(item_generator)
        assert len(results) == 4
        for item in results:
            assert isinstance(item, Subreddit)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_live_call(self, _):
        thread_id = "ukaeu1ik4sw5"
        with self.use_cassette():
            thread = await self.reddit.live(thread_id, fetch=True)
            assert thread.title == "reddit updates"

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_live_create(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            live = await self.reddit.live.create("PRAW Create Test")
            assert isinstance(live, LiveThread)
            await live._fetch()
            assert live.title == "PRAW Create Test"

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_live_info__contain_invalid_id(self, _):
        gen = self.reddit.live.info(["invalid"])
        with self.use_cassette():
            with pytest.raises(ServerError):
                await self.async_list(gen)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_live_info(self, _):
        ids = """
        ta40aifzobnv ta40l9u2ermf ta40ucdiq366 ta416hjgvbhy ta41ln5vsyaz
        ta42cyzy1nze ta42i49806k0 ta436ojd653m ta43945wgmaa ta43znjvza9t
        ta4418kxie3z ta44mk0nllhm ta45j0yvww9t ta4613lzdh8q ta46l8k86jt9
        ta47qua0xu3n ta489fm9515p ta48ml5k1uk9 ta48zy4jzjcb ta49irvwndau
        ta49upckgoyw ta4a02h9ynsb ta4aa4lrgvst ta4alauoi8ws ta4aqyacr70u

        ta4ekdk6m5g2 ta4ezvoc49gy ta4f3iv06c1n ta4ffvliq5l7 ta4fib9lx3zx
        ta4gka0ll41h ta4h89f6isfg ta4ht7s8he49 ta4i1eb564ar ta4imxhap4fg
        ta4iu3g9whtk ta4j3o05j0d3 ta4kloqi6csg ta4m6kj44dql ta4mlqtihiil
        ta4ng30l3fz1 ta4nldsjimhu ta4pd78tuk29 ta4prwyy1w9i ta4pvu8y6f8o
        ta4ray2odqub ta4rua4oe6a1 ta4tk9fwjgz1 ta4trgqw6mmx ta4tv3sen7u4

        ta4uyh0fnc0a ta4v54gnggcl ta4v5cm004z1 ta4vortaefna ta4wqym9d0v3
        ta4wsuouxjtm ta4x7jr9v0fn ta4yast5e96b ta4z337yzlgu ta4zo9zzo9ui
        ta507u2euo3w ta50exn0mtx1 ta51x2crezff ta52ch48gn6l ta53ijowvc6z
        ta53iy196uod ta541cz1hfb4 ta54n0ncx8pc ta55ytfmre2g ta581bybyjwi
        ta59gcidn2ym ta59mkwnrd43 ta5ar22wzi2w ta5awwo42ibb ta5dhmvylw0l

        ta5hipd6wahr ta5itb7clg3s ta5nlm09y8kb ta5nm0f831x1 ta5oavbflorf
        ta5rnv18s85o ta5ru6ysh254 ta5sfz02nc8b ta5syawj086b ta5t41osygln
        ta5uy3ynoo4a ta5w0seb1xfy ta5wddbh0ln0 ta5zmjzuijwo ta617ozbmxhb
        ta64q6pjz2bs ta696fdie4ne ta6bmog7gvoq ta6f9y7sdzru ta6j838d2wjn
        ta6l4q5c17fd ta6ofypk3yp2 ta6sjmjt1aeb ta6sqhgyv41q ta70eezhz50r

        ta72azs1l4u9 ta74r3dp2pt5 ta7pfcqdx9cl ta8zxbt2sk6z ta94nde51q4i
        """.split()
        gen = self.reddit.live.info(ids)
        with self.use_cassette():
            threads = await self.async_list(gen)
        assert len(threads) > 100
        assert all(isinstance(thread, LiveThread) for thread in threads)
        thread_ids = [thread.id for thread in threads]
        assert thread_ids == ids

    # async def test_live_now__featured(self): # TODO: record when something is featured
    #     with self.use_cassette():
    #         thread = await self.reddit.live.now()
    #     assert isinstance(thread, LiveThread)
    #     assert thread.id == "z2f981agq7ky"

    async def test_live_now__no_featured(self):
        with self.use_cassette():
            now = await self.reddit.live.now()
            assert now is None

    async def test_random_subreddit(self):
        names = set()
        with self.use_cassette():
            for i in range(3):
                sub = await self.reddit.random_subreddit()
                names.add(sub.display_name)
        assert len(names) == 3

    async def test_subreddit_with_randnsfw(self):
        with self.use_cassette():
            subreddit = await self.reddit.subreddit("randnsfw")
            assert subreddit.display_name != "randnsfw"
            assert subreddit.over18

    async def test_subreddit_with_random(self):
        with self.use_cassette():
            subreddit = await self.reddit.subreddit("random")
            assert subreddit.display_name != "random"

    async def test_username_available__available(self):
        fake_user = "prawtestuserabcd1234"
        with self.use_cassette():
            assert await self.reddit.username_available(fake_user)

    async def test_username_available__unavailable(self):
        with self.use_cassette():
            assert not await self.reddit.username_available("bboe")

    async def test_username_available_exception(self):
        with self.use_cassette():
            with pytest.raises(RedditAPIException) as exc:
                await self.reddit.username_available("a")
            assert str(exc.value) == "BAD_USERNAME: 'invalid user name' on field 'user'"


class TestDomainListing(IntegrationTest):
    async def test_controversial(self):
        with self.use_cassette():
            submissions = await self.async_list(
                self.reddit.domain("youtube.com").controversial()
            )
        assert len(submissions) == 100

    async def test_hot(self):
        with self.use_cassette():
            submissions = await self.async_list(self.reddit.domain("youtube.com").hot())
        assert len(submissions) == 100

    async def test_new(self):
        with self.use_cassette():
            submissions = await self.async_list(self.reddit.domain("youtube.com").new())
        assert len(submissions) == 100

    async def test_random_rising(self):
        with self.use_cassette():
            submissions = await self.async_list(
                self.reddit.domain("youtube.com").random_rising()
            )
        assert len(submissions) == 100

    async def test_rising(self):
        with self.use_cassette():
            await self.async_list(self.reddit.domain("youtube.com").rising())

    async def test_top(self):
        with self.use_cassette():
            submissions = await self.async_list(self.reddit.domain("youtube.com").top())
        assert len(submissions) == 100
