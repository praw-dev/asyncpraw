Migrating to Async PRAW
=======================

With the conversion to async, there are few critical changes that had to be made. This
page outlines a few those changes.

Network Requests
----------------

.. _network_requests:

Async PRAW utilizes `aiohttp <https://docs.aiohttp.org/>`_ to make network requests to
Reddit's API. Since aiohttp can only be used in an asynchronous environment, all network
requests need to be awaited. Due to this, most Async PRAW methods need to be awaited as
well. You can tell if a method needs awaited by looking at the docs. For example,
:meth:`.me` has the word ``await`` before ``me(use_cache: bool = True)`` in the header
for that method since that method makes a network request.

Lazy Loading
------------

.. _lazy_loading:

In PRAW, the majority of objects are lazily loaded and are not fetched until an
attribute is accessed. With Async PRAW, objects can be fetched on initialization and
some now do this by default. For example:

- PRAW:

  .. code-block:: python

      # network request is not made and object is lazily loaded
      submission = reddit.submission("id")

      # network request is made and object is fully fetched
      print(submission.score)

- Async PRAW:

  .. code-block:: python

      # network request made and object is fully loaded
      submission = await reddit.submission("id")

      # network request is not made as object is already fully fetched
      print(submission.score)

Now, lazy loading is not gone completely and can still be done. For example, if you only
want to remove a post, you don't need the object fully fetched to do that.

- PRAW:

  .. code-block:: python

      # object is not fetched and is only removed
      reddit.submission("id").mod.remove()

- Async PRAW:

  .. code-block:: python

      # network request is not made and object is lazily loaded
      submission = await reddit.submission("id", lazy=True)

      # object is not fetched and is only removed
      await submission.mod.remove()

The following objects are still lazily loaded by default:

- :class:`.Subreddit`
- :class:`.Redditor`
- :class:`.LiveThread`
- :class:`.Multireddit`

You can pass ``fetch=True`` in their respective helper method to fully load it.

Inversely, the following objects are now fully fetched when initialized:

- :class:`.Submission`
- :class:`.Comment`
- :class:`.WikiPage`
- :class:`.RemovalReason`
- :class:`.Collection`
- :class:`.Emoji`
- :class:`.LiveUpdate`
- :class:`.Rule`
- :class:`.Preferences`

You can pass ``lazy=True`` in their respective helper method if you want to lazily load
it.

In addition, there will be a ``load()`` method provided for manually fetching/refreshing
objects that subclass :class:`.RedditBase`. If you need to later on access an attribute
you need to call the ``.load()`` method first:

.. code-block:: python

    # object is lazily loaded and no requests are made
    submission = await reddit.submission("id", lazy=True)
    ...
    # network request is made and item is fully fetched
    await submission.load()

    # network request is not made as object is already fully fetched
    print(submission.score)

Getting items by Indices
------------------------

.. _objects_by_indices:

In PRAW you could get specific :class:`.WikiPage`, :class:`.RemovalReason`,
:class:`.Emoji`, :class:`.LiveUpdate`, and :class:`.Rule` objects by using string
indices. This will no longer work and has been converted to a ``.get_<item name>(item)``
method. Also, they are not lazily loaded by default anymore.

- PRAW:

  .. code-block:: python

      # lazily creates a WikiPage instance
      page = subreddit.wiki["page"]

      # network request is made and item is fully fetched
      print(page.content_md)

- Async PRAW:

  .. code-block:: python

      # network request made and object is fully loaded
      page = await subreddit.wiki.get_page("page")

      # network request is not made as WikiPage is already fully fetched``
      print(page.content_md)

      # using slices
      rule = await subreddit.mod.rules.get_rule(slice(-3, None))  # to get the last 3 rules
