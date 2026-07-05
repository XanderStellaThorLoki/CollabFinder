"""Build per-person expertise profiles from topic signals.

Weighting model (the part the README formula describes):

    w_i(topic) = sum over messages of  base_weight * e^(-lambda * age_days)

base_weight encodes that contribution depth beats volume:
    thread parent authored:   3.0  (+0.5 per reply received, capped at +2.5)
    reply given in a thread:  2.0  (answering is expertise signal)
    standalone message:       1.0
Being mentioned in a message about a topic credits the mentioned user 1.0 —
people point at experts.

Recency half-life defaults to 90 days (lambda = ln(2)/90). All seeded sandbox
messages share ~one timestamp, so decay is uniform there; the math is covered
by unit tests instead of demo data.
"""

from __future__ import annotations

import math
import time
from collections import defaultdict

DEFAULT_HALF_LIFE_DAYS = 90.0

W_THREAD_PARENT = 3.0
W_REPLY_RECEIVED = 0.5      # per reply to your thread
W_REPLY_RECEIVED_CAP = 2.5
W_REPLY_GIVEN = 2.0
W_STANDALONE = 1.0
W_MENTIONED = 1.0


def _decay(age_days: float, half_life_days: float) -> float:
    lam = math.log(2) / half_life_days
    return math.exp(-lam * max(age_days, 0.0))


def build_profiles(
    signals: list[dict],
    half_life_days: float = DEFAULT_HALF_LIFE_DAYS,
    now: float | None = None,
) -> dict[str, dict]:
    """signals: message records with 'topics' attached (see indexer.run).

    Returns {author: {"topics": {topic: score}, "evidence": {topic: {...}}}}.
    Evidence powers the reasoning strings in ranking: per topic we track
    thread parents authored, replies given, total messages, channels, and
    replies received.
    """
    now = now or time.time()
    profiles: dict[str, dict] = defaultdict(
        lambda: {"topics": defaultdict(float), "evidence": defaultdict(
            lambda: {"thread_parents": 0, "replies_given": 0, "messages": 0,
                     "replies_received": 0, "channels": defaultdict(int)}
        )}
    )

    for sig in signals:
        author = sig["author"]
        age_days = (now - float(sig["ts"])) / 86400.0
        decay = _decay(age_days, half_life_days)

        if sig.get("is_thread_parent"):
            base = W_THREAD_PARENT + min(
                sig.get("reply_count", 0) * W_REPLY_RECEIVED, W_REPLY_RECEIVED_CAP
            )
        elif sig.get("is_reply"):
            base = W_REPLY_GIVEN
        else:
            base = W_STANDALONE

        prof = profiles[author]
        for topic in set(sig.get("topics", [])):
            prof["topics"][topic] += base * decay
            ev = prof["evidence"][topic]
            ev["messages"] += 1
            ev["channels"][sig["channel"]] += 1
            if sig.get("is_thread_parent"):
                ev["thread_parents"] += 1
                ev["replies_received"] += sig.get("reply_count", 0)
            elif sig.get("is_reply"):
                ev["replies_given"] += 1

    # defaultdicts -> plain dicts for storage
    return {
        author: {
            "topics": dict(p["topics"]),
            "evidence": {
                t: {**ev, "channels": dict(ev["channels"])}
                for t, ev in p["evidence"].items()
            },
        }
        for author, p in profiles.items()
    }
