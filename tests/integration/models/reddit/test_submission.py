import pytest

from asyncpraw.exceptions import ClientException, RedditAPIException
from asyncpraw.models import Comment, InlineGif, InlineImage, InlineVideo, Submission

from ... import IntegrationTest


class TestSubmission(IntegrationTest):
    @staticmethod
    def _inline_media(image_path):
        gif = InlineGif(caption="optional caption", path=image_path("test.gif"))
        image = InlineImage(caption="optional caption", path=image_path("test.png"))
        video = InlineVideo(caption="optional caption", path=image_path("test.mp4"))
        return {"gif1": gif, "image1": image, "video1": video}

    @staticmethod
    async def _new_submission_instance(
        reddit, submission_id, return_rtjson=False, fetch=True
    ):
        submission = Submission(reddit, submission_id)
        submission.add_fetch_param("rtj", "all")
        if fetch:
            await submission.load()
        if return_rtjson:
            return submission, submission.rtjson
        return submission

    async def test_award(self, reddit):
        reddit.read_only = False
        award_data = await Submission(reddit, "j3kyoo").award()
        assert award_data["gildings"]["gid_2"] == 2

    async def test_award__not_enough_coins(self, reddit):
        reddit.read_only = False
        with pytest.raises(RedditAPIException) as excinfo:
            await Submission(reddit, "j3kyoo").award(
                gild_type="award_2385c499-a1fb-44ec-b9b7-d260f3dc55de"
            )
        exception = excinfo.value
        assert "INSUFFICIENT_COINS_WITH_AMOUNT" == exception.items[0].error_type

    async def test_award__self_gild(self, reddit):
        reddit.read_only = False
        with pytest.raises(RedditAPIException) as excinfo:
            await Submission(reddit, "j3fkiw").award(
                gild_type="award_2385c499-a1fb-44ec-b9b7-d260f3dc55de"
            )
        exception = excinfo.value
        assert "SELF_GILDING_NOT_ALLOWED" == exception.items[0].error_type

    async def test_clear_vote(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").clear_vote()

    async def test_comments(self, reddit):
        submission = await reddit.submission("2gmzqe")
        assert len(submission.comments) == 1
        assert isinstance(submission.comments[0], Comment)
        assert isinstance(submission.comments[0].replies[0], Comment)

    async def test_crosspost(self, reddit):
        reddit.read_only = False
        subreddit = pytest.placeholders.test_subreddit
        crosspost_parent = await reddit.submission("6vx01b")

        submission = await crosspost_parent.crosspost(subreddit)
        await submission.load()
        assert submission.author == pytest.placeholders.username
        assert submission.title == "Test Title"
        assert submission.crosspost_parent == "t3_6vx01b"

    async def test_crosspost__custom_title(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        crosspost_parent = await reddit.submission("6vx01b")

        submission = await crosspost_parent.crosspost(subreddit, title="my title")
        await submission.load()
        assert submission.author == pytest.placeholders.username
        assert submission.title == "my title"
        assert submission.crosspost_parent == "t3_6vx01b"

    async def test_crosspost__flair(self, reddit):
        flair_id = "94f13282-e2e8-11e8-8291-0eae4e167256"
        flair_text = "AF"
        flair_class = ""
        reddit.read_only = False
        subreddit = pytest.placeholders.test_subreddit
        crosspost_parent = await reddit.submission("6vx01b")

        submission = await crosspost_parent.crosspost(
            subreddit, flair_id=flair_id, flair_text=flair_text
        )
        await submission.load()
        assert submission.link_flair_css_class == flair_class
        assert submission.link_flair_text == flair_text
        assert submission.crosspost_parent == "t3_6vx01b"

    async def test_crosspost__nsfw(self, reddit):
        reddit.read_only = False
        subreddit = pytest.placeholders.test_subreddit
        crosspost_parent = await reddit.submission("6vx01b")

        submission = await crosspost_parent.crosspost(subreddit, nsfw=True)
        await submission.load()
        assert submission.over_18 is True
        assert submission.crosspost_parent == "t3_6vx01b"

    async def test_crosspost__spoiler(self, reddit):
        reddit.read_only = False
        subreddit = pytest.placeholders.test_subreddit
        crosspost_parent = await reddit.submission("6vx01b")

        submission = await crosspost_parent.crosspost(subreddit, spoiler=True)
        await submission.load()
        assert submission.spoiler is True
        assert submission.crosspost_parent == "t3_6vx01b"

    async def test_crosspost__subreddit_object(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        crosspost_parent = await reddit.submission("6vx01b")

        submission = await crosspost_parent.crosspost(subreddit)
        await submission.load()
        assert submission.author == pytest.placeholders.username
        assert submission.title == "Test Title"
        assert submission.crosspost_parent == "t3_6vx01b"

    async def test_delete(self, reddit):
        reddit.read_only = False
        submission = Submission(reddit, "hmkbt8")
        await submission.delete()
        await submission.load()
        assert submission.author is None
        assert submission.selftext == "[deleted]"

    async def test_disable_inbox_replies(self, reddit):
        reddit.read_only = False
        submission = Submission(reddit, "hmkbt8")
        await submission.disable_inbox_replies()

    async def test_downvote(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").downvote()

    async def test_duplicates(self, reddit):
        submission = Submission(reddit, "avj2v")
        assert len(await self.async_list(submission.duplicates())) > 0

    async def test_edit(self, reddit):
        reddit.read_only = False
        submission = Submission(reddit, "hmkbt8")
        await submission.edit("New text")
        assert submission.selftext == "New text"

    # the edit inline media tests need to recorded in a specific order.
    async def test_edit__existing_and_new_inline_media(self, image_path, reddit):
        # 4th
        reddit.read_only = False
        inline_media = self._inline_media(image_path)
        submission, original_rtjson = await self._new_submission_instance(
            reddit, "mcqjl8", True
        )
        submission2 = await self._new_submission_instance(reddit, "mcqjl8", fetch=False)
        new_selftext = (
            "\n\nNew text with a gif {gif1} an image {image1} and a video {video1}"
            " inline"
        )
        await submission._edit_experimental(
            submission.selftext + new_selftext,
            inline_media=inline_media,
            preserve_inline_media=True,
        )
        await submission2.load()
        added_rtjson = await submission2.subreddit._convert_to_fancypants(
            new_selftext.format(**inline_media)
        )
        assert (
            original_rtjson["document"] + added_rtjson["document"]
        ) == submission2.rtjson["document"]

    async def test_edit__existing_inline_media(self, reddit):
        # 3rd
        reddit.read_only = False
        submission, original_rtjson = await self._new_submission_instance(
            reddit, "mcqjl8", True
        )
        submission2 = await self._new_submission_instance(reddit, "mcqjl8", fetch=False)
        assert not submission2._fetched
        await submission._edit_experimental(
            submission.selftext, preserve_inline_media=True
        )
        await submission2.load()
        assert original_rtjson == submission2.rtjson

    async def test_edit__experimental(self, reddit):
        # 1st
        reddit.read_only = False
        submission = Submission(reddit, "mcqjl8")
        await submission._edit_experimental("New text")
        assert submission.selftext == "New text"

    async def test_edit__new_inline_media(self, image_path, reddit):
        # 2nd
        reddit.read_only = False
        inline_media = self._inline_media(image_path)
        submission, original_rtjson = await self._new_submission_instance(
            reddit, "mcqjl8", True
        )
        submission2 = await self._new_submission_instance(reddit, "mcqjl8", fetch=False)
        additional_selftext = (
            "\n\nNew Text with a gif {gif1} an image {image1} and a video {video1}"
            " inline"
        )
        await submission._edit_experimental(
            submission.selftext + additional_selftext,
            inline_media=inline_media,
        )
        await submission2.load()
        added_rtjson = await submission2.subreddit._convert_to_fancypants(
            additional_selftext.format(**inline_media)
        )
        assert (
            original_rtjson["document"] + added_rtjson["document"]
        ) == submission2.rtjson["document"]

    async def test_edit_invalid(self, reddit):
        reddit.read_only = False
        reddit.validate_on_submit = True
        submission = Submission(reddit, "hmkfoy")
        with pytest.raises(RedditAPIException):
            await submission.edit("rewtwert")

    async def test_enable_inbox_replies(self, reddit):
        reddit.read_only = False
        submission = Submission(reddit, "hmkbt8")
        await submission.enable_inbox_replies()

    async def test_gilded(self, reddit):
        submission = await reddit.submission("2gmzqe")
        assert 1 == submission.gilded

    async def test_hide(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").hide()

    async def test_hide_multiple(self, reddit):
        reddit.read_only = False
        submissions = [
            Submission(reddit, "fewoh"),
            Submission(reddit, "c625v"),
        ]
        await Submission(reddit, "1eipl7").hide(other_submissions=submissions)

    async def test_hide_multiple_in_batches(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit("popular")
        submissions = await self.async_list(subreddit.hot(limit=100))
        assert len(submissions) == 100
        await submissions[0].hide(other_submissions=submissions[1:])

    async def test_invalid_attribute(self, reddit):
        with pytest.raises(AttributeError) as excinfo:
            submission = await reddit.submission("2gmzqe")
            submission.invalid_attribute
        assert (
            excinfo.value.args[0]
            == "'Submission' object has no attribute 'invalid_attribute'"
        )

    async def test_mark_visited(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkfoi").mark_visited()

    async def test_reply(self, reddit):
        reddit.read_only = False
        submission = Submission(reddit, "hmkbt8")
        comment = await submission.reply("Test reply")
        assert comment.author == pytest.placeholders.username
        assert comment.body == "Test reply"
        assert comment.parent_id == submission.fullname

    # async def test_reply__none(self, reddit): # TODO: I have not been able to reproduce this again; same with praw
    #     reddit.read_only = False
    #     submission = Submission(reddit, "ah19vv")
    #     reply = submission.reply("TEST")
    #     assert reply is None

    async def test_report(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").report("praw")

    async def test_resolve_from_share_url(self, reddit):
        url = "https://www.reddit.com/r/redditdev/s/WNauetbiNG"
        assert await reddit.submission(url=url) == "2gmzqe", url

    async def test_resolve_from_share_url__invalid_url(self, reddit):
        url = "https://reddit.com/r/space/s/"
        with pytest.raises(ClientException):
            await reddit.submission(url=url)

    async def test_save(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").save()

    async def test_unhide(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").unhide()

    async def test_unhide_multiple(self, reddit):
        reddit.read_only = False
        submissions = [
            Submission(reddit, "fewoh"),
            Submission(reddit, "c625v"),
        ]
        await Submission(reddit, "1eipl7").unhide(other_submissions=submissions)

    async def test_unhide_multiple_in_batches(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit("popular")
        submissions = await self.async_list(subreddit.hot(limit=100))
        assert len(submissions) == 100
        await submissions[0].unhide(other_submissions=submissions[1:])

    async def test_unsave(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").unsave()

    async def test_upvote(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").upvote()


class TestSubmissionFlair(IntegrationTest):
    async def test_choices(self, reddit):
        reddit.read_only = False
        submission = Submission(reddit, "hmkbt8")
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

    async def test_select(self, reddit):
        reddit.read_only = False
        submission = Submission(reddit, "hmkbt8")
        await submission.flair.select("94f13282-e2e8-11e8-8291-0eae4e167256")


class TestSubmissionModeration(IntegrationTest):
    async def test_add_removal_reason(self, reddit):
        reddit.read_only = False
        submission = Submission(reddit, "hmkbt8")
        await submission.mod.remove()
        await submission.mod._add_removal_reason(
            mod_note="Foobar", reason_id="159bqhvme3rxe"
        )

    async def test_add_removal_reason_without_id(self, reddit):
        reddit.read_only = False
        submission = Submission(reddit, "hmkbt8")
        await submission.mod.remove()
        await submission.mod._add_removal_reason(mod_note="Foobar")

    async def test_add_removal_reason_without_id_or_note(self, reddit):
        reddit.read_only = False
        with pytest.raises(ValueError) as excinfo:
            submission = Submission(reddit, "hmkbt8")
            await submission.mod.remove()
            await submission.mod._add_removal_reason()
        assert excinfo.value.args[0].startswith("mod_note cannot be blank")

    async def test_approve(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").mod.approve()

    async def test_contest_mode(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").mod.contest_mode()

    async def test_contest_mode__disable(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").mod.contest_mode(state=False)

    async def test_distinguish(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hrzz2x").mod.distinguish()

    async def test_flair(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").mod.flair(text="AF")

    async def test_flair_all(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").mod.flair(
            text="submission flair",
            css_class="submission flair",
            flair_template_id="94f13282-e2e8-11e8-8291-0eae4e167256",
        )

    async def test_flair_just_css_class(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").mod.flair(css_class="submission flair")

    async def test_flair_just_template_id(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").mod.flair(
            flair_template_id="94f13282-e2e8-11e8-8291-0eae4e167256"
        )

    async def test_flair_template_id(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").mod.flair(
            text="submission flair",
            flair_template_id="94f13282-e2e8-11e8-8291-0eae4e167256",
        )

    async def test_flair_text_and_css_class(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").mod.flair(
            text="submission flair", css_class="submission flair"
        )

    async def test_flair_text_only(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").mod.flair(text="submission flair")

    async def test_ignore_reports(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").mod.ignore_reports()

    async def test_lock(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").mod.lock()

    async def test_notes(self, reddit):
        reddit.read_only = False
        submission = await reddit.submission("uflrmv")
        note = await submission.mod.create_note(label="HELPFUL_USER", note="test note")
        notes = await self.async_list(submission.mod.author_notes())
        assert note in notes
        assert notes[notes.index(note)].user == submission.author

    async def test_nsfw(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").mod.nsfw()

    async def test_remove(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").mod.remove(spam=True)

    async def test_remove_with_reason_id(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").mod.remove(reason_id="159bqhvme3rxe")

    async def test_send_removal_message(self, reddit):
        reddit.read_only = False
        submission = await reddit.submission("hmkutx")
        mod = submission.mod
        await mod.remove()
        message = "message"
        res = [
            await mod.send_removal_message(message=type, title="title", type=message)
            for type in ("public", "private", "private_exposed")
        ]
        assert isinstance(res[0], Comment)
        assert res[0].parent_id == f"t3_{submission.id}"
        assert res[0].stickied
        assert res[0].body == message
        assert res[1] is None
        assert res[2] is None

    async def test_set_original_content(self, reddit):
        reddit.read_only = False
        submission = await reddit.submission("hmkbt8")
        assert not submission.is_original_content
        await submission.mod.set_original_content()
        submission = await reddit.submission("hmkbt8")
        assert submission.is_original_content

    async def test_sfw(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").mod.sfw()

    async def test_spoiler(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").mod.spoiler()

    async def test_sticky(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").mod.sticky()

    async def test_sticky__ignore_conflicts(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").mod.sticky(bottom=False)
        await Submission(reddit, "hmkbt8").mod.sticky(bottom=False)

    async def test_sticky__remove(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").mod.sticky(state=False)

    async def test_sticky__top(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").mod.sticky(bottom=False)

    async def test_suggested_sort(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").mod.suggested_sort(sort="random")

    async def test_suggested_sort__clear(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").mod.suggested_sort(sort="blank")

    async def test_undistinguish(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hrzz2x").mod.undistinguish()

    async def test_unignore_reports(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").mod.unignore_reports()

    async def test_unlock(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").mod.unlock()

    async def test_unset_original_content(self, reddit):
        reddit.read_only = False
        submission = await reddit.submission("hmkbt8")
        assert submission.is_original_content
        await submission.mod.unset_original_content()
        submission = await reddit.submission("hmkbt8")
        assert not submission.is_original_content

    async def test_unspoiler(self, reddit):
        reddit.read_only = False
        await Submission(reddit, "hmkbt8").mod.unspoiler()

    async def test_update_crowd_control_level(self, reddit):
        reddit.read_only = False
        submission = await reddit.submission("ol4d5w")
        await submission.mod.update_crowd_control_level(2)
        modlog = await self.async_next(
            submission.subreddit.mod.log(
                action="adjust_post_crowd_control_level", limit=1
            )
        )
        assert modlog.action == "adjust_post_crowd_control_level"
        assert modlog.details == "medium"
        assert modlog.target_fullname == submission.fullname
