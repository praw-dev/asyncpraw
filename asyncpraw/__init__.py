"""
Python Reddit API Wrapper.

asyncpraw, an acronym for "Python Reddit API Wrapper", is a python package that
allows for simple access to reddit's API. asyncpraw aims to be as easy to use as
possible and is designed to follow all of reddit's API rules. You have to give
a useragent, everything else is handled by asyncpraw so you needn't worry about
violating them.

More information about asyncpraw can be found at https://github.com/asyncpraw-dev/asyncpraw
"""

from .const import __version__  # NOQA
from .reddit import Reddit  # NOQA
