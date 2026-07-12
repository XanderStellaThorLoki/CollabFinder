"""Outside Experts: matching, gating, and the no-payment boundary."""

import json

from mcp_server.external import match_external
from mcp_server.ranking import query_experts
from profiles.builder import build_profiles
from profiles.store import ProfileStore
from privacy.optout import OptOutRegistry

NOW = 1_800_000_000.0


def test_matches_on_field_words():
    # Relevance first: Rachel matches both words (patent, law), Ingrid only
    # one (law) — Rachel places first despite Ingrid's higher bid.
    results = match_external("patent law question")
    names = [r["name"] for r in results]
    assert names == ["Rachel Goldman", "Dr. Ingrid Vasquez"]


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

    none_at_all = query_experts("trademark strategy", store=store)
    assert none_at_all["confidence"] == "none"
    assert none_at_all["external"][0]["name"] == "Rachel Goldman"

    no_match_anywhere = query_experts("quantum knitting", store=store)
    assert "external" not in no_match_anywhere  # empty directory match omitted


def test_booking_links_are_platform_hosted():
    """All booking flows through CollabFinder's own pages — that's where the
    platform takes its commission."""
    for e in match_external("gdpr data protection"):
        assert e["booking_url"].startswith("https://")
        assert "/book/" in e["booking_url"]
        assert e["commission_percent"] > 0


def test_booking_links_carry_query_attribution():
    e = match_external("trademark strategy")[0]
    assert "/book/rachel-goldman" in e["booking_url"]
    assert "q=trademark+strategy" in e["booking_url"]


def test_highest_commission_ranks_first(tmp_path):
    """Experts bid their commission; among matches, highest bid places first —
    but only matching experts appear at all."""
    directory = tmp_path / "experts.json"
    directory.write_text(json.dumps({"experts": [
        {"name": "Low Bid", "field": "gdpr", "credentials": "c", "rate": "$1/hr",
         "slug": "low", "status": "verified", "commission_percent": 10},
        {"name": "High Bid", "field": "gdpr", "credentials": "c", "rate": "$1/hr",
         "slug": "high", "status": "verified", "commission_percent": 30},
        {"name": "Rich Irrelevant", "field": "carpentry", "credentials": "c",
         "rate": "$1/hr", "slug": "rich", "status": "verified",
         "commission_percent": 90},
    ]}), encoding="utf-8")
    names = [e["name"] for e in match_external("gdpr", path=directory)]
    assert names == ["High Bid", "Low Bid"]  # commission order, no pay-to-enter


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
