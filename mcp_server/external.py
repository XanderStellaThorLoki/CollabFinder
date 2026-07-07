"""Outside Expert directory — paid consultation as the graceful fallback.

When the org has no strong internal signal for a topic, the answer shouldn't
dead-end. The org curates a vetted directory of external consultants
(config/external_experts.json); matches are offered alongside the honest
"no clear internal signal" message.

Boundaries, by design:
  * Org-controlled: entries come from the directory file, never the open web.
  * CollabFinder links to the expert's own booking page. Payment never
    flows through CollabFinder.
  * Offered only when internal confidence is low or none — the tool's first
    job is connecting colleagues, not selling consults.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

DEFAULT_PATH = Path(__file__).parent.parent / "config" / "external_experts.json"


def _load_directory(path: Path | str | None = None) -> list[dict]:
    p = Path(path or os.environ.get("COLLABFINDER_EXPERTS_PATH", DEFAULT_PATH))
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8")).get("experts", [])


def match_external(topic: str, limit: int = 2, path: Path | str | None = None) -> list[dict]:
    """Whole-word match of query terms against each expert's field tags."""
    terms = {t for t in topic.lower().replace(",", " ").split() if len(t) > 1}
    results = []
    for expert in _load_directory(path):
        field_words = set(expert["field"].lower().replace(",", " ").split())
        overlap = terms & field_words
        if overlap:
            results.append({**expert, "matched_on": sorted(overlap)})
    results.sort(key=lambda e: len(e["matched_on"]), reverse=True)
    return results[:limit]
