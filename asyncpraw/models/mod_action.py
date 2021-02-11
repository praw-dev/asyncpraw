"""Provide the ModAction class."""
from typing import Union

from .base import AsyncPRAWBase
from .reddit.redditor import Redditor


class ModAction(AsyncPRAWBase):
    """Represent a moderator action."""

    @property
    def mod(self) -> "Redditor":
        """Return the Redditor who the action was issued by."""
        return Redditor(self._reddit, name=self._mod)  # pylint: disable=no-member

    @mod.setter
    def mod(self, value: Union[str, "Redditor"]):
        self._mod = value  # pylint: disable=attribute-defined-outside-init
