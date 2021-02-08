Change Log
==========

Unreleased
----------

7.1.1 (2021/02/08)
------------------

**Added**

* Add method :meth:`~.Subreddits.premium` to reflect the naming change in Reddit's API.
* Ability to submit image galleries with :meth:`.submit_gallery`.
* Ability to pass a gallery url to :meth:`.Reddit.submission`.
* Ability to specify modmail mute duration.
* Add method :meth:`.invited` to get invited moderators of a subreddit.
* Ability to submit text/self posts with inline media.
* Add method :meth:`~.Submission.award` and :meth:`~.Comment.award` with the ability to
  specify type of award, anonymity, and message when awarding a submission or comment.
* Ability to specify subreddits by name using the `subreddits` parameter in
  :meth:`.Reddit.info`.
* Added :meth:`.Reddit.close` to close the requestor session.
* Ability to use :class:`.Reddit` as an asynchronous context manager that automatically
  closes the requestor session on exit.

**Changed**

* :class:`~.BoundedSet` will now utilize a Last-Recently-Used (LRU) storing mechanism,
  which will change the order in which elements are removed from the set.
* Improved :meth:`.submit_image` and :meth:`.submit_video` performance in slow
  network environments by removing a race condition when establishing a
  websocket connection.

**Deprecated**

* :meth:`~.Subreddits.gold` is superseded by :meth:`~.Subreddits.premium`.
* :meth:`~.Submission.gild` is superseded by :meth:`~.Submission.award`.
* :meth:`~.Comment.gild` is superseded by :meth:`~.Comment.award`.

**Fixed**

* An issue where leaving as a moderator fails if you are using token auth.
* An issue where an incorrect error was being raised due to invalid submission urls.
* A bug where if you call `.parent()` on a comment it clears its replies.
* An issue where performing a deepcopy on an :class:`.RedditBase` object will fail.
* Some cases where streams yield the same item multiple times. This cannot be
  prevented in every case.
* An issue where streams could get stuck on a deleted item and never pull new items.
* Fix subreddit style asset uploading.

7.1.0 (2020/07/16)
------------------

* First official Async PRAW release!


7.1.0.pre1 (2020/07/16)
-----------------------

* Initial Async PRAW pre release.


For changes in PRAW please see: `PRAW Changelog
<https://praw.readthedocs.io/en/latest/pages/changelog.html>`_
