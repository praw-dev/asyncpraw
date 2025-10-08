"""Provides the Objector class."""

from __future__ import annotations

from datetime import datetime
from json import loads
from typing import TYPE_CHECKING, Any

from asyncpraw.exceptions import ClientException, RedditAPIException
from asyncpraw.util import snake_case_keys

if TYPE_CHECKING:
    import asyncpraw
    from asyncpraw.models.reddit.base import RedditBase


class Objector:
    """The objector builds :class:`.RedditBase` objects."""

    @classmethod
    def check_error(cls, data: list[Any] | dict[str, dict[str, str]]) -> None:
        """Raise an error if the argument resolves to an error object."""
        if error := cls.parse_error(data):
            raise error

    @classmethod
    def parse_error(cls, data: list[Any] | dict[str, dict[str, str]]) -> RedditAPIException | None:
        """Convert JSON response into an error object.

        :param data: The dict to be converted.

        :returns: An instance of :class:`.RedditAPIException`, or ``None`` if ``data``
            doesn't fit this model.

        """
        if isinstance(data, list):
            # Fetching a Submission returns a list (of two items). Although it's handled
            # manually in `Submission._fetch()`, assume it's a possibility here.
            return None

        errors = data.get("json", {}).get("errors")
        if errors is None:
            return None
        if len(errors) < 1:
            # See `Collection._fetch()`.
            msg = "successful error response"
            raise ClientException(msg, data)
        return RedditAPIException(errors)

    def __init__(self, reddit: asyncpraw.Reddit, parsers: dict[str, Any] | None = None) -> None:
        """Initialize an :class:`.Objector` instance.

        :param reddit: An instance of :class:`.Reddit`.

        """
        self.parsers = {} if parsers is None else parsers
        self._reddit = reddit

    def _objectify_dict(self, *, data: dict[str, Any]) -> RedditBase:
        """Create :class:`.RedditBase` objects from dicts.

        :param data: The structured data, assumed to be a dict.

        :returns: An instance of :class:`.RedditBase`.

        """
        if {"messages", "modActions"}.issubset(data) and {
            "conversations",
            "conversation",
        }.intersection(data):
            # fetched conversation
            data.update(data.pop("conversation") if "conversation" in data else data.pop("conversations"))
            parser = self.parsers["ModmailConversation"]
            parser._convert_conversation_objects(data, self._reddit)
        elif {"messages", "modActions"}.issubset(data) or {
            "legacyFirstMessageId",
            "state",
        }.issubset(data):
            # not fetched conversation i.e., from conversations()
            del data["objIds"]  # delete objIds since it could be missing data
            parser = self.parsers["ModmailConversation"]
        elif {"conversationIds", "conversations", "messages"}.issubset(data):
            # modmail conversations
            conversations = []
            for conversation_id in data["conversationIds"]:
                conversation = data["conversations"][conversation_id]
                # set if the numMessages is same as number of messages in objIds
                if conversation["numMessages"] == len([
                    obj for obj in conversation["objIds"] if obj["key"] == "messages"
                ]):
                    conversation["messages"] = [
                        self.objectify(data=data["messages"][obj_id["id"]]) for obj_id in conversation["objIds"]
                    ]
                conversations.append(conversation)
            data["conversations"] = conversations
            data = snake_case_keys(data)
            parser = self.parsers["ModmailConversations-list"]
        elif {"actionTypeId", "author", "date"}.issubset(data):
            # Modmail mod action
            data = snake_case_keys(data)
            parser = self.parsers["ModmailAction"]
        elif {"bodyMarkdown", "isInternal"}.issubset(data):
            # Modmail message
            data = snake_case_keys(data)
            parser = self.parsers["ModmailMessage"]
        elif {"kind", "short_name", "violation_reason"}.issubset(data):
            # This is a Rule
            parser = self.parsers["rule"]
        elif {"isAdmin", "isDeleted"}.issubset(data):
            # Modmail author
            data = snake_case_keys(data)
            # Prevent clobbering base-36 id
            del data["id"]
            data["is_subreddit_mod"] = data.pop("is_mod")
            parser = self.parsers[self._reddit.config.kinds["redditor"]]
        elif {"banStatus", "muteStatus", "recentComments"}.issubset(data):
            # Modmail user
            data = snake_case_keys(data)
            data["created_string"] = data.pop("created")
            parser = self.parsers[self._reddit.config.kinds["redditor"]]
        elif {"displayName", "id", "type"}.issubset(data):
            # Modmail subreddit
            data = snake_case_keys(data)
            parser = self.parsers[self._reddit.config.kinds[data["type"]]]
        elif {"date", "id", "name"}.issubset(data) or {
            "id",
            "name",
            "permissions",
        }.issubset(data):
            parser = self.parsers[self._reddit.config.kinds["redditor"]]
        elif {"text", "url"}.issubset(data):
            key = "Button" if "color" in data or "linkUrl" in data else "MenuLink"
            parser = self.parsers[key]
        elif {"children", "text"}.issubset(data):
            parser = self.parsers["Submenu"]
        elif {"height", "url", "width"}.issubset(data):
            parser = self.parsers["Image"]
        elif {"isSubscribed", "name", "subscribers"}.issubset(data):
            # discards icon and subscribed information
            data["display_name"] = data["name"]
            del data["name"]
            parser = self.parsers[self._reddit.config.kinds["subreddit"]]
        elif {"authorFlairType", "name"}.issubset(data):
            # discards flair information
            parser = self.parsers[self._reddit.config.kinds["redditor"]]
        elif {"parent_id"}.issubset(data):
            parser = self.parsers[self._reddit.config.kinds["comment"]]
        elif "collection_id" in data:
            parser = self.parsers["Collection"]
        elif {"moderators", "moderatorIds", "allUsersLoaded", "subredditId"}.issubset(data):
            data = snake_case_keys(data)
            moderators = []
            for mod_id in data["moderator_ids"]:
                mod = snake_case_keys(data["moderators"][mod_id])
                mod["mod_permissions"] = list(mod["mod_permissions"].keys())
                moderators.append(mod)
            data["moderators"] = moderators
            parser = self.parsers["moderator-list"]
        elif "username" in data:
            data["name"] = data.pop("username")
            parser = self.parsers[self._reddit.config.kinds["redditor"]]
        elif {"mod_permissions", "name", "sr", "subscribers"}.issubset(data):
            data["display_name"] = data["sr"]
            parser = self.parsers[self._reddit.config.kinds["subreddit"]]
        elif {"drafts", "subreddits"}.issubset(data):  # Draft list
            subreddit_parser = self.parsers[self._reddit.config.kinds["subreddit"]]
            user_subreddit_parser = self.parsers["UserSubreddit"]
            subreddits = {
                subreddit["name"]: (
                    user_subreddit_parser.parse(subreddit, self._reddit)
                    if subreddit["display_name_prefixed"].startswith("u/")
                    else subreddit_parser.parse(subreddit, self._reddit)
                )
                for subreddit in data.pop("subreddits")
            }
            for draft in data["drafts"]:
                if draft["subreddit"]:
                    draft["subreddit"] = subreddits[draft["subreddit"]]
                draft["modified"] = datetime.fromtimestamp(draft["modified"] / 1000).astimezone()
            parser = self.parsers["DraftList"]
        elif {"mod_action_data", "user_note_data"}.issubset(data):
            redditor_parser = self.parsers[self._reddit.config.kinds["redditor"]]
            subreddit_parser = self.parsers[self._reddit.config.kinds["subreddit"]]
            data["moderator"] = redditor_parser(self._reddit, data["operator"])
            data["subreddit"] = subreddit_parser(self._reddit, data["subreddit"])
            data["user"] = redditor_parser(self._reddit, data["user"])
            # move these sub dict values into the main dict for simplicity
            data.update(data["mod_action_data"])
            del data["mod_action_data"]
            data.update(data["user_note_data"])
            del data["user_note_data"]
            parser = self.parsers["mod_note"]
        elif (
            "created" in data
            and isinstance(data["created"], dict)
            and {"mod_action_data", "user_note_data"}.issubset(data["created"])
        ):
            data = data["created"]
            return self._objectify_dict(data=data)
        else:
            if "user" in data:
                parser = self.parsers[self._reddit.config.kinds["redditor"]]
                data["user"] = parser.parse({"name": data["user"]}, self._reddit)
            return data
        return parser.parse(data, self._reddit)

    def objectify(
        self, *, data: dict[str, Any] | list[Any] | bool | None
    ) -> RedditBase | dict[str, Any] | list[Any] | bool | None:
        """Create :class:`.RedditBase` objects from data.

        :param data: The structured data.

        :returns: An instance of :class:`.RedditBase`, or ``None`` if given ``data`` is
            ``None``.

        """
        if data is None:  # 204 no content
            return None
        if isinstance(data, list):
            return [self.objectify(data=item) for item in data]
        if isinstance(data, bool):  # Reddit.username_available
            return data
        if "json" in data and "errors" in data["json"]:
            errors = data["json"]["errors"]
            if len(errors) > 0:
                raise RedditAPIException(errors)
        if "kind" in data and ("shortName" in data or data["kind"] in {"menu", "moderators"}):
            # This is a widget
            parser = self.parsers.get(data["kind"], self.parsers["widget"])
            return parser.parse(data, self._reddit)
        if {"kind", "data"}.issubset(data) and data["kind"] in self.parsers:
            parser = self.parsers[data["kind"]]
            if data["kind"] == "ModeratedList":
                return parser.parse(data, self._reddit)
            return parser.parse(data["data"], self._reddit)
        if "json" in data and "data" in data["json"]:
            if "websocket_url" in data["json"]["data"]:
                return data
            if "things" in data["json"]["data"]:  # Submission.reply
                return self.objectify(data=data["json"]["data"]["things"])
            if "rules" in data["json"]["data"]:
                return self.objectify(data=loads(data["json"]["data"]["rules"]))
            if "drafts_count" in data["json"]["data"] and all(
                key not in data["json"]["data"] for key in ["name", "url"]
            ):  # Draft
                data["json"]["data"].pop("drafts_count")
                return self.parsers["Draft"].parse(data["json"]["data"], self._reddit)
            if "url" in data["json"]["data"]:  # Subreddit.submit
                # The URL is the URL to the submission, so it's removed.
                del data["json"]["data"]["url"]
                parser = self.parsers[self._reddit.config.kinds["submission"]]
                if data["json"]["data"]["id"].startswith(f"{self._reddit.config.kinds['submission']}_"):
                    # With polls, Reddit returns a fullname but calls it an "id". This
                    # fixes this by coercing the fullname into an id.
                    data["json"]["data"]["id"] = data["json"]["data"]["id"].split("_", 1)[1]
            else:
                parser = self.parsers["LiveUpdateEvent"]
            return parser.parse(data["json"]["data"], self._reddit)
        if {"is_public_link", "title", "body"}.issubset(data):
            parser = self.parsers["Draft"]
            return parser.parse(data, self._reddit)
        if "rules" in data:
            return self.objectify(data=data["rules"])
        if isinstance(data, dict):
            return self._objectify_dict(data=data)
        return data
