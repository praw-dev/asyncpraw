#!/usr/bin/env python3
"""This example demonstrates using the sqlite token manager for refresh tokens.

In order to run this program, you will first need to obtain one or more valid refresh
tokens. You can use the ``obtain_refresh_token.py`` example to help.

In this example, refresh tokens will be saved into a file ``tokens.sqlite3`` relative to
your current working directory. If your current working directory is under version
control it is strongly encouraged you add ``tokens.sqlite3`` to the version control ignore
list.

This example differs primarily from ``use_file_token_manager.py`` due to the fact that a
shared SQLite3 database can manage many ``refresh_tokens``. While each instance of
Reddit still needs to have 1-to-1 mapping to a token manager, multiple Reddit instances
can concurrently share access to the same SQLite3 database; the same cannot be done with
the FileTokenManager.

Usage:

    export praw_client_id=hIkgfjAZpV9u4A
    export praw_client_secret=jHXu3riMfnn2vEsUDTHMgSNjFWA
    python use_sqlite_token_manager.py test

"""
import asyncio
import os
import sys

import asyncpraw
from asyncpraw.util.token_manager import SQLiteTokenManager

DATABASE_PATH = "tokens.sqlite3"


async def main():
    if "praw_client_id" not in os.environ:
        sys.stderr.write("Environment variable ``praw_client_id`` must be defined\n")
        return 1
    if "praw_client_secret" not in os.environ:
        sys.stderr.write(
            "Environment variable ``praw_client_secret`` must be defined\n"
        )
        return 1
    if len(sys.argv) != 2:
        sys.stderr.write(
            "KEY must be provided.\n\nUsage: python3 use_sqlite_token_manager.py TOKEN_KEY\n"
        )
        return 1

    refresh_token_manager = SQLiteTokenManager(DATABASE_PATH, key=sys.argv[1])
    reddit = asyncpraw.Reddit(
        token_manager=refresh_token_manager,
        user_agent="sqlite_token_manager/v0 by u/bboe",
    )

    if not await refresh_token_manager.is_registered():
        refresh_token = input("Enter initial refresh token: ").strip()
        await refresh_token_manager.register(refresh_token)

    scopes = await reddit.auth.scopes()
    if scopes == {"*"}:
        print(f"{await reddit.user.me()} is authenticated with all scopes")
    elif "identity" in scopes:
        print(
            f"{await reddit.user.me()} is authenticated with the following scopes: {scopes}"
        )
    else:
        print(f"You are authenticated with the following scopes: {scopes}")
    await refresh_token_manager.close()
    await reddit.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
