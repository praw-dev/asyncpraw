Change Log
==========

Unreleased
----------

**Added**

* Add method :meth:`~.Subreddits.premium` to reflect the naming change in Reddit's API.
* Ability to submit image galleries with :meth:`.submit_gallery`.
* Ability to pass a gallery url to :meth:`.Reddit.submission`.
* Ability to specify modmail mute duration.
* Add method :meth:`.invited` to get invited moderators of a subreddit.
* Added :meth:`.Reddit.close` to close the requestor session.
* Ability to use :class:`.Reddit` as an asynchronous context manager that automatically
  closes the requestor session on exit.

**Changed**

* :class:`~.BoundedSet` will now utilize a Last-Recently-Used (LRU) storing mechanism,
  which will change the order in which elements are removed from the set.

**Deprecated**

* :meth:`~.Subreddits.gold` is superseded by :meth:`~.Subreddits.premium`.

**Fixed**

* A bug where if you call `.parent()` on a comment it clears its replies.
* An issue where performing a deepcopy on an :class:`.RedditBase` object will fail.
* Some cases where streams yield the same item multiple times. This cannot be
  prevented in every case.

7.1.0 (2020/07/16)
------------------

* First official Async PRAW release!


7.1.0.pre1 (2020/07/16)
-----------------------

* Initial Async PRAW pre release.


For changes in PRAW please see: `PRAW Changelog
<https://praw.readthedocs.io/en/latest/pages/changelog.html>`_
