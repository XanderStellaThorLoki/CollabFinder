"""Outside Experts: matching, gating, and the no-payment boundary."""

import json

from mcp_server.external import match_external
from mcp_server.ranking import query_experts
from profiles.builder import build_profiles
from profiles.store import ProfileStore
from privacy.optout import OptOutRegistry

NOW = 1_800_000_000.0


def test_matches_on_field_words():
    results = match_external("patent law question")
    assert results and results[0]["name"] == "Rachel Goldman"


def test_no_match_returns_empty():
    assert match_external("quantum knitting") == []


def test_external_only_offered_when_internal_signal_weak(tmp_path):
    signals = [
        {"author": "Sarah Okafor", "topics": ["gdpr", "gdpr compliance"],
         "ts": str(NOW), "channel": "legal-compliance",
         "is_thread_parent": True, "reply_count": 4, "text": "New GDPR guidance."}
    ] * 3
    store = ProfileStore(path=tmp_path / "profiles.json",
                         optout=OptOutRegistry(path=tmp_path / "optouts.json"))
    store.save_all(build_profiles(signals, now=NOW))

    strong = query_experts("gdpr", store=store)
    assert strong["confidence"] == "high"
    assert "external" not in strong  # internal expert exists; no upsell

    none_at_all = query_experts("patent law", store=store)
    assert none_at_all["confidence"] == "none"
    assert none_at_all["external"][0]["name"] == "Rachel Goldman"


def test_directory_entries_link_out_only():
    """The boundary: directory provides booking links, never payment fields."""
    for e in match_external("gdpr data protection"):
        assert e["booking_url"].startswith("https://")
        assert "payment" not in json.dumps(e).lower()
