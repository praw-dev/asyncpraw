############
 Change Log
############

asyncpraw follows `semantic versioning <https://semver.org/>`_.

********************
 8.0.2 (2026/06/24)
********************

**Changed**

- Reword property docstrings and clarify in the 8.0.0 change log that arguments
  deprecated for positional use in v7 are now keyword-only. Maintenance and
  documentation only; no functional changes.

********************
 8.0.1 (2026/06/15)
********************

**Fixed**

- Declare ``__all__`` in ``asyncpraw`` and ``asyncpraw.models`` so that, now that Async
  PRAW ships a ``py.typed`` marker, type checkers recognize documented imports such as
  ``from asyncpraw import Reddit`` and ``from asyncpraw.models import Redditor`` as
  public re-exports instead of reporting them as private.

********************
 8.0.0 (2026/06/14)
********************

**Added**

- :class:`.Announcement` and :class:`.AnnouncementHelper`, exposed as
  :attr:`.Reddit.announcements`, for listing, hiding, and marking the currently
  authenticated user's announcements as read. Provides :meth:`.Announcement.hide`,
  :meth:`.Announcement.mark_read`, :meth:`.AnnouncementHelper.hide`,
  :meth:`.AnnouncementHelper.mark_read`, and :meth:`.AnnouncementHelper.mark_all_read`.
  :attr:`.Announcement.sent_datetime` and :attr:`.Announcement.read_datetime` return the
  announcement's ``sent_at`` and ``read_at`` timestamps as timezone-aware
  :class:`datetime.datetime` objects (``read_datetime`` is ``None`` for unread
  announcements).
- :attr:`~.Comment.created_datetime` to objects with a creation time (for example
  :class:`.Comment`, :class:`.Submission`, :class:`.Redditor`, :class:`.Subreddit`,
  :class:`.Collection`, and :class:`.ModNote`), returning a timezone-aware
  :class:`datetime.datetime`.
- :attr:`~.Collection.updated_datetime` to :class:`.Collection`,
  :attr:`~.PollData.voting_end_datetime` to :class:`.PollData`, and
  :attr:`~.Comment.edited_datetime` to :class:`.Comment` and :class:`.Submission`
  (``None`` when the object has not been edited), all returning timezone-aware
  :class:`datetime.datetime` objects.
- An ``exception_handler`` keyword argument to :func:`.stream_generator` (and thus all
  ``stream`` methods) that is invoked with any exception raised while fetching items,
  allowing the stream to resume rather than terminate. Re-raise from the handler to stop
  the stream.
- Warn when a ``praw.ini`` in the current working directory sets the ``oauth_url`` or
  ``reddit_url`` endpoint, as such a file can redirect credentials to an untrusted host.
  The warning can be silenced by setting the ``PRAW_ALLOW_ENDPOINT_OVERRIDE``
  environment variable.
- :meth:`.Redditor.overview` to iterate over a Redditor's combined comments and
  submissions, mirroring the user overview page on Reddit. It returns the same listing
  as calling a sort method directly on a :class:`.Redditor`, so
  ``redditor.overview.new()`` and ``redditor.new()`` yield the same items; use
  ``redditor.comments`` or ``redditor.submissions`` to restrict the listing to a single
  type.
- Add support for Python 3.13.
- Add support for Python 3.14.
- Add support for optional Markdown-formatted ``selftext`` when submitting link, image,
  gallery and video posts.
- Add :class:`.Media` and its subclasses :class:`.EmojiMedia`, :class:`.PostMedia`,
  :class:`.StylesheetAsset`, :class:`.StylesheetImage`, and :class:`.WidgetMedia` to
  consolidate media uploads. Media can be constructed from a file path, or from
  ``bytes`` content along with a ``name``, so media no longer has to be written to disk
  before uploading.
- Support delayed session creation in asyncprawcore 2.5.0+.
- Add parameter ``fetch`` to :meth:`.get_rule` to control whether to fetch the rule data
  when initializing the rule object.
- A ``py.typed`` marker (:PEP:`561`) so that downstream projects can type check against
  Async PRAW's inline annotations.

**Changed**

- Arguments deprecated for positional use in Async PRAW 7 are now keyword-only across
  most methods, fulfilling the deprecation announced in 7.6.0. Notably, the
  ``time_filter`` argument to listing methods such as :meth:`.Subreddit.top` and
  :meth:`.Subreddit.controversial` — shown positionally in older documentation (for
  example ``subreddit.top("all")``) — must now be passed by keyword
  (``subreddit.top(time_filter="all")``).
- Drop support for Python 3.9, which was end-of-life on 2025-10-31.
- Require ``asyncprawcore >=3.1.0, <4`` for its public :class:`!Session` and authorizer
  accessors and the widened :meth:`!Session.request` annotations, which let Async PRAW
  drop a number of internal ``cast``\ s and type-checker suppressions.
- Require ``update_checker[async] >=1.0, <2.0`` and perform the update check using its
  native async API on the first request, instead of a blocking call during ``Reddit``
  initialization. The 1.0 release is dependency-free, dropping ``requests`` from Async
  PRAW's transitive dependencies.
- Drop support for Python 3.8, which was end-of-life on 2024-10-07.
- Change ``Reddit.user.me`` to raise :class:`.ReadOnlyException` when called in
  :attr:`.read_only` mode.
- The ``subreddit`` attribute of :class:`.Redditor` is a :class:`.UserSubreddit`
  instance.
- The ``data`` argument to ``Objector.objectify`` must now be passed by keyword.
- The ``mark_read`` argument to ``subreddit.modmail`` (:class:`.ModmailConversation`)
  must now be passed by keyword.
- The ``flair_type`` argument to :class:`.SubredditFlairTemplates` must be passed by
  keyword.
- The ``selftext`` and ``url`` arguments to :meth:`.Subreddit.submit` are no longer
  mutually exclusive. When ``url`` is provided ``selftext`` will be used as optional
  body text to accompany the link submission. An exception is raised when trying to use
  ``inline_media`` with ``selftext`` for a ``url`` submission because Reddit does not
  support inline media in body text for link submissions.
- ``Subreddit.submit_gallery``, ``Subreddit.submit_image``, ``Subreddit.submit_poll``,
  and ``Subreddit.submit_video`` have been merged into :meth:`.Subreddit.submit`. The
  kind of submission is selected with the ``gallery``, ``image``, ``poll``, ``url``, or
  ``video`` keyword argument. At least one of those, or ``selftext``, must be provided,
  and they are mutually exclusive, while ``selftext`` may accompany any of them as
  optional Markdown-formatted body text. ``image`` takes a :class:`.PostMedia` instance;
  ``gallery`` takes a list of :class:`.PostMedia` instances or ``dict``\ s with a
  ``media`` key; ``video`` takes a :class:`.PostMedia` instance or a ``dict`` with a
  ``media`` key and optional ``gif`` and ``thumbnail`` keys; and ``poll`` takes a
  ``dict`` with ``duration`` and ``options`` keys.
- Media upload methods now accept :class:`.Media` instances instead of file paths:

  - The ``image_path`` argument to :meth:`.SubredditEmoji.add` has been replaced by
    ``media``, which takes an :class:`.EmojiMedia` instance.
  - The ``image_path`` arguments to the :class:`.SubredditStylesheet` ``upload_*``
    methods have been replaced by ``media``, which must be passed positionally.
    :meth:`.SubredditStylesheet.upload`, :meth:`.SubredditStylesheet.upload_header`,
    :meth:`.SubredditStylesheet.upload_mobile_header`, and
    :meth:`.SubredditStylesheet.upload_mobile_icon` take a :class:`.StylesheetImage`
    instance, while :meth:`.SubredditStylesheet.upload_banner`,
    :meth:`.SubredditStylesheet.upload_banner_additional_image`,
    :meth:`.SubredditStylesheet.upload_banner_hover_image`, and
    :meth:`.SubredditStylesheet.upload_mobile_banner` take a :class:`.StylesheetAsset`
    instance.
  - The ``file_path`` argument to :meth:`.SubredditWidgetsModeration.upload_image` has
    been replaced by ``media``, which takes a :class:`.WidgetMedia` instance and must be
    passed positionally.
  - The ``path`` argument to :class:`.InlineMedia` (:class:`.InlineGif`,
    :class:`.InlineImage`, and :class:`.InlineVideo`) has been replaced by ``media``,
    which takes a :class:`.PostMedia` instance.

- An unknown media type now raises :class:`.ClientException` when uploading media,
  instead of falling back to JPEG.
- Media uploads to Reddit's S3 buckets now respect the configured ``timeout`` and raise
  ``asyncprawcore.RequestException`` on transport errors, consistent with all other
  requests, instead of bypassing the configured timeout and raising raw ``aiohttp``
  exceptions.
- :meth:`.CommentForest.list` no longer needs to be awaited.
- The keyword argument ``lazy`` has been replace by ``fetch`` to consolidate the keyword
  argument used to explicitly perform a fetch when initializing an object.
- The argument ``reason_id`` in :meth:`.RemovalReason.__init__` has been replaced with
  ``id`` and is now a positional-only argument.
- The ``name`` argument in :meth:`.get_emoji` is now a positional-only argument.
- The ``reason_id`` argument in :meth:`.get_reason` has been replaced with ``id`` and is
  now a positional-only argument.
- The ``short_name`` argument in :meth:`.get_rule` is now a positional-only argument.
- The ``update_id`` argument in :meth:`.get_update` has been replaced with ``id`` and is
  now a positional-only argument.
- The ``page_name`` argument in :meth:`.get_page` is now a positional-only argument.
- The ``fetch`` argument in the following methods is now a keyword-only argument:

  - :meth:`.get_emoji`
  - :meth:`.get_reason`
  - :meth:`.get_update`
  - :meth:`.DraftHelper.__call__`
  - :meth:`.LiveHelper.__call__`
  - :meth:`.Modmail.__call__`
  - :meth:`.SubredditCollections.__call__`
  - :meth:`.SubredditHelper.__call__`

- :meth:`.Submission.add_fetch_param` now raises :class:`.ClientException` when called
  on a submission that has already been fetched, rather than logging a warning, since
  the added parameters would have no effect.
- The ``comment_sort`` and ``comment_limit`` attributes of a :class:`.Submission` must
  now be set before the submission is fetched; setting either after the submission has
  been fetched raises :class:`.ClientException` instead of logging a warning. Because
  ``reddit.submission()`` fetches by default, initialize the submission with
  ``fetch=False``, set the attributes, then call :meth:`~.Submission.load`.
- Require ``asyncprawcore >=4, <5``.
- Split ``asyncpraw/models/reddit/subreddit.py`` into an
  ``asyncpraw.models.reddit.subreddit`` package, with :class:`.Subreddit` and each of
  its helper classes (:class:`.Modmail`, :class:`.SubredditFilters`,
  :class:`.SubredditFlair`, :class:`.SubredditModeration`,
  :class:`.SubredditQuarantine`, :class:`.SubredditRelationship`,
  :class:`.SubredditStream`, :class:`.SubredditStylesheet`, :class:`.SubredditWiki`, and
  their related classes) moved to dedicated modules. All classes remain importable from
  ``asyncpraw.models.reddit.subreddit`` and ``asyncpraw.models`` for backwards
  compatibility. See the :ref:`migration guide <asyncpraw8_migration>` for the full
  mapping.

**Fixed**

- An issue where submitting a gallery post with websockets enabled would fail.
- Fix API endpoint for :meth:`.Submission.hide` and :meth:`.Submission.unhide`, which
  returned a 404 due to a trailing slash.
- Fix ``TypeError`` when objectifying a response whose ``json.errors`` field is ``null``
  rather than an empty list (e.g. ``api/hide``).

**Removed**

- The ``warn_additional_fetch_params`` configuration option, which is obsolete now that
  adding fetch parameters to an already-fetched submission raises
  :class:`.ClientException`.
- The ``warn_comment_sort`` configuration option, which is obsolete now that setting
  ``comment_sort`` or ``comment_limit`` after the comments have been fetched raises
  :class:`.ClientException`.
- Remove ``Reddit.random_subreddit``, ``Subreddit.random``, and
  ``Subreddit.random_rising``.
- Remove ``APIException`` class.
- Remove ``PRAWException`` class rename handler.
- Remove ``Comment.award`` and ``Submission.award`` methods.
- Remove ``Comment.gild``, ``Redditor.gild``, and ``Submission.gild`` methods.
- Remove ``Redditor.gilded`` and ``Subreddit.gilded`` methods.
- Remove ``Redditor.gildings`` method.
- Remove ``Subreddit.mod.inbox``, ``Subreddit.mod.unread``, and
  ``Subreddit.mod.stream.unread`` methods.
- Remove ``Subreddits.search_by_topic`` method.
- Remove ``Subreddits.gold`` method.
- Remove :class:`.Reddit` keyword argument ``token_manager`` and all associated token
  managers.
- Remove ``Reddit.validate_on_submit`` configuration attribute.
- Remove ``WebSocketException.original_exception`` method.
- Remove the ``after`` argument for :meth:`.conversations`.
- Remove ability to use :class:`.CommentForest` as an asynchronous iterator.
- Remove ability to use :class:`.Reddit` as an synchronous context manager.
- Remove key ``reset_timestamp`` from :meth:`.limits`.
- Remove ``SubredditMessage.mute`` and ``SubredditMessage.unmute`` methods.
- Remove ``InboxableMixin.unblock_subreddit`` method.

********************
 7.8.1 (2024/12/21)
********************

**Changed**

- Bump asyncprawcore minimum version.

********************
 7.8.0 (2024/10/20)
********************

**Added**

- :meth:`~.SubredditLinkFlairTemplates.reorder` to reorder a subreddit's link flair
  templates.
- :meth:`~.SubredditRedditorFlairTemplates.reorder` to reorder a subreddit's redditor
  flair templates.
- Experimental :meth:`~.Submission._edit_experimental` for adding new inline media or
  editing a submission that has inline media.

  .. danger::

      This method is experimental. It is reliant on undocumented API endpoints and may
      result in existing inline media not displaying correctly and/or creating a
      malformed body. Use at your own risk. This method may be removed in the future
      without warning.

  This method is identical to :meth:`.Submission.edit` except for the following:

  - The ability to add inline media to existing posts.
  - Additional ``preserve_inline_media`` keyword argument to allow Async PRAW to attempt
    to preserve the existing inline media when editing a post. This is an experimental
    fix for an issue that occurs when editing a post with inline media would cause the
    media to lose their inline appearance.

- :func:`.stream_generator` now accepts the ``continue_after_id`` parameter, which
  starts the stream after a given item ID.
- Support for new share URL format created from Reddit's mobile apps.
- :class:`.Reddit` has a new configurable parameter, ``window_size``. This tells PRAW
  how long reddit's rate limit window is. This defaults to 600 seconds and shouldn't
  need to be changed unless reddit changes the size of their rate limit window.

**Fixed**

- An issue where submitting a post with media would fail due to an API change.

**Changed**

- Drop support for Python 3.7, which is end-of-life on 2023-06-27.

**Fixed**

- XML parsing error when media uploads fail.

********************
 7.7.1 (2023/07/11)
********************

**Changed**

- Drop ``asyncio_extras`` dependency, use ``contextlib.asynccontextmanager`` instead.

**Fixed**

- An issue with replying to a modmail conversation results in a error.

********************
 7.7.0 (2023/02/25)
********************

**Added**

- :meth:`.delete_mobile_banner` to delete mobile banners.
- :meth:`.upload_mobile_banner` to upload mobile banners.

**Fixed**

- An issue with iterating :class:`.ModNote` when a user has more than a hundred notes.
- An issue when uploading media during the submission of a new media post.
- Removal reasons are now returned in the same order as they appear on Reddit.

********************
 7.6.1 (2022/11/28)
********************

**Changed**

- Revert :meth:`~.Comment.edit` positional argument deprecation.
- Revert :meth:`~.Submission.edit` positional argument deprecation.

**Fixed**

- An issue where :class:`.ModmailConversation`'s ``messages`` attribute would only
  contain the latest message.

********************
 7.6.0 (2022/10/23)
********************

**Added**

- :meth:`.pin` to manage pinned submissions on the authenticated user's profile.
- :meth:`.update_display_layout` to update the display layout of posts in a
  :class:`.Collection`.
- :meth:`.SubredditCollectionsModeration.create` keyword argument ``display_layout`` for
  specifying a display layout when creating a :class:`.Collection`.
- :attr:`~.Message.parent` to get the parent of a :class:`.Message`.
- :class:`.ModNote` to represent a moderator note.
- :meth:`.ModNote.delete` to delete a single moderator note.
- :class:`.RedditModNotes` to interact with moderator notes from a :class:`.Reddit`
  instance. This provides the ability to create and fetch notes for one or more
  redditors from one or more subreddits.
- :class:`.RedditorModNotes` to interact with moderator notes from a :class:`.Redditor`
  instance.
- :meth:`.RedditorModNotes.subreddits` to obtain moderator notes from multiple
  subreddits for a single redditor.
- :class:`.SubredditModNotes` to interact with moderator notes from a
  :class:`.Subreddit` instance.
- :meth:`.SubredditModNotes.redditors` to obtain moderator notes for multiple redditors
  from a single subreddit.
- :meth:`~.BaseModNotes.create` to create a moderator note.
- :attr:`.Redditor.notes` to interact with :class:`.RedditorModNotes`.
- :attr:`.SubredditModeration.notes` to interact with :class:`.SubredditModNotes`.
- :meth:`~.ModNoteMixin.create_note` create a moderator note from a :class:`.Comment` or
  :class:`.Submission`.
- :meth:`~.ModNoteMixin.author_notes` to view the moderator notes for the author of a
  :class:`.Comment` or :class:`.Submission`.

**Changed**

- Drop support for Python 3.6, which is end-of-life on 2021-12-23.
- :meth:`.conversations` now returns a :class:`.ListingGenerator` allowing you to page
  through more than 100 conversations.

**Deprecated**

- The ``after`` argument for :meth:`.conversations` will now have to be included in
  ``params`` keyword argument.
- Positional keyword arguments for applicable functions and methods. Starting with Async
  PRAW 8, most functions and methods will no longer support positional arguments. It
  will encourage more explicit argument passing, enable arguments to be sorted
  alphabetically, and prevent breaking changes when adding new arguments to existing
  methods.

********************
 7.5.0 (2021/11/13)
********************

**Added**

- Log a warning if a submission's ``comment_sort`` attribute is updated after the
  submission has already been fetched and a ``warn_comment_sort`` config setting to turn
  off the warning.
- :meth:`.user_selectable` to get available subreddit link flairs.
- Automatic RateLimit handling will support errors with millisecond resolution.
- :class:`.Draft` to represent a submission draft.
- :meth:`.Draft.delete` to delete drafts.
- :meth:`.Draft.submit` to submit drafts.
- :meth:`.Draft.update` to modify drafts.
- :class:`.DraftHelper` to fetch or create drafts on new Reddit.
- :class:`.DraftList` to represent a list of :class:`.Draft` objects.

**Deprecated**

- Ability to use :class:`.CommentForest` as an asynchronous iterator.
- :meth:`.CommentForest.list` no longer needs to be awaited.
- :attr:`.Submission.comments` no longer needs to be awaited and is now a property.
- The keyword argument ``lazy`` has been replace by ``fetch`` to consolidate the keyword
  argument used to explicitly perform a fetch when initializing an object.

**Fixed**

- Fixed return value type of methods returning a listing in :class:`.Subreddit` and its
  helper classes.
- An import error when using Async PRAW in environments where ``libsqlite3-dev`` is
  needed to utilize ``aiosqlite`` package which depends on the ``sqlite3`` builtin.

********************
 7.4.0 (2021/07/30)
********************

**Added**

- :meth:`~.WikiPage.discussions` to obtain site-wide link submissions that link to the
  WikiPage.
- :meth:`.revert` to revert a WikiPage to a specified revision.
- :meth:`.Inbox.mark_all_read` to mark all messages as read with one API call.
- ``InboxableMixin.unblock_subreddit`` to unblock a subreddit.
- :meth:`.update_crowd_control_level` to update the crowd control level of a post.
- :meth:`.moderator_subreddits`, which returns information about the subreddits that the
  authenticated user moderates, has been restored.
- The configuration setting ``refresh_token`` has been added back. See
  https://www.reddit.com/r/redditdev/comments/olk5e6/followup_oauth2_api_changes_regarding_refresh/
  for more info.

**Changed**

- :meth:`.Reddit.delete` now accepts the ``params`` parameter.

**Deprecated**

- :class:`.Reddit` keyword argument ``token_manager``.

********************
 7.3.1 (2021/07/06)
********************

**Changed**

- :class:`.Reddit` will now be shallow copied when a deepcopy is preformed on it as
  ``asyncprawcore.Session`` (more specifically, :py:class:`asyncio.AbstractEventLoop`)
  does not support being deepcopied.

**Fixed**

- Fixed an issue where some :class:`.RedditBase` objects would be sent in a request as
  ``"None"``.

********************
 7.3.0 (2021/06/18)
********************

**Added**

- :class:`.UserSubreddit` for the ``subreddit`` attribute of :class:`.Redditor`.
- :meth:`.username_available` checks if a username is available.
- :meth:`.trusted` to retrieve a :class:`.RedditorList` of trusted users.
- :meth:`.trust` to add a user to the trusted list.
- :meth:`.distrust` to remove a user from the trusted list.
- ``SQLiteTokenManager`` (may not work on Windows).

**Changed**

- :meth:`.moderated` will now objectify all data returned from the API.
- The ``wiki_edit`` endpoint has been changed from ``r/{subreddit}/api/wiki/edit/`` to
  ``r/{subreddit}/api/wiki/edit``.
- :meth:`.Redditor.block` no longer needs to retrieve a user's fullname.

**Deprecated**

- The ``subreddit`` attribute of :class:`.Redditor` will no longer function as a
  ``dict``.
- Legacy modmail is slated for deprecation by Reddit in June 2021. See
  https://www.reddit.com/r/modnews/comments/mar9ha/even_more_modmail_improvements/ for
  more info.

**Fixed**

- Fixed bug where :meth:`.WikiPage.edit` and :meth:`.SubredditWiki.create` would fail if
  passed ``content`` and ``reason`` parameters that produced a request with a body
  greater than 500 KiB, even when the parameters did not exceed their respective
  permitted maximum lengths.
- Fixed bug where :meth:`.request` could not handle instances of ``BadRequest``\ s when
  the JSON data contained only the keys "reason" and "message".
- Fixed bug where :meth:`.request` could not handle instances of ``BadRequest``\ s when
  the response did not contain valid JSON data.
- Fixed bug where :meth:`~.FullnameMixin.fullname` sometimes returned the wrong
  fullname.

********************
 7.2.0 (2021/02/25)
********************

**Added**

- :class:`.Reddit` keyword argument ``token_manager``.
- ``FileTokenManager`` and its parent abstract class ``BaseTokenManager``.

**Deprecated**

- The configuration setting ``refresh_token`` is deprecated and its use will result in a
  :py:class:`DeprecationWarning`. This deprecation applies in all ways of setting
  configuration values, i.e., via ``praw.ini``, as a keyword argument when initializing
  an instance of :class:`.Reddit`, and via the ``PRAW_REFRESH_TOKEN`` environment
  variable. To be prepared for Async PRAW 8, use the new :class:`.Reddit` keyword
  argument ``token_manager``. See :ref:`refresh_token` in Async PRAW's documentation for
  an example.
- ``Reddit.user.me`` will no longer return ``None`` when called in :attr:`.read_only`
  mode starting in Async PRAW 8. A :py:class:`DeprecationWarning` will be issued. To
  switch forward to the Async PRAW 8 behavior set ``praw8_raise_exception_on_me=True``
  in your ``asyncpraw.Reddit(...)`` call.

********************
 7.1.1 (2021/02/11)
********************

**Added**

- Add method :meth:`.Subreddits.premium` to reflect the naming change in Reddit's API.
- Ability to submit image galleries with ``Subreddit.submit_gallery``.
- Ability to pass a gallery url to :meth:`.Reddit.submission`.
- Ability to specify modmail mute duration.
- Add method :meth:`.invited` to get invited moderators of a subreddit.
- Ability to submit text/self posts with inline media.
- Add method ``Submission.award`` and ``Comment.award`` with the ability to specify type
  of award, anonymity, and message when awarding a submission or comment.
- Ability to specify subreddits by name using the `subreddits` parameter in
  :meth:`.Reddit.info`.
- Added :meth:`.Reddit.close` to close the requestor session.
- Ability to use :class:`.Reddit` as an asynchronous context manager that automatically
  closes the requestor session on exit.

**Changed**

- :class:`.BoundedSet` will now utilize a Last-Recently-Used (LRU) storing mechanism,
  which will change the order in which elements are removed from the set.
- Improved ``Subreddit.submit_image`` and ``Subreddit.submit_video`` performance in slow
  network environments by removing a race condition when establishing a websocket
  connection.

**Deprecated**

- ``Subreddits.gold`` is superseded by :meth:`.Subreddits.premium`.
- ``Submission.gild`` is superseded by ``Submission.award``.
- ``Comment.gild`` is superseded by ``Comment.award``.
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

********************
 7.1.0 (2020/07/16)
********************

- First official Async PRAW release!

*************************
 7.1.0.pre1 (2020/07/16)
*************************

- Initial Async PRAW pre-release.

For changes in PRAW please see: `PRAW Changelog
<https://praw.readthedocs.io/en/latest/pages/changelog.html>`_
