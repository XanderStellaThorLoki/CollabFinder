"""Delete all bot-posted messages from the corpus channels.

The inverse of seed_sandbox: wipe + re-seed = clean reproducible demo.
Only touches messages this bot authored (Slack forbids deleting others'
messages anyway) and only in channels the corpus defines.

Usage:
    python -m seeding.wipe_sandbox            # dry run: count what would go
    python -m seeding.wipe_sandbox --execute  # actually delete
"""

from __future__ import annotations

import argparse
import os
import sys
import time

from .corpus_builder import CorpusBuilder

DELETE_INTERVAL_SECONDS = 1.1


def get_client():
    from slack_sdk import WebClient
    from slack_sdk.http_retry.builtin_handlers import RateLimitErrorRetryHandler
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        sys.exit("SLACK_BOT_TOKEN is not set.")
    client = WebClient(token=token)
    client.retry_handlers.append(RateLimitErrorRetryHandler(max_retry_count=10))
    return client


def collect_deletable(client, channel_id: str) -> list[str]:
    """All bot-message timestamps in a channel, replies before their parents
    (deleting a parent first would orphan its replies)."""
    parents_last: list[str] = []
    to_delete: list[str] = []
    cursor = None
    while True:
        resp = client.conversations_history(channel=channel_id, limit=200, cursor=cursor)
        for msg in resp["messages"]:
            if msg.get("subtype") not in (None, "bot_message"):
                continue
            if msg.get("reply_count"):
                replies = client.conversations_replies(channel=channel_id, ts=msg["ts"], limit=200)
                to_delete.extend(
                    m["ts"] for m in replies["messages"]
                    if m["ts"] != msg["ts"] and m.get("subtype") in (None, "bot_message")
                )
            parents_last.append(msg["ts"])
        cursor = resp.get("response_metadata", {}).get("next_cursor") or None
        if not cursor:
            break
    return to_delete + parents_last


def main() -> None:
    parser = argparse.ArgumentParser(description="Wipe bot messages from corpus channels.")
    parser.add_argument("--execute", action="store_true",
                        help="Delete. Without this flag, counts and exits.")
    args = parser.parse_args()

    client = get_client()
    builder = CorpusBuilder()

    channels = {}
    cursor = None
    while True:
        resp = client.conversations_list(types="public_channel", limit=200, cursor=cursor)
        for ch in resp["channels"]:
            channels[ch["name"]] = ch["id"]
        cursor = resp.get("response_metadata", {}).get("next_cursor") or None
        if not cursor:
            break

    total = 0
    for name in builder.channels:
        cid = channels.get(name)
        if not cid:
            continue
        try:
            client.conversations_join(channel=cid)
        except Exception:
            pass
        targets = collect_deletable(client, cid)
        total += len(targets)
        print(f"#{name}: {len(targets)} bot messages", flush=True)
        if args.execute:
            for ts in targets:
                client.chat_delete(channel=cid, ts=ts)
                time.sleep(DELETE_INTERVAL_SECONDS)
            print(f"#{name}: wiped", flush=True)

    if not args.execute:
        print(f"\nDry run: {total} messages would be deleted. Re-run with --execute.")
    else:
        print(f"done: deleted {total} messages", flush=True)


if __name__ == "__main__":
    main()
