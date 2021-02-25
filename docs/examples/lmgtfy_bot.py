#!/usr/bin/env python3
import asyncio
from urllib.parse import quote_plus

import asyncpraw

QUESTIONS = ["what is", "who is", "what are"]
REPLY_TEMPLATE = "[Let me google that for you](https://lmgtfy.com/?q={})"


async def main():
    reddit = asyncpraw.Reddit(
        user_agent="LMGTFY (by u/USERNAME)",
        client_id="CLIENT_ID",
        client_secret="CLIENT_SECRET",
        username="USERNAME",
        password="PASSWORD",
    )

    subreddit = await reddit.subreddit("AskReddit")
    async for submission in subreddit.stream.submissions():
        await process_submission(submission)


async def process_submission(submission):
    # Ignore titles with more than 10 words as they probably are not simple
    # questions.
    if len(submission.title.split()) > 10:
        return

    normalized_title = submission.title.lower()
    for question_phrase in QUESTIONS:
        if question_phrase in normalized_title:
            url_title = quote_plus(submission.title)
            reply_text = REPLY_TEMPLATE.format(url_title)
            print(f"Replying to: {submission.title}")
            await submission.reply(reply_text)
            # A reply has been made so do not attempt to match other phrases.
            break


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
