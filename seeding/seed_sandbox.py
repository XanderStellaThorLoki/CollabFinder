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

Re-running --execute appends duplicate messages. For a clean slate, use a fresh
sandbox or delete/archive the channels first.
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
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        sys.exit("SLACK_BOT_TOKEN is not set. Export the sandbox bot token first.")
    return WebClient(token=token)


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


def post_plan(client: WebClient, plan: list[PlannedMessage], channel_ids: dict[str, str],
              personas: dict[str, dict]) -> None:
    thread_ts: dict[str, str] = {}  # thread_key -> parent message ts
    # Parents must post before their replies; the plan is already ordered that way.
    total = len(plan)
    for i, msg in enumerate(plan, 1):
        persona = personas[msg.author]
        kwargs = dict(
            channel=channel_ids[msg.channel],
            text=msg.text,
            username=persona["display_name"],
            icon_emoji=persona.get("icon_emoji", ":bust_in_silhouette:"),
        )
        if msg.is_reply and msg.thread_key:
            parent = thread_ts.get(msg.thread_key)
            if parent:
                kwargs["thread_ts"] = parent
        resp = client.chat_postMessage(**kwargs)
        if msg.thread_key and not msg.is_reply:
            thread_ts[msg.thread_key] = resp["ts"]
        if i % 25 == 0 or i == total:
            print(f"posted {i}/{total}")
        time.sleep(POST_INTERVAL_SECONDS)


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
