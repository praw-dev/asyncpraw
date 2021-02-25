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

Async PRAW, an abbreviation for "Asynchronous Python Reddit API Wrapper", is a Python
package that allows for simple access to Reddit's API. Async PRAW aims to be easy to use
and internally follows all of `Reddit's API rules
<https://github.com/reddit/reddit/wiki/API>`_. With Async PRAW there's no need to
introduce ``sleep`` calls in your code. Give your client an appropriate user agent and
you're set.

.. _installation:

Installation
------------

Async PRAW is supported on Python 3.6+. The recommended way to install Async PRAW is via
`pip <https://pypi.python.org/pypi/pip>`_.

.. code-block:: bash

    pip install asyncpraw

To install the latest development version of Async PRAW run the following instead:

.. code-block:: bash

    pip install --upgrade https://github.com/praw-dev/asyncpraw/archive/master.zip

For instructions on installing Python and pip see "The Hitchhiker's Guide to Python"
`Installation Guides <https://docs.python-guide.org/en/latest/starting/installation/>`_.

Quickstart
----------

Assuming you already have a credentials for a script-type OAuth application you can
instantiate an instance of Async PRAW like so:

.. code-block:: python

    import asyncpraw

    reddit = asyncpraw.Reddit(
        client_id="CLIENT_ID",
        client_secret="CLIENT_SECRET",
        password="PASSWORD",
        user_agent="USERAGENT",
        username="USERNAME",
    )

With the ``reddit`` instance you can then interact with Reddit:

.. code-block:: python

    # Create a submission to r/test
    subreddit = await reddit.subreddit("test")
    await subreddit.submit("Test Submission", url="https://reddit.com")

    # Comment on a known submission
    submission = await reddit.submission(
        url="https://www.reddit.com/comments/5e1az9", lazy=True
    )
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

Please see Async PRAW's `documentation <https://asyncpraw.readthedocs.io/>`_ for more
examples of what you can do with Async PRAW.

Async PRAW Discussion and Support
---------------------------------

For those new to Python, or would otherwise consider themselves a Python beginner,
please consider asking questions on the `r/learnpython
<https://www.reddit.com/r/learnpython>`_ subreddit. There are wonderful people there who
can help with general Python and simple Async PRAW related questions.

Otherwise, there are a few official places to ask questions about Async PRAW:

`r/redditdev <https://www.reddit.com/r/redditdev>`_ is the best place on Reddit to ask
Async PRAW related questions. This subreddit is for all Reddit API related discussion so
please tag submissions with *[Async PRAW]*. Please perform a search on the subreddit
first to see if anyone has similar questions.

Real-time chat can be conducted via the `PRAW Slack Organization
<https://join.slack.com/t/praw/shared_invite/enQtOTUwMDcxOTQ0NzY5LWVkMGQ3ZDk5YmQ5MDEwYTZmMmJkMTJkNjBkNTY3OTU0Y2E2NGRlY2ZhZTAzMWZmMWRiMTMwYjdjODkxOGYyZjY>`_
(please create an issue if that invite link has expired).

Please do not directly message any of the contributors via Reddit, email, or Slack
unless they have indicated otherwise. We strongly encourage everyone to help others with
their questions.

Please file bugs and feature requests as issues on `GitHub
<https://github.com/praw-dev/asyncpraw/issues>`_ after first searching to ensure a
similar issue was not already filed. If such an issue already exists please give it a
thumbs up reaction. Comments to issues containing additional information are certainly
welcome.

.. note::

    This project is released with a `Contributor Code of Conduct
    <https://github.com/praw-dev/asyncpraw/blob/master/CODE_OF_CONDUCT.md>`_. By
    participating in this project you agree to abide by its terms.

Documentation
-------------

Async PRAW's documentation is located at https://asyncpraw.readthedocs.io/.

History
-------

`February 2019
<https://github.com/praw-dev/asyncpraw/commit/55480eb3d59dc7bc3d1480d83b98c95effc77181>`_:
Joel forked PRAW and began work on Async PRAW, an asynchronous compatible version of
PRAW.

`July 2020
<https://github.com/praw-dev/asyncpraw/commit/b8b8a4bf3618639968e8be379e85e2ff84f2307a>`_:
Async PRAW was moved into the praw-dev namespace.

License
-------

Async PRAW's source (v7.1.1+) is provided under the `Simplified BSD License
<https://github.com/praw-dev/asyncpraw/blob/30796acc29b4ba2335cf0eab414477702c29452f/LICENSE.txt>`_.

- Copyright ©, 2020, Joel Payne
