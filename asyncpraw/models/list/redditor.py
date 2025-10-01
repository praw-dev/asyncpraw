"""Provide the RedditorList class."""

from asyncpraw.models.list.base import BaseList


class RedditorList(BaseList):
    """A list of :class:`.Redditor` objects. Works just like a regular list."""

    CHILD_ATTRIBUTE = "children"
