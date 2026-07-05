"""Read public-channel activity out of Slack and emit normalized message records.

The ONLY module that reads Slack content. Scope enforcement lives here:
public channels only — the bot token's scopes (channels:history, search:read.public)
make anything wider impossible at the API level, not just the code level.

Attribution: seeded persona messages are posted by the bot with a `username`
override, so records are attributed by that field when present; real user
messages are attributed by resolved display name.
"""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass, field, asdict

from .audit_log import AuditLog


@dataclass
class MessageRecord:
    channel: str            # channel name
    author: str             # display name (persona username override or real user)
    ts: str                 # Slack timestamp of the message
    text: str
    is_thread_parent: bool = False
    is_reply: bool = False
    reply_count: int = 0    # for thread parents
    mentions: list[str] = field(default_factory=list)  # user ids mentioned

    def to_dict(self) -> dict:
        return asdict(self)


class SlackReader:
    def __init__(self, token: str | None = None, audit: AuditLog | None = None):
        from slack_sdk import WebClient
        token = token or os.environ.get("SLACK_BOT_TOKEN")
        if not token:
            sys.exit("SLACK_BOT_TOKEN is not set.")
        self.client = WebClient(token=token)
        self.audit = audit or AuditLog()
        self._user_names: dict[str, str] = {}

    def _resolve_user(self, user_id: str) -> str:
        if user_id not in self._user_names:
            try:
                info = self.client.users_info(user=user_id)
                profile = info["user"]["profile"]
                self._user_names[user_id] = (
                    profile.get("display_name") or profile.get("real_name") or user_id
                )
            except Exception:
                self._user_names[user_id] = user_id
        return self._user_names[user_id]

    def _author_of(self, msg: dict) -> str | None:
        # Persona messages carry a username override; real messages carry a user id.
        if msg.get("username"):
            return msg["username"]
        if msg.get("user"):
            return self._resolve_user(msg["user"])
        return None

    def list_public_channels(self) -> list[dict]:
        channels, cursor = [], None
        while True:
            resp = self.client.conversations_list(
                types="public_channel", limit=200, cursor=cursor
            )
            channels.extend(resp["channels"])
            cursor = resp.get("response_metadata", {}).get("next_cursor") or None
            if not cursor:
                break
        self.audit.record("conversations.list", scope="public_channel",
                          detail=f"{len(channels)} channels")
        return channels

    def read_channel(self, channel_id: str, channel_name: str) -> list[MessageRecord]:
        """Full history of one public channel, threads expanded."""
        records: list[MessageRecord] = []
        cursor = None
        while True:
            resp = self.client.conversations_history(
                channel=channel_id, limit=200, cursor=cursor
            )
            for msg in resp["messages"]:
                if msg.get("subtype") not in (None, "bot_message"):
                    continue  # joins, topic changes, etc.
                author = self._author_of(msg)
                if not author:
                    continue
                is_parent = bool(msg.get("reply_count"))
                records.append(MessageRecord(
                    channel=channel_name,
                    author=author,
                    ts=msg["ts"],
                    text=msg.get("text", ""),
                    is_thread_parent=is_parent,
                    reply_count=msg.get("reply_count", 0),
                    mentions=_extract_mentions(msg.get("text", "")),
                ))
                if is_parent:
                    records.extend(self._read_thread(channel_id, channel_name, msg["ts"]))
            cursor = resp.get("response_metadata", {}).get("next_cursor") or None
            if not cursor:
                break
            time.sleep(0.5)
        self.audit.record("conversations.history", scope=f"#{channel_name}",
                          detail=f"{len(records)} messages")
        return records

    def _read_thread(self, channel_id: str, channel_name: str, parent_ts: str) -> list[MessageRecord]:
        records: list[MessageRecord] = []
        resp = self.client.conversations_replies(channel=channel_id, ts=parent_ts, limit=200)
        for msg in resp["messages"]:
            if msg["ts"] == parent_ts or msg.get("subtype") not in (None, "bot_message"):
                continue
            author = self._author_of(msg)
            if not author:
                continue
            records.append(MessageRecord(
                channel=channel_name,
                author=author,
                ts=msg["ts"],
                text=msg.get("text", ""),
                is_reply=True,
                mentions=_extract_mentions(msg.get("text", "")),
            ))
        return records

    def read_all(self) -> list[MessageRecord]:
        records: list[MessageRecord] = []
        for ch in self.list_public_channels():
            records.extend(self.read_channel(ch["id"], ch["name"]))
        return records


def _extract_mentions(text: str) -> list[str]:
    import re
    return re.findall(r"<@([A-Z0-9]+)(?:\|[^>]*)?>", text)
