Change Log
==========

Async PRAW follows `semantic versioning <http://semver.org/>`_.

7.3.1 (2021/07/06)
------------------

**Changed**

- :class:`.Reddit` will now be shallow copied when a deepcopy is preformed on it as
  ``asyncprawcore.Session`` (more specifically, :py:class:`asyncio.AbstractEventLoop`)
  does not support being deepcopied.

**Fixed**

- Fixed an issue where some :class:`.RedditBase` objects would be sent in a request as
  ``"None"``.

7.3.0 (2021/06/18)
------------------

**Added**

- :class:`.UserSubreddit` for the ``subreddit`` attribute of :class:`.Redditor`.
- :meth:`.Reddit.username_available` checks if a username is available.
- :meth:`.trusted` to retrieve a :class:`.RedditorList` of trusted users.
- :meth:`.trust` to add a user to the trusted list.
- :meth:`.distrust` to remove a user from the trusted list.
- :class:`.SQLiteTokenManager` (may not work on Windows)

**Changed**

- :meth:`.Redditor.moderated` will now objectify all data returned from the API.
- The ``wiki_edit`` endpoint has been changed from ``r/{subreddit}/api/wiki/edit/`` to
  ``r/{subreddit}/api/wiki/edit``.
- :meth:`.Redditor.block` no longer needs to retrieve a user's fullname.

**Deprecated**

- The ``subreddit`` attribute of :class:`.Redditor` is no longer a dict.
- Legacy modmail is slated for deprecation by Reddit in June 2021. See
  https://www.reddit.com/r/modnews/comments/mar9ha/even_more_modmail_improvements/ for
  more info.

**Fixed**

- Fixed bug where :meth:`.WikiPage.edit` and :meth:`.SubredditWiki.create` would fail if
  passed ``content`` and ``reason`` parameters that produced a request with a body
  greater than 500 KiB, even when the parameters did not exceed their respective
  permitted maximum lengths.
- Fixed bug where :meth:`.Reddit.request` could not handle instances of ``BadRequest``\s
  when the JSON data contained only the keys "reason" and "message".
- Fixed bug where :meth:`.Reddit.request` could not handle instances of ``BadRequest``\s
  when the response did not contain valid JSON data.
- Fixed bug where :meth:`.FullnameMixin.fullname` sometimes returned the wrong fullname.

7.2.0 (2021/02/25)
------------------

**Added**

- :class:`.Reddit` keyword argument ``token_manager``.
- :class:`.FileTokenManager` and its parent abstract class :class:`.BaseTokenManager`.

**Deprecated**

- The configuration setting ``refresh_token`` is deprecated and its use will result in a
  :py:class:`DeprecationWarning`. This deprecation applies in all ways of setting
  configuration values, i.e., via ``praw.ini``, as a keyword argument when initializing
  an instance of :class:`.Reddit`, and via the ``PRAW_REFRESH_TOKEN`` environment
  variable. To be prepared for Async PRAW 8, use the new :class:`.Reddit` keyword
  argument ``token_manager``. See :ref:`refresh_token` in Async PRAW's documentation for
  an example.
- :meth:`.me` will no longer return ``None`` when called in :attr:`.read_only` mode
  starting in Async PRAW 8. A :py:class:`DeprecationWarning` will be issued. To switch
  forward to the Async PRAW 8 behavior set ``praw8_raise_exception_on_me=True`` in your
  ``asyncpraw.Reddit(...)`` call.

7.1.1 (2021/02/11)
------------------

**Added**

- Add method :meth:`~.Subreddits.premium` to reflect the naming change in Reddit's API.
- Ability to submit image galleries with :meth:`~.Subreddit.submit_gallery`.
- Ability to pass a gallery url to :meth:`.Reddit.submission`.
- Ability to specify modmail mute duration.
- Add method :meth:`.invited` to get invited moderators of a subreddit.
- Ability to submit text/self posts with inline media.
- Add method :meth:`~.Submission.award` and :meth:`~.Comment.award` with the ability to
  specify type of award, anonymity, and message when awarding a submission or comment.
- Ability to specify subreddits by name using the `subreddits` parameter in
  :meth:`.Reddit.info`.
- Added :meth:`.Reddit.close` to close the requestor session.
- Ability to use :class:`.Reddit` as an asynchronous context manager that automatically
  closes the requestor session on exit.

**Changed**

- :class:`~.BoundedSet` will now utilize a Last-Recently-Used (LRU) storing mechanism,
  which will change the order in which elements are removed from the set.
- Improved :meth:`~.Subreddit.submit_image` and :meth:`~.Subreddit.submit_video`
  performance in slow network environments by removing a race condition when
  establishing a websocket connection.

**Deprecated**

- :meth:`~.Subreddits.gold` is superseded by :meth:`~.Subreddits.premium`.
- :meth:`~.Submission.gild` is superseded by :meth:`~.Submission.award`.
- :meth:`~.Comment.gild` is superseded by :meth:`~.Comment.award`.
- ``PRAWException`` is superseded by :class:`.AsyncPRAWException`.

**Fixed**

- An issue where leaving as a moderator fails if you are using token auth.
- An issue where an incorrect error was being raised due to invalid submission urls.
- A bug where if you call `.parent()` on a comment it clears its replies.
- An issue where performing a deepcopy on an :class:`.RedditBase` object will fail.
- Some cases where streams yield the same item multiple times. This cannot be prevented
  in every case.
- An issue where streams could get stuck on a deleted item and never pull new items.
- Fix subreddit style asset uploading.

7.1.0 (2020/07/16)
------------------

- First official Async PRAW release!

7.1.0.pre1 (2020/07/16)
-----------------------

- Initial Async PRAW pre release.

For changes in PRAW please see: `PRAW Changelog
<https://praw.readthedocs.io/en/latest/pages/changelog.html>`_
