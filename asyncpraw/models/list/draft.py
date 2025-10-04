"""Provide the DraftList class."""

from asyncpraw.models.list.base import BaseList


class DraftList(BaseList):
    """A list of :class:`.Draft` objects. Works just like a regular list."""

    CHILD_ATTRIBUTE = "drafts"
