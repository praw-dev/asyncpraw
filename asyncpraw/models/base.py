"""Provide the AsyncPRAWBase superclass."""
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:  # pragma: no cover
    import asyncpraw


class AsyncPRAWBase:
    """Superclass for all models in Async PRAW."""

    @staticmethod
    def _safely_add_arguments(*, arguments, key, **new_arguments):
        """Replace arguments[key] with a deepcopy and update.

        This method is often called when new parameters need to be added to a request.
        By calling this method and adding the new or updated parameters we can insure we
        don't modify the dictionary passed in by the caller.

        """
        value = deepcopy(arguments[key]) if key in arguments else {}
        value.update(new_arguments)
        arguments[key] = value

    @classmethod
    def parse(cls, data: Dict[str, Any], reddit: "asyncpraw.Reddit") -> Any:
        """Return an instance of ``cls`` from ``data``.

        :param data: The structured data.
        :param reddit: An instance of :class:`.Reddit`.

        """
        return cls(reddit, _data=data)

    def __init__(self, reddit: "asyncpraw.Reddit", _data: Optional[Dict[str, Any]]):
        """Initialize a :class:`.AsyncPRAWBase` instance.

        :param reddit: An instance of :class:`.Reddit`.

        """
        self._reddit = reddit
        if _data:
            for attribute, value in _data.items():
                setattr(self, attribute, value)
