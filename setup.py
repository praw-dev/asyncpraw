"""asyncpraw setup.py"""
import os
import re
from codecs import open
from os import path

from setuptools import find_packages, setup

PACKAGE_NAME = "asyncpraw"
HERE = path.abspath(path.dirname(__file__))
with open(path.join(HERE, "README.rst"), encoding="utf-8") as fp:
    README = fp.read()
with open(path.join(HERE, PACKAGE_NAME, "const.py"), encoding="utf-8") as fp:
    VERSION = re.search('__version__ = "([^"]+)"', fp.read()).group(1)

extras = {
    "ci": ["coveralls"],
    "dev": ["packaging"],
    "lint": ["pre-commit"],
    "readthedocs": [
        "sphinx",
        "sphinx-rtd-dark-mode",
        "sphinx_rtd_theme",
        "sphinxcontrib-trio",
    ],
    "test": [
        "asynctest >=0.13.0 ; python_version < '3.8'",
        "mock >=0.8",
        "pytest ==7.2.*",
        "pytest-asyncio",
        "pytest-vcr",
        "testfixtures >4.13.2, <7",
        "vcrpy >=4.1.1"
        if os.getenv("PYPI_UPLOAD", False)
        else "vcrpy@git+https://github.com/kevin1024/vcrpy.git@b1bc5c3a02db0447c28ab9a4cee314aeb6cdf1a7",
    ],
}
extras["lint"] += extras["readthedocs"]
extras["dev"] += extras["lint"] + extras["test"]

setup(
    name=PACKAGE_NAME,
    author="Joel Payne",
    author_email="lilspazjoekp@gmail.com",
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Utilities",
    ],
    description=(
        'Async PRAW, an abbreviation for "Asynchronous Python Reddit API Wrapper", is a'
        " python package that allows for simple access to Reddit's API."
    ),
    extras_require=extras,
    install_requires=[
        "aiofiles <1",
        "aiohttp <4",
        "aiosqlite <=0.17.0",
        "asyncio_extras <=1.3.2",
        "asyncprawcore >=2.1, <3",
        "update_checker >=0.18",
    ],
    keywords="reddit api wrapper asyncpraw praw async asynchronous",
    license="Simplified BSD License",
    long_description=README,
    package_data={
        "": ["LICENSE.txt", "praw_license.txt"],
        PACKAGE_NAME: ["*.ini", "images/*.png"],
    },
    packages=find_packages(exclude=["tests", "tests.*", "tools", "tools.*"]),
    project_urls={
        "Change Log": "https://asyncpraw.readthedocs.io/en/latest/package_info/change_log.html",
        "Documentation": "https://asyncpraw.readthedocs.io/",
        "Issue Tracker": "https://github.com/praw-dev/asyncpraw/issues",
        "Source Code": "https://github.com/praw-dev/asyncpraw",
    },
    version=VERSION,
)
