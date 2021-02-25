Running Multiple Instances of Async PRAW
========================================

Async PRAW performs rate limiting dynamically based on the HTTP response headers from
Reddit. As a result you can safely run a handful of Async PRAW instances without any
additional configuration.

.. note::

    Running more than a dozen or so instances of Async PRAW concurrently may
    occasionally result in exceeding Reddit's rate limits as each instance can only
    guess how many other instances are running.

If you are authorized on other users' behalf, each authorization should have its own
rate limit, even when running from a single IP address.

Multiple Programs
-----------------

The recommended way to run multiple instances of Async PRAW is to simply write separate
independent Python programs. With this approach one program can monitor a comment stream
and reply as needed, and another program can monitor a submission stream, for example.

If these programs need to share data consider using a third-party system such as a
database or queuing system.
