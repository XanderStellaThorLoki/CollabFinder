"""Rank profiles for a topic query and explain the result.

Confidence is honest by construction:
    high    - clear leader with strong absolute evidence
    medium  - real signal but a close field or thin evidence
    low     - weak signal; the answer says so instead of faking certainty
"""

from __future__ import annotations

from profiles.store import ProfileStore


def _match_score(profile: dict, query_terms: list[str]) -> tuple[float, list[str]]:
    """Sum scores of profile topics that match any query term (substring match
    both directions, so 'gdpr' hits 'gdpr compliance' and vice versa)."""
    score = 0.0
    matched: list[str] = []
    for topic, s in profile["topics"].items():
        for term in query_terms:
            if term in topic or topic in term:
                score += s
                matched.append(topic)
                break
    return score, matched


def _evidence_for(profile: dict, matched_topics: list[str]) -> dict:
    totals = {"thread_parents": 0, "replies_given": 0, "messages": 0,
              "replies_received": 0, "channels": {}}
    for t in matched_topics:
        ev = profile["evidence"].get(t)
        if not ev:
            continue
        for k in ("thread_parents", "replies_given", "messages", "replies_received"):
            totals[k] += ev[k]
        for ch, n in ev["channels"].items():
            totals["channels"][ch] = totals["channels"].get(ch, 0) + n
    return totals


def _reason(evidence: dict) -> str:
    parts = []
    if evidence["thread_parents"]:
        parts.append(f"authored {evidence['thread_parents']} thread(s)")
    if evidence["replies_given"]:
        parts.append(f"answered {evidence['replies_given']} question(s)")
    if evidence["replies_received"]:
        parts.append(f"drew {evidence['replies_received']} replies")
    top_channels = sorted(evidence["channels"], key=evidence["channels"].get, reverse=True)[:2]
    where = " in " + ", ".join(f"#{c}" for c in top_channels) if top_channels else ""
    return (", ".join(parts) or f"{evidence['messages']} relevant message(s)") + where


def _confidence(scores: list[float], evidence: dict) -> str:
    if not scores or scores[0] <= 0:
        return "none"
    strong_evidence = evidence["thread_parents"] >= 2 or evidence["replies_given"] >= 3
    clear_lead = len(scores) == 1 or scores[0] >= 1.5 * scores[1]
    if strong_evidence and clear_lead:
        return "high"
    if strong_evidence or clear_lead:
        return "medium"
    return "low"


def query_experts(topic: str, limit: int = 3, store: ProfileStore | None = None) -> dict:
    store = store or ProfileStore()
    profiles = store.load_all()
    query_terms = [t for t in topic.lower().split() if len(t) > 1]

    scored = []
    for author, profile in profiles.items():
        score, matched = _match_score(profile, query_terms)
        if score > 0:
            scored.append((score, author, matched))
    scored.sort(reverse=True)

    results = []
    top_scores = [s for s, _, _ in scored]
    for score, author, matched in scored[:limit]:
        ev = _evidence_for(profiles[author], matched)
        results.append({
            "name": author,
            "score": round(score, 2),
            "reason": _reason(ev),
            "confidence": _confidence([score] + top_scores[len(results) + 1:], ev),
        })

    overall = results[0]["confidence"] if results else "none"
    return {"query": topic, "confidence": overall, "results": results}
