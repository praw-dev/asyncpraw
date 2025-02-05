"""This file should be updated as files/classes/functions are deprecated."""

import pytest

from asyncpraw import Reddit
from asyncpraw.models import Comment, Subreddit
from asyncpraw.exceptions import WebSocketException
from asyncpraw.models.reddit.user_subreddit import UserSubreddit
from asyncpraw.util.token_manager import FileTokenManager

from . import UnitTest


@pytest.mark.filterwarnings("error", category=DeprecationWarning)
class TestDeprecation(UnitTest):
    async def test_comment_forest_async_iterator(self, reddit):
        submission = await reddit.submission("1234", fetch=False)
        submission._fetched = True
        submission.comments._comments = [Comment(None, id="1234")]
        with pytest.deprecated_call():
            async for comment in submission.comments:
                assert isinstance(comment, Comment)

    async def test_comment_forest_list_async(self, reddit):
        submission = await reddit.submission("1234", fetch=False)
        submission._fetched = True
        submission.comments._comments = []
        with pytest.deprecated_call():
            await submission.comments.list()

    async def test_conversations_after_argument(self, reddit):
        with pytest.deprecated_call():
            subreddit = await reddit.subreddit("all")
            subreddit.modmail.conversations(after="after")

    async def test_gild_method(self, reddit):
        with pytest.deprecated_call() as warning_info:
            submission = await reddit.submission("1234", fetch=False)
            await submission.gild()
            assert (
                str(warning_info.list[0].message)
                == "'.gild' has been renamed to '.award'."
            )

    def test_gold_method(self, reddit):
        with pytest.deprecated_call() as warning_info:
            reddit.subreddits.gold()
            assert (
                str(warning_info.list[0].message)
                == "'subreddits.gold' has be renamed to 'subreddits.premium'."
            )

    async def test_lazy_argument_rename(self, reddit):
        with pytest.deprecated_call() as warning_info:
            await reddit.submission("1234", lazy=True)
        assert (
            str(warning_info.list[0].message)
            == "The parameter ``lazy`` has been renamed to ``fetch`` and support for"
            " the ``lazy`` parameter will be removed in a future version of Async PRAW."
        )

    async def test_reddit_token_manager(self):
        with pytest.deprecated_call():
            async with Reddit(
                token_manager=FileTokenManager("name"),
                client_id="dummy",
                client_secret=None,
                redirect_uri="dummy",
                user_agent="dummy",
            ):
                pass

    async def test_reddit_user_me_read_only(self, reddit):
        with pytest.deprecated_call():
            await reddit.user.me()

    async def test_submission_comments_async(self, reddit):
        submission = await reddit.submission("1234", fetch=False)
        submission._fetched = True
        with pytest.deprecated_call():
            await submission.comments()

    async def test_subreddit_rules_call(self, reddit):
        with pytest.deprecated_call() as warning_info:
            subreddit = Subreddit(reddit, display_name="test")
            await subreddit.rules()
        assert (
            str(warning_info.list[0].message)
            == "Calling SubredditRules to get a list of rules is deprecated. Remove the"
            " parentheses to use the iterator. View the Async PRAW documentation on how"
            " to change the code in order to use the iterator"
            " (https://asyncpraw.readthedocs.io/en/latest/code_overview/other/subredditrules.html#asyncpraw.models.reddit.rules.SubredditRules.__call__)."
        )

    async def test_synchronous_context_manager(self, reddit):
        with pytest.deprecated_call() as warning_info:
            with reddit:
                pass
            assert (
                str(warning_info.list[0].message)
                == "Using this class as a synchronous context manager is deprecated and"
                " will be removed in the next release. Use this class as an"
                " asynchronous context manager instead."
            )

    def test_user_subreddit_as_dict(self):
        user_subreddit = UserSubreddit(None, display_name="test")
        with pytest.deprecated_call() as warning_info:
            display_name = user_subreddit["display_name"]
            assert display_name == "test"
            assert (
                warning_info.list[0].message.args[0]
                == "'Redditor.subreddit' is no longer a dict and is now an"
                " UserSubreddit object. Accessing attributes using string indices is"
                " deprecated."
            )
            assert user_subreddit.keys() == user_subreddit.__dict__.keys()
            assert (
                warning_info.list[1].message.args[0]
                == "'Redditor.subreddit' is no longer a dict and is now an"
                " UserSubreddit object. Using 'keys' is deprecated and will be removed"
                " in Async PRAW 8."
            )
