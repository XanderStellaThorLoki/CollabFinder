"""Per-user opt-out registry.

One rule, enforced in two places: an opted-out user is excluded at ingest
(ProfileStore.save_all never stores them) and at query (ProfileStore.load_all
never returns them). Local JSON file keyed by display name / handle.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

DEFAULT_PATH = Path("optouts.json")


class OptOutRegistry:
    def __init__(self, path: Path | str | None = None):
        self.path = Path(path or os.environ.get("COLLABFINDER_OPTOUT_PATH", DEFAULT_PATH))

    def _load(self) -> set[str]:
        if not self.path.exists():
            return set()
        return set(json.loads(self.path.read_text(encoding="utf-8")))

    def _save(self, entries: set[str]) -> None:
        self.path.write_text(json.dumps(sorted(entries), indent=2), encoding="utf-8")

    def opt_out(self, user: str) -> None:
        entries = self._load()
        entries.add(user.lower())
        self._save(entries)

    def opt_in(self, user: str) -> None:
        entries = self._load()
        entries.discard(user.lower())
        self._save(entries)

    def is_opted_out(self, user: str) -> bool:
        return user.lower() in self._load()
