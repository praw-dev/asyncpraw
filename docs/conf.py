import sys
from datetime import datetime

# Do not touch these. They use the local Async PRAW over the global Async PRAW.
sys.path.insert(0, ".")
sys.path.insert(1, "..")

from asyncpraw import __version__  # noqa: E402

copyright = datetime.today().strftime("%Y, Joel Payne")
exclude_patterns = ["_build"]
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinxcontrib_trio",
]
html_theme = "furo"
htmlhelp_basename = "Async PRAW"
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}
master_doc = "index"
nitpick_ignore = [
    ("py:class", "IO"),
    ("py:class", "prawcore._async.auth.AsyncBaseAuthorizer"),
    ("py:class", "prawcore.AsyncRequestor"),
]
nitpicky = True
project = "Async PRAW"
pygments_style = "sphinx"
release = __version__
source_suffix = ".rst"
suppress_warnings = ["image.nonlocal_uri"]
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
