"""Profile storage with opt-out enforcement at read time.

Local JSON by default (zero-setup, powers the demo); Firestore when
COLLABFINDER_FIRESTORE_COLLECTION is set. Both backends apply the same rule:
opted-out users are filtered out of every read — they can never appear in
results regardless of what upstream wrote.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from privacy.optout import OptOutRegistry

DEFAULT_PATH = Path("profiles.json")


class ProfileStore:
    def __init__(self, path: Path | str | None = None,
                 optout: OptOutRegistry | None = None):
        self.path = Path(path or os.environ.get("COLLABFINDER_PROFILES_PATH", DEFAULT_PATH))
        self.optout = optout or OptOutRegistry()
        self.fs_collection = os.environ.get("COLLABFINDER_FIRESTORE_COLLECTION")
        self._fs = None
        if self.fs_collection:
            try:
                from google.cloud import firestore
                self._fs = firestore.Client()
            except Exception:
                self._fs = None  # local file remains authoritative

    def save_all(self, profiles: dict[str, dict]) -> None:
        # Opt-out is enforced at ingest too: never even store an excluded profile.
        kept = {a: p for a, p in profiles.items() if not self.optout.is_opted_out(a)}
        self.path.write_text(json.dumps(kept, indent=2), encoding="utf-8")
        if self._fs:
            try:
                coll = self._fs.collection(self.fs_collection)
                for author, profile in kept.items():
                    coll.document(author.replace("/", "_")).set(profile)
            except Exception:
                pass

    def load_all(self) -> dict[str, dict]:
        if not self.path.exists():
            return {}
        profiles = json.loads(self.path.read_text(encoding="utf-8"))
        return {
            a: p for a, p in profiles.items()
            if not self.optout.is_opted_out(a)
        }

    def describe(self) -> str:
        backend = f"local:{self.path}"
        if self._fs:
            backend += f" + firestore:{self.fs_collection}"
        return backend
