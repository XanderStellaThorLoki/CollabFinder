"""Rank profiles for a topic query and explain the result.

Confidence is honest by construction:
    high    - clear leader with strong absolute evidence
    medium  - real signal but a close field or thin evidence
    low     - weak signal; the answer says so instead of faking certainty
"""

from __future__ import annotations

from profiles.store import ProfileStore

from .external import match_external


def _match_score(profile: dict, query_terms: list[str]) -> tuple[float, list[str]]:
    """Sum scores of profile topics sharing a whole word with the query, so
    'gdpr' matches 'gdpr compliance' but 'access' does NOT match
    'accessibility' (substring matching proved too loose in practice)."""
    terms = set(query_terms)
    score = 0.0
    matched: list[str] = []
    for topic, s in profile["topics"].items():
        if terms & set(topic.split()):
            score += s
            matched.append(topic)
    return score, matched


def _evidence_for(profile: dict, matched_topics: list[str]) -> dict:
    """Evidence from the single strongest matched topic. Matched topics overlap
    (one message about "gdpr compliance" matches both "gdpr" and "gdpr
    compliance"), so summing across them double-counts the same messages and
    produces reasons that overstate reality."""
    empty = {"thread_parents": 0, "questions_asked": 0, "replies_given": 0,
             "messages": 0, "replies_received": 0, "channels": {}}
    best = max(
        (t for t in matched_topics if t in profile["evidence"]),
        key=lambda t: profile["topics"].get(t, 0.0),
        default=None,
    )
    return profile["evidence"][best] if best else empty


def _reason(evidence: dict) -> str:
    parts = []
    if evidence["thread_parents"]:
        parts.append(f"authored {evidence['thread_parents']} thread(s)")
    if evidence["replies_given"]:
        parts.append(f"answered {evidence['replies_given']} question(s)")
    if evidence["replies_received"]:
        parts.append(f"drew {evidence['replies_received']} replies")
    if not parts and evidence.get("questions_asked"):
        # Interest, not expertise — say exactly that.
        parts.append(f"asked about this {evidence['questions_asked']} time(s)")
    top_channels = sorted(evidence["channels"], key=evidence["channels"].get, reverse=True)[:2]
    where = " in " + ", ".join(f"#{c}" for c in top_channels) if top_channels else ""
    return (", ".join(parts) or f"{evidence['messages']} relevant message(s)") + where


def _confidence(scores: list[float], evidence: dict) -> str:
    if not scores or scores[0] <= 0:
        return "none"
    # Asker-only evidence is interest, never authority.
    if not (evidence["thread_parents"] or evidence["replies_given"]):
        return "low"
    strong_evidence = (
        evidence["thread_parents"] >= 2
        or evidence["replies_given"] >= 3
        # One authored thread that the community engaged with is corroborated
        # authority, not a lone data point.
        or (evidence["thread_parents"] >= 1 and evidence["replies_received"] >= 3)
    )
    clear_lead = len(scores) == 1 or scores[0] >= 1.5 * scores[1]
    if strong_evidence and clear_lead:
        return "high"
    if strong_evidence or clear_lead:
        return "medium"
    return "low"


def query_experts(topic: str, limit: int = 3, store: ProfileStore | None = None) -> dict:
    from .marketplace import log_query
    try:
        log_query(topic)  # demand signal for the expert marketplace
    except Exception:
        pass
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
    payload = {"query": topic, "confidence": overall, "results": results}

    # Outside Experts always ride along when the org's curated directory has
    # a match — internal colleagues rank first, but the paid option is
    # always visible.
    external = match_external(topic)
    if external:
        payload["external"] = external
    return payload
