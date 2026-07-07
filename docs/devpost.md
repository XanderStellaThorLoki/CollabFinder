# Devpost submission text (paste-ready)

## Inspiration

Ambition without guidance is a path to career stagnation. In large
organisations, the people who advance fastest aren't always the most talented —
they're the ones who know who to call. That institutional knowledge lives in
the heads of long-tenured employees and in informal networks new hires spend
years breaking into.

CollabFinder exists so that nobody who wants to do well gets stuck simply
because they couldn't figure out who to pair up with to get there. The
knowledge is already in your Slack workspace. We just surface it.

## What it does

CollabFinder is a Slack agent that turns public channel activity into a living
expertise map of your organisation.

Ask `/collab who knows about GDPR compliance` and it returns ranked colleagues
with plain-English reasoning drawn from their actual participation — "authored
3 threads in #legal-compliance, drew 12 replies" — plus a confidence band it
is honest about. No surveys, no self-reported skill tags.

Key behaviours:

- Indexes **public channels and @mentions only** by default — enforced by the
  bot's own Slack scopes (`search:read.public`), not just policy
- Weighs **contribution depth over volume**: threads you author and questions
  you answer count; raw message count doesn't. Asking about a topic is
  interest, not expertise — the model scores it accordingly, and if asking is
  all the evidence there is, the answer says "asked about this," not "expert"
- **Says "no clear signal" instead of fabricating certainty** when the
  evidence is thin
- Drafts an intro message to lower the barrier to reaching out
- `/collab opt-out` removes you from profiling immediately, enforced at both
  ingest and query time

Privacy is a first-class feature: expanded monitoring is an org-level
decision, and any monitored channel carries a pinned banner — like the light
on an active webcam. No banner, no monitoring.

## How we built it

| Layer | Technology |
|---|---|
| Message indexing | Slack Web API / Real-Time Search, public-only scopes |
| Expertise model | topic frequency × recency decay × contribution depth |
| Profile store | Local JSON (demo) / Firestore (deploy), opt-out filtered |
| Agent tool | MCP server (streamable HTTP) built with FastAPI, on Cloud Run |
| Slack surface | Bolt (Python): /collab command, Block Kit cards, pinned banner |
| Transparency | Audit log of every indexer read; plain-English Canvas policy |

Recency decay: $w_i = \sum_t f_{i,t} \cdot e^{-\lambda (T - t)}$ with a 90-day
half-life — go quiet on a topic and CollabFinder stops recommending you for it.

The demo workspace is seeded by a reproducible generator: 10 personas, 9
channels, 518 messages with real thread structure — including a deliberately
high-volume, low-expertise persona to prove the ranking can't be gamed by
talking a lot.

## Challenges we ran into

**The model was right and the demo data was wrong — twice.** Our first live
index ranked the noisiest persona #1 for GDPR because the seeded corpus let
non-experts reply with expert-sounding answers. Fixing that surfaced a second
bug: someone *asking* about GDPR outranked the person answering, because a
question is structurally a thread parent. That produced the "asking ≠
expertise" heuristic — thread parents ending in "?" score as interest, not
authority — which turned out to be one of the model's most defensible ideas.

**Substring matching is a trap.** "access review" discussions matched
"accessibility" queries until topic matching required whole-word overlap.

**Honesty as a feature costs nothing until you build it.** Confidence bands,
"asked about this" labels, and empty-but-honest answers each forced the
evidence model to track *why* someone ranks, not just how much.

## Accomplishments we're proud of

- Privacy transparent by design, not by policy — scope-enforced public-only
  reading, ambient disclosure, immediate opt-out
- Suggestions that cite reasons, not just names
- A reproducible demo pipeline: wipe → seed → index → verified rankings

## What we learned

The hardest part of building a tool that reasons about people is building one
people will trust. Feature completeness matters less than the answer to "what
does this know about me, and who can see it?"

And the most valuable Slack signal isn't who talks the most — it's who gets
replied to.

## What's next for CollabFinder

- **Team gap analysis** — given a project brief, identify missing expertise
- **Onboarding mode** — a new hire's "first five people to meet"
- **Expertise decay alerts** — warn when the only active expert on a critical
  topic goes quiet
- **Embedding-based topics** — the extractor is deliberately swappable
