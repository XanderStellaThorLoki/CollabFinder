"""Expand personas + templates into a deterministic message plan.

Produces the full list of messages (parents, thread replies, standalone chatter)
that seed_sandbox.py posts to the Slack sandbox. Deterministic: same inputs and
seed always yield the same plan, so a wiped sandbox can be re-seeded identically.

The plan encodes WHO says WHAT and WHERE — expertise structure comes from role
assignment, not chance:
- Channel experts author threads and give answers (high thread-authorship +
  replies-received signal → high expertise score).
- Non-experts ask the questions experts answer.
- chris.taylor asks questions everywhere and answers nothing — the high-volume /
  low-expertise control the ranking demo needs.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, asdict
from pathlib import Path

HERE = Path(__file__).parent
DEFAULT_SEED = 42

# Per-channel volume knobs. Totals land ~520 messages across 9 channels.
# Template pools are smaller than these counts; templates repeat with different
# {kw} fills, which reads naturally (same person, same beat, different topic).
THREADS_PER_CHANNEL = 8
REPLIES_PER_THREAD = (2, 6)  # min, max
QUESTIONS_PER_CHANNEL = 6
CHATTER_PER_CHANNEL = 9


@dataclass
class PlannedMessage:
    channel: str
    author: str          # persona handle
    text: str
    thread_key: str | None = None  # parents define it, replies reference it
    is_reply: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def _load(name: str) -> dict:
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def _fill(template: str, keywords: list[str], rng: random.Random) -> str:
    return template.replace("{kw}", rng.choice(keywords)) if "{kw}" in template else template


def _cycle_to(items: list, n: int) -> list:
    """Repeat the list until it has n entries (empty list stays empty)."""
    if not items:
        return []
    return [items[i % len(items)] for i in range(n)]


class CorpusBuilder:
    def __init__(self, seed: int = DEFAULT_SEED):
        self.rng = random.Random(seed)
        data = _load("personas.json")
        self.personas = {p["handle"]: p for p in data["personas"]}
        self.channels = data["channels"]
        self.templates = _load("templates.json")["channels"]

    def _experts_in(self, channel: str) -> list[str]:
        return [h for h, p in self.personas.items() if channel in p["expert_channels"]]

    def _actives_in(self, channel: str, exclude: set[str] | None = None) -> list[str]:
        exclude = exclude or set()
        return [
            h for h, p in self.personas.items()
            if channel in p["active_channels"] and h not in exclude
        ]

    def build(self) -> list[PlannedMessage]:
        plan: list[PlannedMessage] = []
        for channel in self.channels:
            t = self.templates.get(channel)
            if not t:
                continue
            kws = t["keywords"]
            experts = self._experts_in(channel)
            actives = self._actives_in(channel)
            if not actives:
                continue

            # Threads: expert-authored parent + replies from others in channel.
            thread_templates = list(t.get("threads", []))
            self.rng.shuffle(thread_templates)
            thread_templates = _cycle_to(thread_templates, THREADS_PER_CHANNEL)
            for i, parent_tpl in enumerate(thread_templates):
                author = self.rng.choice(experts) if experts else self.rng.choice(actives)
                key = f"{channel}-thread-{i}"
                plan.append(PlannedMessage(channel, author, _fill(parent_tpl, kws, self.rng), thread_key=key))
                repliers = self._actives_in(channel, exclude={author}) or actives
                for _ in range(self.rng.randint(*REPLIES_PER_THREAD)):
                    replier = self.rng.choice(repliers)
                    reply_pool = t.get("answers", []) + t.get("chatter", [])
                    plan.append(PlannedMessage(
                        channel, replier, _fill(self.rng.choice(reply_pool), kws, self.rng),
                        thread_key=key, is_reply=True,
                    ))

            # Q&A: non-expert asks (as a thread parent), expert answers in-thread.
            askers = [h for h in actives if h not in experts] or actives
            question_templates = list(t.get("questions", []))
            self.rng.shuffle(question_templates)
            question_templates = _cycle_to(question_templates, QUESTIONS_PER_CHANNEL)
            for i, q_tpl in enumerate(question_templates):
                asker = self.rng.choice(askers)
                key = f"{channel}-q-{i}"
                plan.append(PlannedMessage(channel, asker, _fill(q_tpl, kws, self.rng), thread_key=key))
                if experts and t.get("answers"):
                    answerer = self.rng.choice(experts)
                    plan.append(PlannedMessage(
                        channel, answerer, _fill(self.rng.choice(t["answers"]), kws, self.rng),
                        thread_key=key, is_reply=True,
                    ))

            # Standalone chatter from anyone active.
            for _ in range(CHATTER_PER_CHANNEL):
                if not t.get("chatter"):
                    break
                author = self.rng.choice(actives)
                plan.append(PlannedMessage(channel, author, _fill(self.rng.choice(t["chatter"]), kws, self.rng)))

        return plan

    def summarize(self, plan: list[PlannedMessage]) -> str:
        by_channel: dict[str, int] = {}
        by_author: dict[str, int] = {}
        for m in plan:
            by_channel[m.channel] = by_channel.get(m.channel, 0) + 1
            by_author[m.author] = by_author.get(m.author, 0) + 1
        lines = [f"Total messages: {len(plan)}", "", "By channel:"]
        lines += [f"  #{c}: {n}" for c, n in sorted(by_channel.items())]
        lines += ["", "By author:"]
        lines += [f"  {a}: {n}" for a, n in sorted(by_author.items(), key=lambda x: -x[1])]
        return "\n".join(lines)


if __name__ == "__main__":
    builder = CorpusBuilder()
    plan = builder.build()
    print(builder.summarize(plan))
