"""Seed the Slack developer sandbox with demo data.

Usage:
    python -m seeding.seed_sandbox            # dry run: print the plan summary
    python -m seeding.seed_sandbox --execute  # actually post to Slack

Requires:
    SLACK_BOT_TOKEN env var (xoxb-...) with scopes:
        chat:write            post messages
        chat:write.customize  post with per-persona username + icon
        channels:manage       create channels
        channels:read         find existing channels
        channels:join         join channels before posting

Attribution model: the sandbox has one bot user, so personas are simulated with
chat.postMessage username/icon_emoji overrides. Messages carry the persona's
display name in the `username` field — the indexer attributes by that field for
bot-authored messages. (Slack does not allow backdating, so all seeded messages
share ~one timestamp; recency-decay behaviour is covered by unit tests instead
of demo data.)

Re-running --execute is safe: existing messages are read back first and
already-posted plan entries are skipped, so an interrupted run resumes where
it stopped instead of duplicating.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

from .corpus_builder import CorpusBuilder, PlannedMessage

POST_INTERVAL_SECONDS = 1.1  # stay under chat.postMessage rate limits


def get_client():
    from slack_sdk import WebClient  # imported here so dry runs don't need slack_sdk
    from slack_sdk.http_retry.builtin_handlers import RateLimitErrorRetryHandler
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        sys.exit("SLACK_BOT_TOKEN is not set. Export the sandbox bot token first.")
    client = WebClient(token=token)
    client.retry_handlers.append(RateLimitErrorRetryHandler(max_retry_count=10))
    return client


def ensure_channels(client, names: list[str]) -> dict[str, str]:
    """Create (or find) each public channel; join it; return name -> channel id."""
    from slack_sdk.errors import SlackApiError

    existing: dict[str, str] = {}
    cursor = None
    while True:
        resp = client.conversations_list(types="public_channel", limit=200, cursor=cursor)
        for ch in resp["channels"]:
            existing[ch["name"]] = ch["id"]
        cursor = resp.get("response_metadata", {}).get("next_cursor") or None
        if not cursor:
            break

    ids: dict[str, str] = {}
    for name in names:
        if name in existing:
            ids[name] = existing[name]
        else:
            resp = client.conversations_create(name=name)
            ids[name] = resp["channel"]["id"]
            print(f"created #{name}")
        try:
            client.conversations_join(channel=ids[name])
        except SlackApiError as e:
            if e.response["error"] != "already_in_channel":
                raise
    return ids


def _fetch_existing(client, channel_id: str):
    """Read back what's already in a channel so re-runs post only the missing.

    Returns (top_level, replies):
        top_level: {text: deque of ts, oldest first} for non-reply messages
        replies:   {parent_ts: {text: count}} for thread replies
    """
    from collections import defaultdict, deque

    history = []
    cursor = None
    while True:
        resp = client.conversations_history(channel=channel_id, limit=200, cursor=cursor)
        history.extend(resp["messages"])
        cursor = resp.get("response_metadata", {}).get("next_cursor") or None
        if not cursor:
            break
    top_level = defaultdict(deque)
    replies = defaultdict(lambda: defaultdict(int))
    for msg in reversed(history):  # oldest first, matching plan order
        if msg.get("subtype") not in (None, "bot_message"):
            continue
        top_level[msg.get("text", "")].append(msg["ts"])
        if msg.get("reply_count"):
            resp = client.conversations_replies(channel=channel_id, ts=msg["ts"], limit=200)
            for reply in resp["messages"]:
                if reply["ts"] == msg["ts"] or reply.get("subtype") not in (None, "bot_message"):
                    continue
                replies[msg["ts"]][reply.get("text", "")] += 1
    return top_level, replies


def post_plan(client, plan: list[PlannedMessage], channel_ids: dict[str, str],
              personas: dict[str, dict]) -> None:
    thread_ts: dict[str, str] = {}   # thread_key -> parent message ts
    existing: dict[str, tuple] = {}  # channel -> (top_level, replies), fetched lazily
    total, posted, skipped = len(plan), 0, 0

    # Parents must post before their replies; the plan is already ordered that way.
    for i, msg in enumerate(plan, 1):
        if msg.channel not in existing:
            existing[msg.channel] = _fetch_existing(client, channel_ids[msg.channel])
        top_level, replies = existing[msg.channel]

        if not msg.is_reply:
            if top_level.get(msg.text):
                ts = top_level[msg.text].popleft()  # already posted — reuse its ts
                if msg.thread_key:
                    thread_ts[msg.thread_key] = ts
                skipped += 1
                continue
        else:
            parent = thread_ts.get(msg.thread_key or "")
            if parent and replies.get(parent, {}).get(msg.text, 0) > 0:
                replies[parent][msg.text] -= 1
                skipped += 1
                continue

        persona = personas[msg.author]
        kwargs = dict(
            channel=channel_ids[msg.channel],
            text=msg.text,
            username=persona["display_name"],
            icon_emoji=persona.get("icon_emoji", ":bust_in_silhouette:"),
        )
        if msg.is_reply and msg.thread_key and thread_ts.get(msg.thread_key):
            kwargs["thread_ts"] = thread_ts[msg.thread_key]
        resp = client.chat_postMessage(**kwargs)
        posted += 1
        if msg.thread_key and not msg.is_reply:
            thread_ts[msg.thread_key] = resp["ts"]
        if i % 25 == 0 or i == total:
            print(f"progress {i}/{total} (posted {posted}, skipped {skipped})", flush=True)
        time.sleep(POST_INTERVAL_SECONDS)
    print(f"done: posted {posted}, skipped {skipped} already-present", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the Slack sandbox with demo data.")
    parser.add_argument("--execute", action="store_true",
                        help="Post to Slack. Without this flag, prints the plan and exits.")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed (default 42).")
    args = parser.parse_args()

    builder = CorpusBuilder(seed=args.seed)
    plan = builder.build()
    print(builder.summarize(plan))

    if not args.execute:
        print("\nDry run. Re-run with --execute to post to Slack.")
        return

    client = get_client()
    channel_ids = ensure_channels(client, builder.channels)
    est_minutes = len(plan) * POST_INTERVAL_SECONDS / 60
    print(f"\nPosting {len(plan)} messages (~{est_minutes:.0f} min at rate limit)...")
    post_plan(client, plan, channel_ids, builder.personas)
    print("Done. Sandbox is seeded.")


if __name__ == "__main__":
    main()
