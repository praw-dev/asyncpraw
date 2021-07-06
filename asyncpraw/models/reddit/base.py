"""Provide the RedditBase class."""
from typing import TYPE_CHECKING, Any, Dict, Optional, Union
from urllib.parse import urlparse

from ...exceptions import InvalidURL
from ..base import AsyncPRAWBase

if TYPE_CHECKING:  # pragma: no cover
    from .... import asyncpraw


class RedditBase(AsyncPRAWBase):
    """Base class that represents actual Reddit objects."""

    @staticmethod
    def _url_parts(url):
        parsed = urlparse(url)
        if not parsed.netloc:
            raise InvalidURL(url)
        return parsed.path.rstrip("/").split("/")

    def __eq__(self, other: Union[Any, str]) -> bool:
        """Return whether the other instance equals the current."""
        if isinstance(other, str):
            return other.lower() == str(self).lower()
        return (
            isinstance(other, self.__class__)
            and str(self).lower() == str(other).lower()
        )

    def __getattr__(self, attribute: str) -> Any:
        """Return the value of `attribute`."""
        if not attribute.startswith("_") and not self._fetched:
            raise AttributeError(
                "{0!r} object has no attribute {1!r}. {0!r} object has not been"
                " fetched, did you forget to execute '.load()'?".format(
                    self.__class__.__name__, attribute
                )
            )
        raise AttributeError(
            f"{self.__class__.__name__!r} object has no attribute {attribute!r}"
        )

    def __hash__(self) -> int:
        """Return the hash of the current instance."""
        return hash(self.__class__.__name__) ^ hash(str(self).lower())

    def __init__(
        self,
        reddit: "asyncpraw.Reddit",
        _data: Optional[Dict[str, Any]],
        _extra_attribute_to_check: Optional[str] = None,
        _fetched: bool = False,
        _str_field: bool = True,
    ):
        """Initialize a RedditBase instance (or a subclass).

        :param reddit: An instance of :class:`~.Reddit`.

        """
        super().__init__(reddit, _data=_data)
        self._fetched = _fetched
        if _str_field and self.STR_FIELD not in self.__dict__:
            if (
                _extra_attribute_to_check is not None
                and _extra_attribute_to_check in self.__dict__
            ):
                return
            raise ValueError(
                f"An invalid value was specified for {self.STR_FIELD}. Check that the "
                f"argument for the {self.STR_FIELD} parameter is not empty."
            )

    def __repr__(self) -> str:
        """Return an object initialization representation of the instance."""
        return f"{self.__class__.__name__}({self.STR_FIELD}={str(self)!r})"

    def __str__(self) -> str:
        """Return a string representation of the instance."""
        return getattr(self, self.STR_FIELD)

    def __ne__(self, other: Any) -> bool:
        """Return whether the other instance differs from the current."""
        return not self == other

    async def _fetch(self):  # pragma: no cover
        self._fetched = True

    def _reset_attributes(self, *attributes):
        for attribute in attributes:
            if attribute in self.__dict__:
                del self.__dict__[attribute]
        self._fetched = False

    async def load(self):
        """Re-fetches the object.

        This is used to explicitly fetch or re-fetch the object from reddit. This method
        can be used on any :class:`.RedditBase` object.

        .. code-block:: python

            await reddit_base_object.load()

        """
        await self._fetch()
