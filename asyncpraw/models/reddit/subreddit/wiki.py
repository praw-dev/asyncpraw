"""Provide the SubredditWiki class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from asyncpraw.const import API_PATH
from asyncpraw.models.reddit.subreddit.relationship import SubredditRelationship
from asyncpraw.models.reddit.wikipage import WikiPage

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    import asyncpraw.models


class SubredditWiki:
    """Provides a set of wiki functions to a :class:`.Subreddit`."""

    async def __aiter__(self) -> AsyncIterator[WikiPage]:
        """Iterate through the pages of the wiki.

        This method is to be used to discover all wikipages for a subreddit:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            async for wikipage in subreddit.wiki:
                print(wikipage)

        """
        response = await self.subreddit._reddit.get(
            API_PATH["wiki_pages"].format(subreddit=self.subreddit),
            params={"unique": self.subreddit._reddit._next_unique},
        )
        for page_name in response["data"]:
            yield WikiPage(self.subreddit._reddit, self.subreddit, page_name)

    def __init__(self, subreddit: asyncpraw.models.Subreddit) -> None:
        """Initialize a :class:`.SubredditWiki` instance.

        :param subreddit: The subreddit whose wiki to work with.

        """
        self.banned = SubredditRelationship(subreddit, "wikibanned")
        self.contributor = SubredditRelationship(subreddit, "wikicontributor")
        self.subreddit = subreddit

    async def create(
        self,
        *,
        content: str,
        name: str,
        reason: str | None = None,
        **other_settings: Any,
    ) -> WikiPage:
        """Create a new :class:`.WikiPage`.

        :param name: The name of the new :class:`.WikiPage`. This name will be
            normalized.
        :param content: The content of the new :class:`.WikiPage`.
        :param reason: The reason for the creation.
        :param other_settings: Additional keyword arguments to pass.

        To create the wiki page ``"praw_test"`` in r/test try:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            await subreddit.wiki.create(
                name="praw_test", content="wiki body text", reason="Async PRAW Test Creation"
            )

        """
        name = name.replace(" ", "_").lower()
        new = WikiPage(self.subreddit._reddit, self.subreddit, name)
        await new.edit(content=content, reason=reason, **other_settings)
        return new

    async def get_page(self, /, page_name: str, *, fetch: bool = True) -> WikiPage:
        """Return the :class:`.WikiPage` for the :class:`.Subreddit` named ``page_name``.

        :param page_name: Name of the wikipage.
        :param fetch: Determines if Async PRAW will fetch the object (default:
            ``True``).

        This method is to be used to fetch a specific wikipage, like so:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            wikipage = await subreddit.wiki.get_page("proof")
            print(wikipage.content_md)

        """
        wikipage = WikiPage(self.subreddit._reddit, self.subreddit, page_name.lower())
        if fetch:
            await wikipage._fetch()
        return wikipage

    def revisions(
        self, **generator_kwargs: Any
    ) -> AsyncIterator[dict[str, asyncpraw.models.Redditor | WikiPage | str | int | bool | None]]:
        """Return a :class:`.ListingGenerator` for recent wiki revisions.

        Additional keyword arguments are passed in the initialization of
        :class:`.ListingGenerator`.

        To view the wiki revisions for ``"praw_test"`` in r/test try:

        .. code-block:: python

            subreddit = await reddit.subreddit("test")
            page = await subreddit.wiki.get_page("praw_test")
            async for item in page.revisions():
                print(item)

        """
        url = API_PATH["wiki_revisions"].format(subreddit=self.subreddit)
        return WikiPage._revision_generator(generator_kwargs=generator_kwargs, subreddit=self.subreddit, url=url)
