"""Marketplace mechanics: adjustable bids, demand signals, two-sided ratings.

The Outside Expert directory is a market, and markets need three feedback
loops this module provides:

  * Bids move.  Experts change their commission bid any time (10% floor).
    Fast-moving work pulls bids up; oversaturated categories push them down.
  * Demand is visible.  Every expertise query is logged (topic + timestamp,
    nothing else), so an expert signing up sees the recent volume of work
    for their field before choosing a bid.
  * Quality is scored.  When a deal closes, buyer and seller each rate the
    experience 1-5. Ratings show on expert cards and booking pages.

Local JSONL storage, same pattern as the audit log; swaps to Firestore via
the same env-var convention at launch.
"""

from __future__ import annotations

import datetime
import json
import os
from pathlib import Path

QUERY_LOG = Path(os.environ.get("COLLABFINDER_QUERY_LOG", "query_log.jsonl"))
RATINGS_LOG = Path(os.environ.get("COLLABFINDER_RATINGS_PATH", "ratings.jsonl"))

BID_FLOOR = 10
BID_CEILING = 50


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


# --- demand signal -----------------------------------------------------------

def log_query(topic: str, path: Path | None = None) -> None:
    row = {"at": _now().isoformat(), "topic": topic.lower()[:120]}
    with (path or QUERY_LOG).open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def demand(field: str, days: int = 30, path: Path | None = None) -> dict:
    """Recent query volume touching a field description. Shown to experts at
    signup so bids can price demand rationally."""
    terms = {t for t in field.lower().replace(",", " ").split() if len(t) > 1}
    cutoff = _now() - datetime.timedelta(days=days)
    count = 0
    p = path or QUERY_LOG
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if datetime.datetime.fromisoformat(row["at"]) < cutoff:
                continue
            if terms & set(row["topic"].split()):
                count += 1
    if count >= 20:
        level = "high — work in this field moves fast"
    elif count >= 5:
        level = "moderate"
    else:
        level = "low — this field is quiet or well covered"
    return {
        "field": field,
        "days": days,
        "queries": count,
        "message": (f"{count} expertise queries touched this field in the "
                    f"last {days} days. Demand: {level}."),
    }


# --- adjustable bids ---------------------------------------------------------

def update_bid(slug: str, percent: int, key: str,
               directory_path: Path | str | None = None) -> dict:
    """Expert self-serve bid change, authenticated by their bid_key.
    Effective immediately; clamped to the platform floor/ceiling."""
    from .external import DEFAULT_PATH
    p = Path(directory_path or os.environ.get("COLLABFINDER_EXPERTS_PATH", DEFAULT_PATH))
    data = json.loads(p.read_text(encoding="utf-8"))
    for expert in data["experts"]:
        if expert.get("slug") == slug:
            if expert.get("bid_key") != key:
                raise PermissionError("bid_key mismatch")
            expert["commission_percent"] = max(BID_FLOOR, min(BID_CEILING, int(percent)))
            p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            return {"slug": slug, "commission_percent": expert["commission_percent"]}
    raise KeyError(f"no expert with slug {slug}")


# --- two-sided ratings -------------------------------------------------------

def add_rating(expert_slug: str, stars: int, rater: str,
               booking_ref: str = "", path: Path | None = None) -> dict:
    """rater is 'buyer' (the workspace user) or 'seller' (the expert rating
    the engagement). Both sides rate at deal close."""
    if rater not in ("buyer", "seller"):
        raise ValueError("rater must be buyer or seller")
    stars = max(1, min(5, int(stars)))
    row = {"at": _now().isoformat(), "expert": expert_slug, "stars": stars,
           "rater": rater, "booking_ref": booking_ref}
    with (path or RATINGS_LOG).open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    return row


def avg_rating(expert_slug: str, path: Path | None = None) -> tuple[float, int]:
    p = path or RATINGS_LOG
    if not p.exists():
        return (0.0, 0)
    stars = [
        json.loads(line)["stars"]
        for line in p.read_text(encoding="utf-8").splitlines()
        if json.loads(line)["expert"] == expert_slug
    ]
    if not stars:
        return (0.0, 0)
    return (round(sum(stars) / len(stars), 1), len(stars))
