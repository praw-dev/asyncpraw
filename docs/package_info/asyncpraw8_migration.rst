.. _asyncpraw8_migration:

###########################
 Migrating to Async PRAW 8
###########################

Async PRAW 8 completes the deprecation cycle started during the 7.x series. This guide
covers every removed or changed item, with examples showing how to update your code.

************************
 Python Version Support
************************

Async PRAW 8 requires Python 3.10 or newer. Support for Python 3.8 and 3.9, both of
which are end-of-life, has been dropped, and support for Python 3.13 and 3.14 has been
added.

*********************************
 Dependency and Behavior Changes
*********************************

Async PRAW 8 raises several dependency floors: it now requires ``asyncprawcore >=4, <5``
(for its public :class:`!Session` and authorizer accessors and the widened
:meth:`!Session.request` annotations) and ``update_checker[async] >=1.0, <2``. The 1.0
release of ``update_checker`` is dependency-free, dropping ``requests`` from Async
PRAW's transitive dependencies; the update check now uses the native async API on the
first request, instead of a blocking call during ``Reddit`` initialization. These
requirements are resolved automatically when you install or upgrade Async PRAW; no code
changes are required.

Async PRAW now ships a :PEP:`561` ``py.typed`` marker, so downstream projects can type
check against Async PRAW's inline annotations. This is additive and does not change
runtime behavior.

Async PRAW now warns at initialization if a ``praw.ini`` file in the current working
directory sets the ``oauth_url`` or ``reddit_url`` endpoint, since such a file can
redirect credentials to an untrusted host. If you intentionally override these endpoints
(for example, to test against a mock server), silence the warning by setting the
``PRAW_ALLOW_ENDPOINT_OVERRIDE`` environment variable.

Because a :class:`.Submission` is fetched on initialization, its ``comment_sort`` and
``comment_limit`` attributes -- and :meth:`.Submission.add_fetch_param` -- must be set
before it is fetched. Initialize the submission with ``fetch=False``, set them, then
call :meth:`~.Submission.load`. Setting any of them after the submission has been
fetched now raises :class:`.ClientException` instead of logging a warning. The
``warn_comment_sort`` and ``warn_additional_fetch_params`` configuration options, which
previously toggled these warnings, have been removed.

Old:

.. code-block:: python
    :class: code-old

    submission = await reddit.submission("id")
    submission.comment_sort = "new"
    await submission.load()

New:

.. code-block:: python

    submission = await reddit.submission("id", fetch=False)
    submission.comment_sort = "new"
    await submission.load()

***************
 Media Uploads
***************

All methods that upload media now accept :class:`.Media` instances instead of file
paths. The relevant subclass depends on what is being uploaded: :class:`.PostMedia` for
submissions and inline media, :class:`.EmojiMedia` for emoji, :class:`.StylesheetImage`
and :class:`.StylesheetAsset` for stylesheet images, and :class:`.WidgetMedia` for
widget images.

A :class:`.Media` instance can be constructed from a file path, or from ``bytes``
content along with a ``name``, so media no longer has to be written to disk before
uploading:

.. code-block:: python

    from asyncpraw.models import PostMedia

    media_from_path = PostMedia("/path/to/image.png")
    media_from_bytes = PostMedia(image_bytes, "image.png")

Inline media
============

The ``path`` argument to :class:`.InlineMedia` (:class:`.InlineGif`,
:class:`.InlineImage`, and :class:`.InlineVideo`) has been replaced by ``media``, which
takes a :class:`.PostMedia` instance.

Old:

.. code-block:: python
    :class: code-old

    from asyncpraw.models import InlineImage

    image = InlineImage(caption="optional caption", path="/path/to/image.jpg")

New:

.. code-block:: python

    from asyncpraw.models import InlineImage, PostMedia

    image = InlineImage(caption="optional caption", media=PostMedia("/path/to/image.jpg"))

Emoji
=====

The ``image_path`` argument to :meth:`.SubredditEmoji.add` has been replaced by
``media``, which takes an :class:`.EmojiMedia` instance.

Old:

.. code-block:: python
    :class: code-old

    subreddit = await reddit.subreddit("test")
    await subreddit.emoji.add(image_path="emoji.png", name="emoji")

New:

.. code-block:: python

    from asyncpraw.models import EmojiMedia

    subreddit = await reddit.subreddit("test")
    await subreddit.emoji.add(media=EmojiMedia("emoji.png"), name="emoji")

Stylesheet images
=================

The ``image_path`` arguments to the :class:`.SubredditStylesheet` ``upload_*`` methods
have been replaced by ``media``, which must be passed positionally.
:meth:`.SubredditStylesheet.upload`, :meth:`.upload_header`,
:meth:`.upload_mobile_header`, and :meth:`.upload_mobile_icon` take a
:class:`.StylesheetImage` instance, while :meth:`.upload_banner`,
:meth:`.upload_banner_additional_image`, :meth:`.upload_banner_hover_image`, and
:meth:`.upload_mobile_banner` take a :class:`.StylesheetAsset` instance.

Old:

.. code-block:: python
    :class: code-old

    subreddit = await reddit.subreddit("test")
    await subreddit.stylesheet.upload(image_path="img.png", name="smile")
    await subreddit.stylesheet.upload_banner("banner.png")

New:

.. code-block:: python

    from asyncpraw.models import StylesheetAsset, StylesheetImage

    subreddit = await reddit.subreddit("test")
    await subreddit.stylesheet.upload(StylesheetImage("img.png"), name="smile")
    await subreddit.stylesheet.upload_banner(StylesheetAsset("banner.png"))

Widget images
=============

The ``file_path`` argument to :meth:`.SubredditWidgetsModeration.upload_image` has been
replaced by ``media``, which takes a :class:`.WidgetMedia` instance and must be passed
positionally.

Old:

.. code-block:: python
    :class: code-old

    subreddit = await reddit.subreddit("test")
    image_url = await subreddit.widgets.mod.upload_image("/path/to/image.jpg")

New:

.. code-block:: python

    from asyncpraw.models import WidgetMedia

    subreddit = await reddit.subreddit("test")
    image_url = await subreddit.widgets.mod.upload_image(WidgetMedia("/path/to/image.jpg"))

Other media upload changes
==========================

- An unknown media type now raises :class:`.ClientException` when uploading media,
  instead of falling back to JPEG.
- Media uploads to Reddit's S3 buckets now respect the configured ``timeout`` and raise
  ``asyncprawcore.RequestException`` on transport errors, consistent with all other
  requests. Code that caught raw ``aiohttp`` exceptions around media uploads should
  catch ``asyncprawcore.RequestException`` instead.

***************************
 Unified ``submit`` method
***************************

``Subreddit.submit_gallery``, ``Subreddit.submit_image``, ``Subreddit.submit_poll``, and
``Subreddit.submit_video`` have been merged into :meth:`.Subreddit.submit`. The kind of
submission is selected with the ``gallery``, ``image``, ``poll``, ``url``, or ``video``
keyword argument. At least one of those, or ``selftext``, must be provided, and they are
mutually exclusive, while ``selftext`` may accompany any of them as optional
Markdown-formatted body text.

Submitting an image
===================

Old:

.. code-block:: python
    :class: code-old

    subreddit = await reddit.subreddit("test")
    await subreddit.submit_image("My Title", "/path/to/image.png")

New:

.. code-block:: python

    from asyncpraw.models import PostMedia

    subreddit = await reddit.subreddit("test")
    await subreddit.submit("My Title", image=PostMedia("/path/to/image.png"))

Submitting a video
==================

Video-specific options, such as a custom thumbnail or submitting the video as a
videogif, are provided by passing a ``dict`` instead of a bare :class:`.PostMedia`.

Old:

.. code-block:: python
    :class: code-old

    subreddit = await reddit.subreddit("test")
    await subreddit.submit_video(
        "My Title", "/path/to/video.mp4", thumbnail_path="/path/to/thumbnail.png"
    )

New:

.. code-block:: python

    from asyncpraw.models import PostMedia

    subreddit = await reddit.subreddit("test")
    await subreddit.submit(
        "My Title",
        video={
            "media": PostMedia("/path/to/video.mp4"),
            "thumbnail": PostMedia("/path/to/thumbnail.png"),
        },
    )

The ``videogif`` argument is now the ``"gif"`` key of the ``video`` dict:

Old:

.. code-block:: python
    :class: code-old

    subreddit = await reddit.subreddit("test")
    await subreddit.submit_video("My Title", "/path/to/video.mp4", videogif=True)

New:

.. code-block:: python

    from asyncpraw.models import PostMedia

    subreddit = await reddit.subreddit("test")
    await subreddit.submit(
        "My Title", video={"gif": True, "media": PostMedia("/path/to/video.mp4")}
    )

Submitting a gallery
====================

Gallery items are either a bare :class:`.PostMedia`, or a ``dict`` with a ``media`` key
(replacing ``image_path``) when a ``caption`` or ``outbound_url`` is desired.

Old:

.. code-block:: python
    :class: code-old

    images = [
        {"image_path": "/path/to/image.png"},
        {"image_path": "/path/to/image2.png", "caption": "a caption"},
    ]
    subreddit = await reddit.subreddit("test")
    await subreddit.submit_gallery("My Title", images)

New:

.. code-block:: python

    from asyncpraw.models import PostMedia

    gallery = [
        PostMedia("/path/to/image.png"),
        {"caption": "a caption", "media": PostMedia("/path/to/image2.png")},
    ]
    subreddit = await reddit.subreddit("test")
    await subreddit.submit("My Title", gallery=gallery)

Submitting a poll
=================

The ``options`` and ``duration`` arguments are now keys of the ``poll`` dict.
``selftext`` is no longer required for polls.

Old:

.. code-block:: python
    :class: code-old

    subreddit = await reddit.subreddit("test")
    await subreddit.submit_poll(
        "Do you like Async PRAW?", duration=3, options=["Yes", "No"], selftext=""
    )

New:

.. code-block:: python

    subreddit = await reddit.subreddit("test")
    await subreddit.submit(
        "Do you like Async PRAW?", poll={"duration": 3, "options": ["Yes", "No"]}
    )

*********************************
 ``user.me()`` in read-only mode
*********************************

Calling ``await reddit.user.me()`` in :attr:`.read_only` mode previously returned
``None`` with a deprecation warning. It now raises :class:`.ReadOnlyException`.

Old:

.. code-block:: python
    :class: code-old

    if await reddit.user.me() is None:
        print("Not authenticated")

New:

.. code-block:: python

    from asyncpraw.exceptions import ReadOnlyException

    try:
        await reddit.user.me()
    except ReadOnlyException:
        print("Not authenticated")

***********************************************
 ``Redditor.subreddit`` is a ``UserSubreddit``
***********************************************

The ``subreddit`` attribute of :class:`.Redditor` is a :class:`.UserSubreddit` instance.
Its values are accessed as attributes; the ``dict`` interface has been removed.

Old:

.. code-block:: python
    :class: code-old

    title = redditor.subreddit["title"]

New:

.. code-block:: python

    title = redditor.subreddit.title

*********************************
 Link submissions with body text
*********************************

The ``selftext`` and ``url`` arguments to :meth:`.Subreddit.submit` are no longer
mutually exclusive. When ``url`` is provided, ``selftext`` is used as optional
Markdown-formatted body text to accompany the link submission. The same applies to
``gallery``, ``image``, ``poll``, and ``video`` submissions.

One exception: combining ``inline_media`` with ``selftext`` for a ``url`` submission
raises an exception, because Reddit does not support inline media in body text for link
submissions.

******************************************
 Arguments that must be passed by keyword
******************************************

The following arguments must now be passed by keyword:

- The ``mark_read`` argument when calling ``subreddit.modmail`` to fetch a
  :class:`.ModmailConversation`, e.g., ``await subreddit.modmail("2gmz",
  mark_read=True)``.
- The ``is_link`` argument to :meth:`.SubredditFlairTemplates.flair_type`.
- The ``data`` argument to ``Objector.objectify``.
- The ``fetch`` argument to :meth:`.get_emoji`, :meth:`.get_reason`,
  :meth:`.get_update`, :meth:`.DraftHelper.__call__`, :meth:`.LiveHelper.__call__`,
  :meth:`.Modmail.__call__`, :meth:`.SubredditCollections.__call__`, and
  :meth:`.SubredditHelper.__call__`.

********************************************
 Arguments that must be passed positionally
********************************************

The following arguments are now positional-only:

- The ``name`` argument to :meth:`.get_emoji`.
- The ``id`` argument to :meth:`.get_reason` (previously ``reason_id``).
- The ``short_name`` argument to :meth:`.get_rule`.
- The ``id`` argument to :meth:`.get_update` (previously ``update_id``).
- The ``page_name`` argument to :meth:`.get_page`.

*************************************************
 ``lazy`` keyword argument replaced by ``fetch``
*************************************************

The ``lazy`` keyword argument has been replaced by ``fetch`` across the codebase to
consolidate the keyword used to explicitly control fetching when initializing an object.
``fetch=True`` performs the fetch immediately, while ``fetch=False`` leaves the object
lazy. See :ref:`Lazy Loading <lazy_loading>` for the per-class defaults.

Old:

.. code-block:: python
    :class: code-old

    submission = await reddit.submission("id", lazy=True)

New:

.. code-block:: python

    submission = await reddit.submission("id", fetch=False)

***********************************
 ``CommentForest`` iteration model
***********************************

:meth:`.CommentForest.list` no longer needs to be awaited -- it returns the list
directly. Code that previously awaited the call should drop the ``await``.

Old:

.. code-block:: python
    :class: code-old

    submission = await reddit.submission("id")
    comments = await submission.comments.list()

New:

.. code-block:: python

    submission = await reddit.submission("id")
    comments = submission.comments.list()

In addition, :class:`.CommentForest` can no longer be used as an asynchronous iterator.
Iterate over the result of :meth:`~.CommentForest.list` instead:

.. code-block:: python

    for comment in submission.comments.list():
        ...

************************************************
 ``Reddit`` synchronous context manager removed
************************************************

:class:`.Reddit` can no longer be used as a synchronous context manager. Use the
asynchronous context manager (``async with``) instead, which closes the underlying
``aiohttp`` session on exit.

Old:

.. code-block:: python
    :class: code-old

    with asyncpraw.Reddit(...) as reddit:
        ...

New:

.. code-block:: python

    async with asyncpraw.Reddit(...) as reddit:
        ...

*********
 Renamed
*********

- The ``reason_id`` argument to :class:`.RemovalReason` has been renamed to ``id``.
- ``APIException`` has been removed; use :class:`.RedditAPIException`.
- The ``PRAWException`` rename handler has been removed; use
  :class:`.AsyncPRAWException` directly (importing the old name will no longer resolve).
- ``Subreddits.gold`` has been removed; use :meth:`.Subreddits.premium`.

*************
 Old modmail
*************

Reddit retired the old modmail system, so ``Subreddit.mod.inbox``,
``Subreddit.mod.unread``, ``Subreddit.mod.stream.unread``, ``SubredditMessage.mute``,
and ``SubredditMessage.unmute`` have been removed. Use the new modmail interface
instead.

Old:

.. code-block:: python
    :class: code-old

    subreddit = await reddit.subreddit("test")
    async for message in subreddit.mod.unread():
        print(message.subject)

New:

.. code-block:: python

    subreddit = await reddit.subreddit("test")
    async for conversation in subreddit.modmail.conversations(state="new"):
        print(conversation.subject)

To stream conversations, use :meth:`.SubredditModerationStream.modmail_conversations`
(``subreddit.mod.stream.modmail_conversations()``). Muting and unmuting users is
available on :class:`.ModmailConversation` via :meth:`.ModmailConversation.mute` and
:meth:`.ModmailConversation.unmute`.

The ``after`` argument for :meth:`.conversations` has also been removed. To resume a
listing from a known conversation, pass ``after`` through ``params``:

.. code-block:: python

    subreddit = await reddit.subreddit("test")
    conversations = subreddit.modmail.conversations(params={"after": "2gmz"})

****************
 Token managers
****************

The ``token_manager`` keyword argument to :class:`.Reddit`, along with
``BaseTokenManager``, ``FileTokenManager``, and ``SQLiteTokenManager``, has been
removed. Refresh tokens no longer rotate, so a static ``refresh_token`` can be provided
directly.

Old:

.. code-block:: python
    :class: code-old

    from asyncpraw.util.token_manager import FileTokenManager

    reddit = asyncpraw.Reddit(..., token_manager=FileTokenManager("token.txt"))

New:

.. code-block:: python

    reddit = asyncpraw.Reddit(..., refresh_token="...")

See :ref:`refresh_token` for the complete guide to obtaining and using refresh tokens.

*********************************
 Subreddit Module Reorganization
*********************************

The single ``asyncpraw/models/reddit/subreddit.py`` file has been split into an
``asyncpraw.models.reddit.subreddit`` package. The :class:`.Subreddit` class and each of
its helper classes now live in their own module:

.. list-table::
    :header-rows: 1
    :widths: 50 50

    - - Class
      - New module
    - - :class:`.Subreddit`
      - ``asyncpraw.models.reddit.subreddit.subreddit``
    - - :class:`.Modmail`
      - ``asyncpraw.models.reddit.subreddit.modmail``
    - - :class:`.SubredditFilters`
      - ``asyncpraw.models.reddit.subreddit.filters``
    - - :class:`.SubredditFlair`, :class:`.SubredditFlairTemplates`,
        :class:`.SubredditLinkFlairTemplates`, :class:`.SubredditRedditorFlairTemplates`
      - ``asyncpraw.models.reddit.subreddit.flair``
    - - :class:`.SubredditModeration`, :class:`.SubredditModerationStream`
      - ``asyncpraw.models.reddit.subreddit.moderation``
    - - :class:`.SubredditQuarantine`
      - ``asyncpraw.models.reddit.subreddit.quarantine``
    - - :class:`.SubredditRelationship`, :class:`.ContributorRelationship`,
        :class:`.ModeratorRelationship`
      - ``asyncpraw.models.reddit.subreddit.relationship``
    - - :class:`.SubredditStream`
      - ``asyncpraw.models.reddit.subreddit.stream``
    - - :class:`.SubredditStylesheet`
      - ``asyncpraw.models.reddit.subreddit.stylesheet``
    - - :class:`.SubredditWiki`
      - ``asyncpraw.models.reddit.subreddit.wiki``

All of these classes remain importable from ``asyncpraw.models.reddit.subreddit`` and
``asyncpraw.models`` for backwards compatibility, so existing imports of the form ``from
asyncpraw.models.reddit.subreddit import Subreddit`` continue to work unchanged. Update
direct imports only if you were depending on the module file's location on disk (for
example, in tooling or monkeypatches).

*****************************
 Removed without replacement
*****************************

The following were removed because Reddit no longer supports the underlying endpoints or
features:

- ``Reddit.random_subreddit``, ``Subreddit.random``, and ``Subreddit.random_rising`` --
  Reddit removed the random subreddit and random submission endpoints.
- ``Comment.award``, ``Submission.award``, and the ``gild`` aliases on
  :class:`.Comment`, :class:`.Redditor`, and :class:`.Submission` -- Reddit removed the
  awards API.
- ``Redditor.gilded``, ``Subreddit.gilded``, and ``Redditor.gildings`` -- gilded
  listings were removed along with the awards API.
- ``Subreddits.search_by_topic`` -- the endpoint has returned 404 since 2020.
- ``Reddit.validate_on_submit`` -- Reddit now always validates posts on submission, so
  the setting no longer has any effect. Remove any assignments to it.
- ``WebSocketException.original_exception``.
- ``InboxableMixin.unblock_subreddit``.
- The ``reset_timestamp`` key in the dictionary returned by :meth:`.limits` -- the
  remaining keys are ``remaining`` and ``used``.
