"""Marketplace mechanics: bid tie-breaking, self-serve bids, demand, ratings."""

import json

import pytest

from mcp_server.external import match_external
from mcp_server.marketplace import add_rating, avg_rating, demand, log_query, update_bid


def _dir(tmp_path, experts):
    p = tmp_path / "experts.json"
    p.write_text(json.dumps({"experts": experts}), encoding="utf-8")
    return p


def _expert(name, field, commission, **kw):
    return {"name": name, "slug": name.lower().replace(" ", "-"), "field": field,
            "credentials": "c", "rate": "$1/hr", "status": "verified",
            "commission_percent": commission, "bid_key": f"key-{name}", **kw}


def test_relevance_ranks_bid_breaks_ties(tmp_path):
    directory = _dir(tmp_path, [
        _expert("Weak Match High Bid", "gdpr", 40),
        _expert("Strong Match Low Bid", "gdpr compliance audits", 10),
        _expert("Equal Match Higher Bid", "gdpr audits", 30),
    ])
    names = [e["name"] for e in match_external("gdpr audits", limit=3, path=directory)]
    # two-word matches first; among them bid decides; one-word match last
    assert names == ["Equal Match Higher Bid", "Strong Match Low Bid",
                     "Weak Match High Bid"]


def test_update_bid_with_key_and_clamp(tmp_path):
    directory = _dir(tmp_path, [_expert("Ana", "gdpr", 15)])
    result = update_bid("ana", 60, "key-Ana", directory_path=directory)
    assert result["commission_percent"] == 50  # ceiling clamp
    result = update_bid("ana", 3, "key-Ana", directory_path=directory)
    assert result["commission_percent"] == 10  # floor clamp
    with pytest.raises(PermissionError):
        update_bid("ana", 20, "wrong-key", directory_path=directory)


def test_demand_counts_recent_queries(tmp_path):
    log = tmp_path / "queries.jsonl"
    for _ in range(6):
        log_query("gdpr compliance", path=log)
    log_query("kubernetes", path=log)
    d = demand("GDPR, data protection law", path=log)
    assert d["queries"] == 6
    assert "moderate" in d["message"]
    quiet = demand("carpentry", path=log)
    assert quiet["queries"] == 0
    assert "quiet" in quiet["message"]


def test_two_sided_ratings(tmp_path):
    log = tmp_path / "ratings.jsonl"
    add_rating("ana", 5, "buyer", path=log)
    add_rating("ana", 4, "seller", path=log)
    add_rating("ana", 9, "buyer", path=log)  # clamped to 5
    avg, count = avg_rating("ana", path=log)
    assert (avg, count) == (4.7, 3)
    with pytest.raises(ValueError):
        add_rating("ana", 5, "bystander", path=log)
