"""Test asyncpraw.models.mod_notes."""

import pytest

from asyncpraw.models import Redditor, Subreddit

from .. import UnitTest


class TestBaseModNotes(UnitTest):
    async def test__ensure_attribute__(self):
        with pytest.raises(TypeError) as excinfo:
            Subreddit(None, "a").mod.notes._ensure_attribute(
                error_message="error", redditor=None
            )
        assert excinfo.value.args[0] == "error"

    async def test_notes_delete__missing_note_id(self):
        with pytest.raises(TypeError) as excinfo:
            await Subreddit(None, "a").mod.notes.delete(redditor="redditor")
        assert (
            excinfo.value.args[0]
            == "Either 'note_id' or 'delete_all' must be provided."
        )


class TestRedditModNotes(UnitTest):
    def test__call__invalid_thing_type(self, reddit):
        with pytest.raises(TypeError) as excinfo:
            reddit.notes(things=[1])
        assert (
            excinfo.value.args[0]
            == "Cannot get subreddit and author fields from type <class 'int'>"
        )

    def test__call__missing_arguments(self, reddit):
        with pytest.raises(TypeError) as excinfo:
            reddit.notes()
        assert (
            excinfo.value.args[0]
            == "Either the 'pairs', 'redditors', 'subreddits', or 'things' parameters must be provided."
        )

    def test__call__redditors_missing_subreddits(self, reddit):
        with pytest.raises(TypeError) as excinfo:
            reddit.notes(subreddits=[1])
        assert (
            excinfo.value.args[0]
            == "'redditors' must be non-empty if 'subreddits' is not empty."
        )


class TestRedditorModNotes(UnitTest):
    def test_subreddits__missing_argument(self):
        with pytest.raises(ValueError) as excinfo:
            Redditor(None, "a").notes.subreddits()
        assert excinfo.value.args[0] == "At least 1 subreddit must be provided."


class TestSubredditModNotes(UnitTest):
    def test_subreddits__missing_argument(self):
        with pytest.raises(ValueError) as excinfo:
            Subreddit(None, "a").mod.notes.redditors()
        assert excinfo.value.args[0] == "At least 1 redditor must be provided."
