"""Type-checking regression guard for dynamic Reddit attribute access.

Async PRAW populates many objects from Reddit response data rather than declaring their
attributes, because Reddit adds and removes fields without notice. Accessing such an
attribute must therefore resolve to ``Any`` for a downstream type checker rather than
raising an attribute error.

Shipping a ``py.typed`` marker is only safe if these accesses type cleanly: once Async
PRAW advertises itself as typed, every dynamic attribute access would otherwise light up
as an error in downstream projects. :class:`.RedditBase` already returns ``Any`` from
``__getattr__``; this module guards the :class:`.AsyncPRAWBase` data classes that do not
inherit it.

This module is analyzed by pyright (it is added to ``tool.pyright``'s ``include``) and
is never executed, so the bodies below are type-checked but the functions are never
called.

"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asyncpraw.models import ModNote, Stylesheet, Trophy
    from asyncpraw.models.reddit.poll import PollData, PollOption
    from asyncpraw.models.reddit.widgets import Button, Image, Submenu, TextArea


def _dynamic_attributes_resolve_to_any(
    button: Button,
    image: Image,
    mod_note: ModNote,
    poll_data: PollData,
    poll_option: PollOption,
    stylesheet: Stylesheet,
    submenu: Submenu,
    text_area: TextArea,
    trophy: Trophy,
) -> list[object]:
    """Access undeclared, Reddit-provided attributes; each must type as ``Any``."""
    return [
        button.color,
        image.url,
        mod_note.label,
        poll_data.total_vote_count,
        poll_option.vote_count,
        stylesheet.images,
        submenu.text,
        text_area.text,
        trophy.icon_70,
    ]
