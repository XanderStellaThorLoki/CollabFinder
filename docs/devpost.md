# Devpost submission text (paste-ready)

## Inspiration

Ambition without guidance is a path to career stagnation. In large organisations, the people who advance fastest aren't always the most talented — they're the ones who know who to call. That knowledge lives in informal networks that new hires spend years breaking into.

CollabFinder exists so that nobody who wants to do well gets stuck because they couldn't figure out who to pair up with. The knowledge is already in your Slack workspace. We surface it.

## What it does

CollabFinder turns public channel activity into a living expertise map of your organisation. Ask *"who knows about GDPR compliance?"* and you get a person, not a list — ranked, with the reason why, and an honest confidence level.

**One brain, four surfaces:**

- `/collab <topic>` — the slash command
- **Agent pane & DM** — ask conversationally, get the same ranked answer
- **App Home** — a search box, plus a personal privacy dashboard showing exactly what CollabFinder knows about *you*
- **MCP** — the same `query_experts` tool, served publicly for any agent to call

**What makes the answers trustworthy:**

- **Depth beats volume.** Threads you author and questions you answer count heavily; raw message count doesn't. Asking about a topic is scored as interest, not expertise — and the answer says "asked about this," never "expert," when that's all the evidence.
- **Every result cites its reason.** *"Authored 3 threads in #legal-compliance, drew 12 replies."* Patterns of participation, never message quotes.
- **Honesty over theatre.** Weak signal gets a low-confidence label; no signal gets a plain "no clear expert signal" instead of a fabricated answer.
- **Recency decay.** Signals fade with a 90-day half-life — go quiet on a topic and CollabFinder stops recommending you for it: $w_i = \sum_t f_{i,t} \cdot e^{-\lambda (T - t)}$

**Outside Experts — when the org can't answer.** The expertise graph doesn't dead-end at the company walls. An org-curated, credential-verified consultant directory rides along with results: name, credentials, rate, and a booking link on the expert's own page. Referrals are attribution-tagged and click-logged — the platform earns a commission from the expert on referred business, and consultation payment never touches CollabFinder.

**Privacy is the spine, not a setting:**

- **Public by default.** Public channels and @mentions only — enforced by the bot's own Slack scopes (`search:read.public`), not just policy. It lacks the key, not the manners.
- **Ambient disclosure.** Any channel under org-level expanded monitoring carries a pinned banner. Like the light on a webcam: no banner, no monitoring.
- **One-click opt-out.** Enforced at both ingest and query time, effective immediately, reversible, and nobody is notified.
- **See yourself.** The Home tab shows every user their own indexed topics and opt-out status.
- **Auditable.** Every indexer read is logged.

## How we built it

| Layer | Technology |
|---|---|
| Indexing | Slack Web API / Real-Time Search, public-only scopes, audit-logged |
| Expertise model | Topic frequency × contribution depth × 90-day recency decay |
| Agent tool | `query_experts` via MCP (streamable HTTP) — FastAPI on Cloud Run, registered through Slack's MCP Servers integration |
| Slack surfaces | Bolt (Python, Socket Mode): slash command, agent pane, DMs, App Home, pinned banner |
| Storage | Local JSON for the demo; Firestore + BigQuery attach via env vars |
| Outside Experts | Curated directory with verification status, referral-tagged booking links, click audit trail |

The demo workspace is seeded by a reproducible generator: 10 personas, 9 channels, ~500 messages with real thread structure — including a deliberately high-volume, zero-expertise persona to prove the ranking can't be gamed by talking a lot.

## Challenges we ran into

**The model was right and the demo data was wrong — twice.** Our first live index ranked the noisiest persona #1 for GDPR because the seed corpus let non-experts reply with expert-sounding answers. Fixing that surfaced something better: the person *asking* about GDPR outranked the person answering, because a question is structurally a thread parent. That produced the asking-≠-expertise heuristic — one of the model's most defensible ideas, found by watching it fail honestly.

**Substring matching is a trap.** "Access review" discussions matched "accessibility" queries until topic matching required whole-word overlap.

**One brain, many surfaces.** Slack's agent threads, plain DMs, slash commands, and Home tab are four different event surfaces with four different plumbing paths. We routed them all through a single responder so every surface gives the same answer — and every new surface is a wiring job, not a logic fork.

**Slack rate limits are real.** Seeding 500 messages into an Enterprise sandbox meant building a resume-safe seeder that reads back what already landed and posts only the difference — interruption-proof by design.

## Accomplishments we're proud of

- A privacy model that is transparent by *design* — scope-enforced public-only reads, an ambient banner, a per-user dashboard, and immediate opt-out
- Rankings that resist the loudest voice and say why they chose who they chose
- A revenue model with a hard ethical boundary: commissions come from experts on referred business; client money never flows through the platform
- A fully reproducible demo pipeline: wipe → seed → index → verified rankings, end to end

## What we learned

The hardest part of building a tool that reasons about people is building one people will trust. Feature completeness matters less than the answer to "what does this know about me, and who can see it?"

And the most valuable Slack signal isn't who talks the most — it's who gets replied to.

## What's next for CollabFinder

- **Automated commission collection** — Stripe Connect onboarding for Outside Experts, withholding the platform fee at booking time
- **Team gap analysis** — given a project brief, identify the expertise the team is missing and who fills it
- **Onboarding mode** — a new hire's "first five people to meet"
- **Expertise decay alerts** — warn when the only active expert on a critical topic goes quiet
- **Embedding-based topics** — the keyword extractor is deliberately swappable
