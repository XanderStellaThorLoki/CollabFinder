"""Post and pin the transparency banner — the webcam light.

Used when org-level expanded monitoring is enabled for a channel. The rule it
enforces: no monitoring without a visible, pinned, ambient indicator.

Usage:
    python -m slack_app.banner post <channel-name>     # post + pin
    python -m slack_app.banner remove <channel-name>   # unpin + delete
"""

from __future__ import annotations

import os
import sys

from slack_sdk import WebClient

from . import blocks


def _find_channel(client: WebClient, name: str) -> str:
    cursor = None
    while True:
        resp = client.conversations_list(types="public_channel", limit=200, cursor=cursor)
        for ch in resp["channels"]:
            if ch["name"] == name.lstrip("#"):
                return ch["id"]
        cursor = resp.get("response_metadata", {}).get("next_cursor") or None
        if not cursor:
            sys.exit(f"channel not found: {name}")


def post_banner(client: WebClient, channel_name: str) -> str:
    channel_id = _find_channel(client, channel_name)
    client.conversations_join(channel=channel_id)
    resp = client.chat_postMessage(
        channel=channel_id,
        text="This channel is AI-monitored for collaboration suggestions.",
        blocks=blocks.transparency_banner(),
    )
    client.pins_add(channel=channel_id, timestamp=resp["ts"])
    return resp["ts"]


def remove_banner(client: WebClient, channel_name: str) -> int:
    """Unpin and delete every banner message the bot posted in the channel."""
    channel_id = _find_channel(client, channel_name)
    removed = 0
    pins = client.pins_list(channel=channel_id)
    for item in pins.get("items", []):
        msg = item.get("message", {})
        if "AI-monitored" in msg.get("text", ""):
            client.pins_remove(channel=channel_id, timestamp=msg["ts"])
            client.chat_delete(channel=channel_id, ts=msg["ts"])
            removed += 1
    return removed


def main() -> None:
    if len(sys.argv) != 3 or sys.argv[1] not in ("post", "remove"):
        sys.exit(__doc__)
    client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
    action, channel = sys.argv[1], sys.argv[2]
    if action == "post":
        ts = post_banner(client, channel)
        print(f"banner pinned in #{channel.lstrip('#')} (ts {ts})")
    else:
        n = remove_banner(client, channel)
        print(f"removed {n} banner(s) from #{channel.lstrip('#')}")


if __name__ == "__main__":
    main()
