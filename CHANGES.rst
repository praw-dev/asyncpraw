Change Log
==========

Unreleased
----------

**Added**

* Ability to submit image galleries with :meth:`.submit_gallery`.
* Ability to specify modmail mute duration.

**Fixed**

* A bug where if you call `.parent()` on a comment it clears its replies.
* An issue where performing a deepcopy on an :class:`.RedditBase` object will fail.
* Added close method to close requestor session

7.1.0 (2020/07/16)
------------------

* First official Async PRAW release!


7.1.0.pre1 (2020/07/16)
-----------------------

* Initial Async PRAW pre release.


For changes in PRAW please see: `PRAW Changelog
<https://praw.readthedocs.io/en/latest/pages/changelog.html>`_
