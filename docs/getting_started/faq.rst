Frequently Asked Questions
==========================

.. _faq1:

Q: How can I refresh a comment/subreddit/submission?

A: There is two ways to do this:

- Directly calling the constructors will refresh the value:

  .. code-block:: python

      await reddit.comment(id=comment.id)
      await reddit.subreddit(display_name=subreddit.display_name)
      await reddit.submission(id=submission.id)

- Calling :meth:`~.RedditBase.load`:

  .. code-block:: python

      await comment.load()
      await subreddit.load()
      await submission.load()

.. _faq2:

Q: Whenever I try to do anything, I get an ``invalid_grant`` error. What is the cause?

A: This means that either you provided the wrong password and/or the account you are
trying to sign in with has 2FA enabled, and as such, either needs a 2FA token or a
refresh token to sign in. A refresh token is preferred, because then you will not need
to enter a 2FA token in order to sign in, and the session will last for longer than an
hour. Refer to :ref:`2FA` and :ref:`refresh_token` in order to use the respective auth
methods.

.. _faq3:

Q: Some options (like getting moderator logs from r/mod) keep on timing out. How can I
extend the timeout?

A: Set the timeout config option or initialize :class:`.Reddit` with a timeout of your
choosing.

.. _faq4:

Q: Help, I keep on getting redirected to ``/r/subreddit/login/``!

Q2: I keep on getting this exception:

.. code-block:: text

    asyncprawcore.exceptions.Redirect: Redirect to /r/subreddit/login/ (You may be trying to perform a non-read-only action via a read-only instance.)

A: Async PRAW is most likely in read-only mode. This normally occurs when Async PRAW is
authenticated without a username and password or a refresh token. In order to perform
this action, the Reddit instance needs to be authenticated. See :ref:`oauth_options` to
see the available authentication methods.

.. _faq5:

Q: Help, searching for URLs keeps on redirecting me to ``/submit``!

Q2: I keep on getting this exception: ``asyncprawcore.exceptions.Redirect: Redirect to
/submit``

A: Reddit redirects URL searches to the submit page of the URL. To search for the URL,
prefix ``url:`` to the url and surround the url in quotation marks.

For example, the code block:

.. code-block:: python

    subreddit = await reddit.subreddit("all")
    async for result in subreddit.search("https://google.com"):
        # do things with results
        ...

Will become this code block:

.. code-block:: python

    subreddit = await reddit.subreddit("all")
    async for result in subreddit.search('url:"https://google.com"'):
        # do things with results
        ...
