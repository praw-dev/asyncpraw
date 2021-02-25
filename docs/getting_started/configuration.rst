.. _configuration:

Configuring Async PRAW
======================

.. note::

    Async PRAW is fully compatible with the configuration system that PRAW uses.

.. toctree::
    :maxdepth: 2

    configuration/options

Configuration options can be provided to Async PRAW in one of three ways:

.. toctree::
    :maxdepth: 1

    configuration/prawini
    configuration/reddit_initialization
    configuration/environment_variables

Environment variables have the highest priority, followed by keyword arguments to
:class:`.Reddit`, and finally settings in ``praw.ini`` files.

.. _proxy-support:

Using an HTTP or HTTPS proxy with Async PRAW
--------------------------------------------

Async PRAW internally relies upon the `aiohttp <https://docs.aiohttp.org/>`_ package to
handle HTTP requests. Aiohttp supports use of ``HTTP_PROXY`` and ``HTTPS_PROXY``
environment variables in order to proxy HTTP and HTTPS requests respectively [`ref
<https://docs.aiohttp.org/en/stable/client_advanced.html?highlight=proxy#proxy-support>`_].

Given that Async PRAW exclusively communicates with Reddit via HTTPS, only the
``HTTPS_PROXY`` option should be required.

For example, if you have a script named ``prawbot.py``, the ``HTTPS_PROXY`` environment
variable can be provided on the command line like so:

.. code-block:: bash

    HTTPS_PROXY=http://localhost:3128 ./prawbot.py

Contrary to the Requests library, aiohttp won’t read environment variables by default.
But you can do so by passing ``trust_env=True`` into aiohttp and configuring Async PRAW
like so:

.. code-block:: python

    import asyncpraw
    from aiohttp import ClientSession


    session = ClientSession(trust_env=True)
    reddit = asyncpraw.Reddit(
        client_id="SI8pN3DSbt0zor",
        client_secret="xaxkj7HNh8kwg8e5t4m6KvSrbTI",
        password="1guiwevlfo00esyy",
        requestor_kwargs={"session": session},  # pass Session
        user_agent="testscript by u/fakebot3",
        username="fakebot3",
    )

Configuring a custom aiohttp ClientSession
------------------------------------------

Async PRAW uses aiohttp_ to handle networking. If your use-case requires custom
configuration, it is possible to configure a `ClientSession
<https://docs.aiohttp.org/en/stable/client_advanced.html>`_ and then use it with Async
PRAW.

For example, some networks use self-signed SSL certificates when connecting to HTTPS
sites. By default, this would raise an exception in Aiohttp. To use a self-signed SSL
certificate without an exception from Aiohttp, first export the certificate as a
``.pem`` file. Then configure Async PRAW like so:

.. code-block:: python

    import ssl

    import aiohttp
    import asyncpraw


    ssl_ctx = ssl.create_default_context(cafile="/path/to/certfile.pem")

    conn = aiohttp.TCPConnector(ssl_context=ssl_ctx)
    session = aiohttp.ClientSession(connector=conn)
    reddit = asyncpraw.Reddit(
        client_id="SI8pN3DSbt0zor",
        client_secret="xaxkj7HNh8kwg8e5t4m6KvSrbTI",
        password="1guiwevlfo00esyy",
        requestor_kwargs={"session": session},  # pass Session
        user_agent="testscript by u/fakebot3",
        username="fakebot3",
    )

The code above creates a ``ClientSession`` and `configures it to use a custom
certificate
<https://docs.aiohttp.org/en/stable/client_advanced.html#ssl-control-for-tcp-sockets>`_,
then passes it as a parameter when creating the :class:`.Reddit` instance. Note that the
example above uses a :ref:`password_flow` authentication type, but this method will work
for any authentication type.
