"""Index the workspace: read Slack -> extract topics -> build profiles -> store.

Usage:
    python -m indexer.run                # index and write profiles
    python -m indexer.run --dump-signals # also dump raw signal records (debug)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .slack_reader import SlackReader
from .topic_extractor import extract_topics
from profiles.builder import build_profiles
from profiles.store import ProfileStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Index Slack activity into expertise profiles.")
    parser.add_argument("--dump-signals", action="store_true",
                        help="Write raw message records to signals.json for debugging.")
    args = parser.parse_args()

    reader = SlackReader()
    records = reader.read_all()
    print(f"read {len(records)} messages from public channels")

    if args.dump_signals:
        Path("signals.json").write_text(
            json.dumps([r.to_dict() for r in records], indent=2), encoding="utf-8"
        )
        print("wrote signals.json")

    signals = [
        {**r.to_dict(), "topics": extract_topics(r.text)}
        for r in records
    ]

    profiles = build_profiles(signals)
    store = ProfileStore()
    store.save_all(profiles)
    print(f"stored {len(profiles)} profiles -> {store.describe()}")


if __name__ == "__main__":
    main()
