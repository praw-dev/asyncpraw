"""Provide the ModAction class."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import AsyncPRAWBase
from .reddit.redditor import Redditor

if TYPE_CHECKING:  # pragma: no cover
    import asyncpraw.models


class ModAction(AsyncPRAWBase):
    """Represent a moderator action."""

    @property
    def mod(self) -> asyncpraw.models.Redditor:
        """Return the :class:`.Redditor` who the action was issued by."""
        return Redditor(self._reddit, name=self._mod)

    @mod.setter
    def mod(self, value: str | asyncpraw.models.Redditor) -> None:
        self._mod = value
