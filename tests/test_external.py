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


def test_external_always_offered_when_directory_matches(tmp_path):
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
    assert strong["external"][0]["name"] == "Dr. Ingrid Vasquez"  # rides along

    none_at_all = query_experts("patent law", store=store)
    assert none_at_all["confidence"] == "none"
    assert none_at_all["external"][0]["name"] == "Rachel Goldman"

    no_match_anywhere = query_experts("quantum knitting", store=store)
    assert "external" not in no_match_anywhere  # empty directory match omitted


def test_directory_entries_link_out_only():
    """The boundary: directory provides booking links, never payment fields."""
    for e in match_external("gdpr data protection"):
        assert e["booking_url"].startswith("https://")
        assert "payment" not in json.dumps(e).lower()


def test_referral_attribution_on_booking_links():
    e = match_external("patent law")[0]
    assert "ref=collabfinder" in e["booking_url"]
    assert "q=patent+law" in e["booking_url"]


def test_only_verified_experts_offered(tmp_path):
    directory = tmp_path / "experts.json"
    directory.write_text(json.dumps({"experts": [
        {"name": "Pending Pat", "field": "gdpr", "credentials": "c",
         "rate": "$1/hr", "booking_url": "https://example.com/p",
         "status": "pending"},
        {"name": "Verified Vera", "field": "gdpr", "credentials": "c",
         "rate": "$1/hr", "booking_url": "https://example.com/v",
         "status": "verified", "verified_on": "2026-01-01",
         "commission_percent": 15},
    ]}), encoding="utf-8")
    names = [e["name"] for e in match_external("gdpr", path=directory)]
    assert names == ["Verified Vera"]
