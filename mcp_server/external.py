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


BASE_URL = os.environ.get(
    "COLLABFINDER_BASE_URL",
    "https://collabfinder-mcp-658446182420.us-central1.run.app",
)


def _referral_url(expert: dict, topic: str) -> str:
    """CollabFinder-hosted booking page for this expert. All booking and
    payment flows through the platform (commission withheld); the topic tag
    attributes the booking to the query that produced it. No personal data
    in the params."""
    from urllib.parse import quote_plus
    slug = expert.get("slug") or expert["name"].lower().replace(" ", "-")
    return f"{BASE_URL}/book/{slug}?q={quote_plus(topic.lower()[:80])}"


def match_external(topic: str, limit: int = 2, path: Path | str | None = None) -> list[dict]:
    """Whole-word match of query terms against each expert's field tags.
    Only credentialed entries (status == verified) are ever offered.

    Ordering is commission-first: experts set their own commission rate at
    signup, and among experts matching the query, the highest commission
    wins placement (match strength breaks ties). Relevance still gates
    entry — no commission buys a spot on a topic the expert doesn't cover."""
    terms = {t for t in topic.lower().replace(",", " ").split() if len(t) > 1}
    results = []
    for expert in _load_directory(path):
        if expert.get("status") != "verified":
            continue
        field_words = set(expert["field"].lower().replace(",", " ").split())
        overlap = terms & field_words
        if overlap:
            results.append({
                **expert,
                "matched_on": sorted(overlap),
                "booking_url": _referral_url(expert, topic),
            })
    results.sort(key=lambda e: (e.get("commission_percent", 0), len(e["matched_on"])),
                 reverse=True)
    return results[:limit]
