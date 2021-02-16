"""Provide the ModAction class."""
from typing import TYPE_CHECKING, Union

from .base import AsyncPRAWBase
from .reddit.redditor import Redditor

if TYPE_CHECKING:  # pragma: no cover
    from ... import asyncpraw


class ModAction(AsyncPRAWBase):
    """Represent a moderator action."""

    @property
    def mod(self) -> "asyncpraw.models.Redditor":
        """Return the :class:`.Redditor` who the action was issued by."""
        return Redditor(self._reddit, name=self._mod)  # pylint: disable=no-member

    @mod.setter
    def mod(self, value: Union[str, "asyncpraw.models.Redditor"]):
        self._mod = value  # pylint: disable=attribute-defined-outside-init
