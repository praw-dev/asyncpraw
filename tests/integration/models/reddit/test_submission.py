import pytest
from asynctest import mock

from asyncpraw.exceptions import RedditAPIException
from asyncpraw.models import Comment, Submission

from ... import IntegrationTest


class TestSubmission(IntegrationTest):
    async def test_comments(self):
        with self.use_cassette():
            submission = await self.reddit.submission("2gmzqe")
            comments = await submission.comments()
            assert len(comments) == 1
            assert isinstance(comments[0], Comment)
            assert isinstance(comments[0].replies[0], Comment)

    async def test_clear_vote(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").clear_vote()

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_delete(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            submission = Submission(self.reddit, "hmkbt8")
            await submission.delete()
            await submission.load()
            assert submission.author is None
            assert submission.selftext == "[deleted]"

    async def test_disable_inbox_replies(self):
        self.reddit.read_only = False
        submission = Submission(self.reddit, "hmkbt8")
        with self.use_cassette():
            await submission.disable_inbox_replies()

    async def test_downvote(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").downvote()

    async def test_duplicates(self):
        with self.use_cassette():
            submission = Submission(self.reddit, "avj2v")
            assert len(await self.async_list(submission.duplicates())) > 0

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_edit(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            submission = Submission(self.reddit, "hmkbt8")
            await submission.edit("New text")
            assert submission.selftext == "New text"

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_edit_invalid(self, _):
        self.reddit.read_only = False
        self.reddit.validate_on_submit = True
        with self.use_cassette():
            submission = Submission(self.reddit, "hmkfoy")
            with pytest.raises(RedditAPIException):
                await submission.edit("rewtwert")

    async def test_enable_inbox_replies(self):
        self.reddit.read_only = False
        submission = Submission(self.reddit, "hmkbt8")
        with self.use_cassette():
            await submission.enable_inbox_replies()

    async def test_award(self):
        self.reddit.read_only = False
        with self.use_cassette():
            award_data = await Submission(self.reddit, "j3kyoo").award()
            assert award_data["gildings"]["gid_2"] == 2

    async def test_award__not_enough_coins(self):
        self.reddit.read_only = False
        with self.use_cassette():
            with pytest.raises(RedditAPIException) as excinfo:
                await Submission(self.reddit, "j3kyoo").award(
                    gild_type="award_2385c499-a1fb-44ec-b9b7-d260f3dc55de"
                )
            exception = excinfo.value
            assert "INSUFFICIENT_COINS_WITH_AMOUNT" == exception.error_type

    async def test_award__self_gild(self):
        self.reddit.read_only = False
        with self.use_cassette():
            with pytest.raises(RedditAPIException) as excinfo:
                await Submission(self.reddit, "j3fkiw").award(
                    gild_type="award_2385c499-a1fb-44ec-b9b7-d260f3dc55de"
                )
            exception = excinfo.value
            assert "SELF_GILDING_NOT_ALLOWED" == exception.error_type

    async def test_gild(self):
        self.reddit.read_only = False
        with self.use_cassette("TestSubmission.test_award"):
            award_data = await Submission(self.reddit, "j3kyoo").gild()
            assert award_data["gildings"]["gid_2"] == 2

    async def test_gilded(self):
        with self.use_cassette():
            submission = await self.reddit.submission("2gmzqe")
            assert 1 == submission.gilded

    async def test_hide(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").hide()

    async def test_hide_multiple(self):
        self.reddit.read_only = False
        submissions = [
            Submission(self.reddit, "fewoh"),
            Submission(self.reddit, "c625v"),
        ]
        with self.use_cassette():
            await Submission(self.reddit, "1eipl7").hide(submissions)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_hide_multiple_in_batches(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit("popular")
            submissions = await self.async_list(subreddit.hot(limit=100))
            assert len(submissions) == 100
            await submissions[0].hide(submissions[1:])

    async def test_invalid_attribute(self):
        with self.use_cassette():
            with pytest.raises(AttributeError) as excinfo:
                submission = await self.reddit.submission("2gmzqe")
                submission.invalid_attribute
        assert (
            excinfo.value.args[0]
            == "'Submission' object has no attribute 'invalid_attribute'"
        )

    async def test_reply(self):
        self.reddit.read_only = False
        with self.use_cassette():
            submission = Submission(self.reddit, "hmkbt8")
            comment = await submission.reply("Test reply")
            assert comment.author == pytest.placeholders.username
            assert comment.body == "Test reply"
            assert comment.parent_id == submission.fullname

    # async def test_reply__none(self): # TODO: I have not been able to reproduce this again; same with praw
    #     self.reddit.read_only = False
    #     submission = Submission(self.reddit, "ah19vv")
    #     with self.use_cassette():
    #         reply = submission.reply("TEST")
    #     assert reply is None

    async def test_report(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").report("praw")

    async def test_save(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").save()

    async def test_mark_visited(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkfoi").mark_visited()

    async def test_unhide(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").unhide()

    async def test_unhide_multiple(self):
        self.reddit.read_only = False
        submissions = [
            Submission(self.reddit, "fewoh"),
            Submission(self.reddit, "c625v"),
        ]
        with self.use_cassette():
            await Submission(self.reddit, "1eipl7").unhide(submissions)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_unhide_multiple_in_batches(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit("popular")
            submissions = await self.async_list(subreddit.hot(limit=100))
            assert len(submissions) == 100
            await submissions[0].unhide(submissions[1:])

    async def test_unsave(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").unsave()

    async def test_upvote(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").upvote()

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_crosspost(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = pytest.placeholders.test_subreddit
            crosspost_parent = await self.reddit.submission(id="6vx01b")

            submission = await crosspost_parent.crosspost(subreddit)
            await submission.load()
            assert submission.author == pytest.placeholders.username
            assert submission.title == "Test Title"
            assert submission.crosspost_parent == "t3_6vx01b"

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_crosspost__subreddit_object(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            crosspost_parent = await self.reddit.submission(id="6vx01b")

            submission = await crosspost_parent.crosspost(subreddit)
            await submission.load()
            assert submission.author == pytest.placeholders.username
            assert submission.title == "Test Title"
            assert submission.crosspost_parent == "t3_6vx01b"

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_crosspost__custom_title(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = await self.reddit.subreddit(pytest.placeholders.test_subreddit)
            crosspost_parent = await self.reddit.submission(id="6vx01b")

            submission = await crosspost_parent.crosspost(subreddit, "my title")
            await submission.load()
            assert submission.author == pytest.placeholders.username
            assert submission.title == "my title"
            assert submission.crosspost_parent == "t3_6vx01b"

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_crosspost__flair(self, _):
        flair_id = "94f13282-e2e8-11e8-8291-0eae4e167256"
        flair_text = "AF"
        flair_class = ""
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = pytest.placeholders.test_subreddit
            crosspost_parent = await self.reddit.submission(id="6vx01b")

            submission = await crosspost_parent.crosspost(
                subreddit, flair_id=flair_id, flair_text=flair_text
            )
            await submission.load()
            assert submission.link_flair_css_class == flair_class
            assert submission.link_flair_text == flair_text
            assert submission.crosspost_parent == "t3_6vx01b"

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_crosspost__nsfw(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = pytest.placeholders.test_subreddit
            crosspost_parent = await self.reddit.submission(id="6vx01b")

            submission = await crosspost_parent.crosspost(subreddit, nsfw=True)
            await submission.load()
            assert submission.over_18 is True
            assert submission.crosspost_parent == "t3_6vx01b"

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_crosspost__spoiler(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            subreddit = pytest.placeholders.test_subreddit
            crosspost_parent = await self.reddit.submission(id="6vx01b")

            submission = await crosspost_parent.crosspost(subreddit, spoiler=True)
            await submission.load()
            assert submission.spoiler is True
            assert submission.crosspost_parent == "t3_6vx01b"


class TestSubmissionFlair(IntegrationTest):
    @mock.patch("asyncio.sleep", return_value=None)
    async def test_choices(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            submission = Submission(self.reddit, "hmkbt8")
            expected = [
                {
                    "flair_css_class": "",
                    "flair_position": "right",
                    "flair_template_id": "94f13282-e2e8-11e8-8291-0eae4e167256",
                    "flair_text": "AF",
                    "flair_text_editable": True,
                }
            ]
            choices = await submission.flair.choices()
            assert expected == choices

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_select(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            submission = Submission(self.reddit, "hmkbt8")
            await submission.flair.select("94f13282-e2e8-11e8-8291-0eae4e167256")


class TestSubmissionModeration(IntegrationTest):
    async def test_approve(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").mod.approve()

    async def test_contest_mode(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").mod.contest_mode()

    async def test_contest_mode__disable(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").mod.contest_mode(state=False)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_flair(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").mod.flair("AF")

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_flair_template_id(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").mod.flair(
                "submission flair",
                flair_template_id="94f13282-e2e8-11e8-8291-0eae4e167256",
            )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_flair_text_only(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").mod.flair("submission flair")

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_flair_text_and_css_class(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").mod.flair(
                "submission flair", css_class="submission flair"
            )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_flair_all(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").mod.flair(
                "submission flair",
                css_class="submission flair",
                flair_template_id="94f13282-e2e8-11e8-8291-0eae4e167256",
            )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_flair_just_template_id(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").mod.flair(
                flair_template_id="94f13282-e2e8-11e8-8291-0eae4e167256"
            )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_flair_just_css_class(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").mod.flair(
                css_class="submission flair"
            )

    async def test_distinguish(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hrzz2x").mod.distinguish()

    async def test_ignore_reports(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").mod.ignore_reports()

    async def test_nsfw(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").mod.nsfw()

    async def test_lock(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").mod.lock()

    async def test_remove(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").mod.remove(spam=True)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_remove_with_reason_id(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").mod.remove(
                reason_id="159bqhvme3rxe"
            )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_add_removal_reason(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            submission = Submission(self.reddit, "hmkbt8")
            await submission.mod.remove()
            await submission.mod._add_removal_reason(
                mod_note="Foobar", reason_id="159bqhvme3rxe"
            )

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_add_removal_reason_without_id(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            submission = Submission(self.reddit, "hmkbt8")
            await submission.mod.remove()
            await submission.mod._add_removal_reason(mod_note="Foobar")

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_add_removal_reason_without_id_or_note(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            with pytest.raises(ValueError) as excinfo:
                submission = Submission(self.reddit, "hmkbt8")
                await submission.mod.remove()
                await submission.mod._add_removal_reason()
            assert excinfo.value.args[0].startswith("mod_note cannot be blank")

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_send_removal_message(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            submission = await self.reddit.submission("hmkutx")
            mod = submission.mod
            await mod.remove()
            message = "message"
            res = [
                await mod.send_removal_message(message, "Be Kind", type)
                for type in ("public", "private", "private_exposed")
            ]
            assert isinstance(res[0], Comment)
            assert res[0].parent_id == f"t3_{submission.id}"
            assert res[0].stickied
            assert res[0].body == message
            assert res[1] is None
            assert res[2] is None

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_set_original_content(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            submission = await self.reddit.submission("hmkbt8")
            assert not submission.is_original_content
            await submission.mod.set_original_content()
            submission = await self.reddit.submission("hmkbt8")
            assert submission.is_original_content

    async def test_sfw(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").mod.sfw()

    async def test_spoiler(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").mod.spoiler()

    async def test_sticky(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").mod.sticky()

    async def test_sticky__remove(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").mod.sticky(state=False)

    async def test_sticky__top(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").mod.sticky(bottom=False)

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_sticky__ignore_conflicts(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").mod.sticky(bottom=False)
            await Submission(self.reddit, "hmkbt8").mod.sticky(bottom=False)

    async def test_suggested_sort(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").mod.suggested_sort(sort="random")

    async def test_suggested_sort__clear(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").mod.suggested_sort(sort="blank")

    async def test_undistinguish(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hrzz2x").mod.undistinguish()

    async def test_unignore_reports(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").mod.unignore_reports()

    async def test_unlock(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").mod.unlock()

    @mock.patch("asyncio.sleep", return_value=None)
    async def test_unset_original_content(self, _):
        self.reddit.read_only = False
        with self.use_cassette():
            submission = await self.reddit.submission("hmkbt8")
            assert submission.is_original_content
            await submission.mod.unset_original_content()
            submission = await self.reddit.submission("hmkbt8")
            assert not submission.is_original_content

    async def test_unspoiler(self):
        self.reddit.read_only = False
        with self.use_cassette():
            await Submission(self.reddit, "hmkbt8").mod.unspoiler()
