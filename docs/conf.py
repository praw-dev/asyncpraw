import sys
from datetime import datetime

# Do not touch these. They use the local Async PRAW over the global Async PRAW.
sys.path.insert(0, ".")
sys.path.insert(1, "..")

from asyncpraw import __version__

always_use_bars_union = True
autodoc_typehints = "description"
copyright = datetime.today().strftime("%Y, Joel Payne")
exclude_patterns = ["_build"]
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
    "sphinxcontrib_trio",
]
html_theme = "furo"
intersphinx_mapping = {
    "asyncprawcore": ("https://asyncprawcore.readthedocs.io/en/stable/", None),
    "python": ("https://docs.python.org/3", None),
}
# GitHub renders wiki/file anchors client-side, so linkcheck cannot verify them.
linkcheck_anchors_ignore_for_url = [r"https://github\.com/.*"]
# The Reddit Help / Zendesk support site blocks automated requests with a 403.
linkcheck_ignore = [
    r"https://(\w+\.)?reddithelp\.com/.*",
    r"https://reddit\.zendesk\.com/.*",
]
nitpicky = True
project = "Async PRAW"
release = __version__
version = ".".join(__version__.split(".", 2)[:2])


def skip(app, what, name, obj, skip, options):
    if name in {
        "__call__",
        "__contains__",
        "__getitem__",
        "__init__",
        "__iter__",
        "__len__",
    }:
        return False
    return skip


def setup(app):
    app.connect("autodoc-skip-member", skip)
