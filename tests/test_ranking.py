"""Ranking: reasoning strings, confidence honesty, and opt-out at query time."""

from mcp_server.ranking import query_experts
from profiles.builder import build_profiles
from profiles.store import ProfileStore
from privacy.optout import OptOutRegistry

NOW = 1_800_000_000.0


def _sig(author, topics, **kw):
    return {"author": author, "topics": topics, "ts": str(NOW), "channel": kw.pop("channel", "legal-compliance"), **kw}


def _seeded_store(tmp_path, optout=None):
    signals = (
        # Sarah: 3 threads with replies + 2 answers on gdpr
        [_sig("Sarah Okafor", ["gdpr", "gdpr compliance"], is_thread_parent=True, reply_count=4) for _ in range(3)]
        + [_sig("Sarah Okafor", ["gdpr"], is_reply=True) for _ in range(2)]
        # Chris: 6 standalone mentions of gdpr (volume, no depth)
        + [_sig("Chris Taylor", ["gdpr"], channel="general") for _ in range(6)]
        # Tom: one reply
        + [_sig("Tom Hardwick", ["gdpr"], is_reply=True)]
    )
    store = ProfileStore(path=tmp_path / "profiles.json",
                         optout=optout or OptOutRegistry(path=tmp_path / "optouts.json"))
    store.save_all(build_profiles(signals, now=NOW))
    return store


def test_expert_outranks_volume(tmp_path):
    result = query_experts("gdpr", store=_seeded_store(tmp_path))
    names = [r["name"] for r in result["results"]]
    assert names[0] == "Sarah Okafor"
    assert result["results"][0]["confidence"] == "high"


def test_reason_mentions_threads_and_channel(tmp_path):
    result = query_experts("gdpr", store=_seeded_store(tmp_path))
    reason = result["results"][0]["reason"]
    assert "thread" in reason
    assert "#legal-compliance" in reason


def test_unknown_topic_returns_empty_with_no_fake_confidence(tmp_path):
    result = query_experts("quantum knitting", store=_seeded_store(tmp_path))
    assert result["results"] == []
    assert result["confidence"] == "none"


def test_opted_out_user_absent_from_results(tmp_path):
    optout = OptOutRegistry(path=tmp_path / "optouts.json")
    store = _seeded_store(tmp_path, optout=optout)
    optout.opt_out("Sarah Okafor")
    result = query_experts("gdpr", store=store)
    names = [r["name"] for r in result["results"]]
    assert "Sarah Okafor" not in names
    assert names  # others still rank
