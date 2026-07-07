"""Create or update the plain-English transparency Canvas.

The Canvas is the "Read more" behind the banner and /collab privacy — the
full data policy in language a non-lawyer can read in two minutes.

Usage:
    python -m privacy.canvas            # create (prints canvas URL)
"""

from __future__ import annotations

import os
import sys

from slack_sdk import WebClient

CANVAS_TITLE = "CollabFinder — What it knows and why"

CANVAS_MARKDOWN = """# CollabFinder — What it knows and why

CollabFinder answers one question: *"Who should I talk to about X?"*
This page explains exactly what it reads, stores, and shows. It is written
for humans, not lawyers.

## What it reads
* **Public channels** — messages, threads, and reactions in channels anyone
  in this workspace can join.
* **@mentions** — when someone tags you in a public message.
* **Nothing else.** No DMs, no group DMs, no private channels. The bot's
  Slack permissions (`search:read.public`, `channels:history`) make wider
  reading impossible — it lacks the key, not just the policy.

## What it builds
A per-person topic map: which subjects you post about publicly, weighted
toward threads you start and questions you answer. Talking a lot does not
make you an expert; being answered and being asked does.

## What it shows others
* Your name, a confidence level, and a one-line *why* (e.g. "authored 3
  threads in #legal-compliance in the past 60 days").
* **Never message quotes.** Suggestions cite patterns, not content.

## How long it keeps things
Topic signals fade with a 90-day half-life. If you stop discussing a topic,
CollabFinder stops recommending you for it — automatically.

## The banner rule
If a channel is under any expanded monitoring (an org-level decision), a
banner is pinned in that channel — always. **If there is no banner, the
channel is not monitored.** Like a webcam light: no light, no camera.

## Opting out
Type `/collab opt-out` anywhere. Effective immediately: your profile is
deleted and your messages are skipped from then on. `/collab opt-in`
reverses it. Nobody is notified either way.

## Auditability
Every read the indexer performs is logged (what was read, when, under which
scope). Ask a workspace admin to see the audit log.
"""


def main() -> None:
    client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN") or sys.exit("SLACK_BOT_TOKEN not set"))
    resp = client.api_call(
        "canvases.create",
        json={
            "title": CANVAS_TITLE,
            "document_content": {"type": "markdown", "markdown": CANVAS_MARKDOWN},
        },
    )
    canvas_id = resp["canvas_id"]
    print(f"canvas created: {canvas_id}")
    print("Set COLLABFINDER_CANVAS_URL to the canvas link so /collab privacy can point at it.")


if __name__ == "__main__":
    main()
