"""The two things that must never regress: decay math and opt-out exclusion."""

import math

from profiles.builder import build_profiles, _decay, W_THREAD_PARENT, W_STANDALONE
from profiles.store import ProfileStore
from privacy.optout import OptOutRegistry

NOW = 1_800_000_000.0
DAY = 86400.0


def _sig(author, topics, ts=NOW, **kw):
    return {"author": author, "topics": topics, "ts": str(ts), "channel": "test", **kw}


class TestDecay:
    def test_no_age_no_decay(self):
        assert _decay(0.0, 90.0) == 1.0

    def test_half_life(self):
        assert math.isclose(_decay(90.0, 90.0), 0.5, rel_tol=1e-9)

    def test_old_signal_fades(self):
        recent = build_profiles([_sig("a", ["gdpr"], ts=NOW)], now=NOW)
        stale = build_profiles([_sig("a", ["gdpr"], ts=NOW - 360 * DAY)], now=NOW)
        assert stale["a"]["topics"]["gdpr"] < 0.1 * recent["a"]["topics"]["gdpr"]


class TestWeighting:
    def test_thread_parent_beats_standalone(self):
        p = build_profiles([
            _sig("author", ["gdpr"], is_thread_parent=True, reply_count=0),
            _sig("lurker", ["gdpr"]),
        ], now=NOW)
        assert p["author"]["topics"]["gdpr"] == W_THREAD_PARENT
        assert p["lurker"]["topics"]["gdpr"] == W_STANDALONE

    def test_replies_received_boost_capped(self):
        p = build_profiles(
            [_sig("a", ["gdpr"], is_thread_parent=True, reply_count=100)], now=NOW
        )
        assert p["a"]["topics"]["gdpr"] == W_THREAD_PARENT + 2.5

    def test_volume_does_not_beat_depth(self):
        """chris.taylor's case: many standalone messages < few expert threads."""
        chatter = [_sig("chris", ["gdpr"]) for _ in range(4)]
        expert = [_sig("sarah", ["gdpr"], is_thread_parent=True, reply_count=4)
                  for _ in range(2)]
        p = build_profiles(chatter + expert, now=NOW)
        assert p["sarah"]["topics"]["gdpr"] > p["chris"]["topics"]["gdpr"]


class TestOptOut:
    def test_opted_out_user_never_stored_or_returned(self, tmp_path):
        registry = OptOutRegistry(path=tmp_path / "optouts.json")
        registry.opt_out("Sarah Okafor")
        store = ProfileStore(path=tmp_path / "profiles.json", optout=registry)

        profiles = build_profiles([
            _sig("Sarah Okafor", ["gdpr"], is_thread_parent=True, reply_count=3),
            _sig("Tom Hardwick", ["gdpr"]),
        ], now=NOW)
        store.save_all(profiles)

        loaded = store.load_all()
        assert "Sarah Okafor" not in loaded
        assert "Tom Hardwick" in loaded

    def test_opt_back_in(self, tmp_path):
        registry = OptOutRegistry(path=tmp_path / "optouts.json")
        registry.opt_out("maya")
        assert registry.is_opted_out("Maya")  # case-insensitive
        registry.opt_in("MAYA")
        assert not registry.is_opted_out("maya")
