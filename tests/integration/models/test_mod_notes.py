import pytest

from .. import IntegrationTest


class TestModNotes(IntegrationTest):
    REDDITOR = "pyapitestuser3"

    async def test_create_note__submission(self, reddit):
        reddit.read_only = False
        submission = await reddit.submission("uflrmv")
        result_note = await submission.mod.create_note(
            label="HELPFUL_USER", note="test note"
        )
        assert result_note.user == submission.author
        assert result_note.note == "test note"
        assert result_note.label == "HELPFUL_USER"

    async def test_create_note__thing_fullname(self, reddit):
        reddit.read_only = False
        submission = await reddit.submission("uflrmv")
        result_note = await reddit.notes.create(
            label="HELPFUL_USER", note="test note", thing=submission.fullname
        )
        assert result_note.user == submission.author
        assert result_note.id.startswith("ModNote")
        assert result_note.moderator.name == pytest.placeholders.username
        assert result_note.note == "test note"
        assert result_note.label == "HELPFUL_USER"
        assert result_note.reddit_id == submission.fullname

    @pytest.mark.cassette_name("TestModNotes.test_create_note__submission")
    async def test_create_note__thing_submission(self, reddit):
        reddit.read_only = False
        submission = await reddit.submission("uflrmv")
        result_note = await reddit.notes.create(
            label="HELPFUL_USER", note="test note", thing=submission
        )
        assert result_note.user == submission.author
        assert result_note.note == "test note"

    async def test_delete_note(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        result_note = await subreddit.mod.notes.create(
            redditor=self.REDDITOR, note="test note"
        )
        await subreddit.mod.notes.delete(
            note_id=result_note.id, redditor=result_note.user
        )
        notes = await self.async_list(subreddit.mod.notes.redditors(self.REDDITOR))
        assert result_note not in notes

    async def test_delete_note__all_notes(self, reddit):
        reddit.read_only = False
        subreddit = await reddit.subreddit(pytest.placeholders.test_subreddit)
        result_note = await subreddit.mod.notes.create(
            redditor=self.REDDITOR, note="test note"
        )
        await subreddit.mod.notes.delete(delete_all=True, redditor=result_note.user)
        notes = await self.async_list(subreddit.mod.notes.redditors(self.REDDITOR))
        assert len(notes) == 0
