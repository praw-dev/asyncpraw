Async PRAW: The Asynchronous Python Reddit API Wrapper
======================================================

.. image:: https://img.shields.io/pypi/v/asyncpraw.svg
   :alt: Latest asyncpraw Version
   :target: https://pypi.python.org/pypi/asyncpraw
.. image:: https://img.shields.io/pypi/pyversions/asyncpraw
   :alt: Supported Python Versions
   :target: https://pypi.python.org/pypi/asyncpraw
.. image:: https://img.shields.io/pypi/dm/asyncpraw
   :alt: PyPI - Downloads - Monthly
   :target: https://pypi.python.org/pypi/asyncpraw
.. image:: https://coveralls.io/repos/github/praw-dev/asyncpraw/badge.svg?branch=master
   :alt: Coveralls Coverage
   :target: https://coveralls.io/github/praw-dev/asyncpraw?branch=master
.. image:: https://github.com/praw-dev/asyncpraw/workflows/CI/badge.svg
   :alt: Github Actions Coverage
   :target: https://github.com/praw-dev/asyncpraw/actions?query=branch%3Amaster
.. image:: https://img.shields.io/badge/Contributor%20Covenant-v2.0%20adopted-ff69b4.svg
   :alt: Contributor Covenant
   :target: https://github.com/praw-dev/asyncpraw/blob/master/CODE_OF_CONDUCT.md

Async PRAW, an acronym for "Asynchronous Python Reddit API Wrapper", is a Python package that
allows for simple access to Reddit's API. Async PRAW aims to be easy to use and
internally follows all of `Reddit's API rules
<https://github.com/reddit/reddit/wiki/API>`_. With Async PRAW there's no need to
introduce ``sleep`` calls in your code. Give your client an appropriate user
agent and you're set.

.. _installation:

Installation
------------

Async PRAW is supported on Python 3.6+. The recommended way to
install Async PRAW is via `pip <https://pypi.python.org/pypi/pip>`_.

.. code-block:: bash

    pip install asyncpraw

To install the latest development version of Async PRAW run the following instead:

.. code-block:: bash

    pip install --upgrade https://github.com/praw-dev/asyncpraw/archive/master.zip

For instructions on installing Python and pip see "The Hitchhiker's Guide to
Python" `Installation Guides
<https://docs.python-guide.org/en/latest/starting/installation/>`_.

Quickstart
----------

Assuming you already have a credentials for a script-type OAuth application you
can instantiate an instance of Async PRAW like so:

.. code-block:: python

    import asyncpraw
    reddit = asyncpraw.Reddit(client_id="CLIENT_ID", client_secret="CLIENT_SECRET",
                         password="PASSWORD", user_agent="USERAGENT",
                         username="USERNAME")

With the ``reddit`` instance you can then interact with Reddit:

.. code-block:: python

    # Create a submission to r/test
    subreddit = await reddit.subreddit("test")
    await subreddit.submit("Test Submission", url="https://reddit.com")

    # Comment on a known submission
    submission = await reddit.submission(url="https://www.reddit.com/comments/5e1az9")
    await submission.reply("Super rad!")

    # Reply to the first comment of a weekly top thread of a moderated community
    subreddit = await reddit.subreddit("mod")
    async for submission in subreddit.top("week"):
        comments = await submission.comments()
        await comments[0].reply("An automated reply")

    # Output score for the first 256 items on the frontpage
    async for submission in reddit.front.hot(limit=256):
        print(submission.score)

    # Obtain the moderator listing for r/redditdev
    subreddit = await reddit.subreddit("redditdev")
    async for moderator in subreddit.moderator:
        print(moderator)

Please see Async PRAW's `documentation <https://asyncpraw.readthedocs.io/>`_ for
more examples of what you can do with Async PRAW.

Async PRAW Discussion and Support
---------------------------------

For those new to Python, or would otherwise consider themselves a Python
beginner, please consider asking questions on the `r/learnpython
<https://www.reddit.com/r/learnpython>`_ subreddit. There are wonderful people
there who can help with general Python and simple PRAW related questions.

Otherwise, there are a few official places to ask questions about PRAW:

`r/redditdev <https://www.reddit.com/r/redditdev>`_ is the best place on
Reddit to ask PRAW related questions. This subreddit is for all Reddit API
related discussion so please tag submissions with *[PRAW]*. Please perform a
search on the subreddit first to see if anyone has similar questions.

Real-time chat can be conducted via the `PRAW Slack Organization
<https://join.slack.com/t/praw/shared_invite/enQtOTUwMDcxOTQ0NzY5LWVkMGQ3ZDk5YmQ5MDEwYTZmMmJkMTJkNjBkNTY3OTU0Y2E2NGRlY2ZhZTAzMWZmMWRiMTMwYjdjODkxOGYyZjY>`_
(please create an issue if that invite link has expired).

Please do not directly message any of the contributors via Reddit, email, or
Slack unless they have indicated otherwise. We strongly encourage everyone to
help others with their questions.

Please file bugs and feature requests as issues on `GitHub
<https://github.com/praw-dev/asyncpraw/issues>`_ after first searching to ensure a
similar issue was not already filed. If such an issue already exists please
give it a thumbs up reaction. Comments to issues containing additional
information are certainly welcome.

.. note:: This project is released with a `Contributor Code of Conduct
   <https://github.com/praw-dev/asyncpraw/blob/master/CODE_OF_CONDUCT.md>`_. By
   participating in this project you agree to abide by its terms.

Documentation
-------------

Async PRAW's documentation is located at https://asyncpraw.readthedocs.io/.

History
-------

`August 2010
<https://github.com/praw-dev/praw/commit/efef08a4a713fcfd7dfddf992097cf89426586ae>`_:
Timothy Mellor created a github project called ``reddit_api``.

`March 2011
<https://github.com/praw-dev/praw/commit/ebfc9caba5b58b9e68c77af9c8e53f5562a2ee64>`_:
The Python package ``reddit`` was registered and uploaded to pypi.

`December 2011
<https://github.com/praw-dev/praw/commit/74bb962b3eefe04ce6acad88e6f53f43d10c8803>`_:
Bryce Boe took over as maintainer of the ``reddit`` package.

`June 2012
<https://github.com/praw-dev/praw/commit/adaf89fe8631f41ab9913b379de104c9ef6a1e73>`_:
Bryce renamed the project ``PRAW`` and the repository was relocated to the
newly created praw-dev organization on GitHub.

`February 2016
<https://github.com/praw-dev/praw/commit/252083ef1dbfe6ea53c2dc99ac235b4ba330b658>`_:
Bryce began work on PRAW4, a complete rewrite of PRAW.


License
-------

Async PRAW uses the same license as PRAW uses. PRAW's source (v4.0.0+) is provided under the `Simplified BSD License
<https://github.com/praw-dev/praw/blob/0860c11a9309c80621c267af7caeb6a993933744/LICENSE.txt>`_.

* Copyright (c), 2016, Bryce Boe

Earlier versions of PRAW were released under `GPLv3
<https://github.com/praw-dev/praw/blob/0c88697fdc26e75f87b68e2feb11e101e90ce215/COPYING>`_.
