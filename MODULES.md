# CollabFinder — Module Guide

Working reference for what each module does, what it depends on, and what "done" means for it.
Keep this current as the build progresses — it is the map, the code is the territory.

## Big picture

```
seeding  →  (Slack sandbox)  →  indexer  →  profiles  →  mcp_server  →  slack_app  →  user
                                    │            │                          │
                                    └── audit ───┴──────── privacy ────────┘
```

One-line pitch: index public Slack activity → per-person expertise profiles → agent answers
"who should I talk to about X?" with a ranked, reasoned suggestion. Privacy layer is
load-bearing: public-by-default scope, org-level opt-in for anything more, persistent
banner in monitored channels, per-user opt-out.

---

## `seeding/` — sandbox demo data

**Purpose:** populate the Slack developer sandbox with realistic fake activity so the demo
has signal to rank. ~10 users, ~500 messages, 6–8 public channels with distinct topic
clusters (#legal-compliance, #frontend, #data-eng, ...). Reproducible: wipe + re-seed must
always produce a working demo.

- `seed_sandbox.py` — creates channels, posts messages/threads via Slack Web API using
  per-user tokens (or a single bot with username overrides if sandbox limits apply).
  Message corpus lives in a JSON/YAML fixture alongside, not inline in code.

**Depends on:** Slack Web API only. Nothing depends on it (demo tooling).
**Done when:** fresh sandbox + one script run = queryable demo workspace.

## `indexer/` — read Slack, extract signal

**Purpose:** pull public-channel history and @mentions, turn raw messages into
topic signals per user. The ONLY module that reads Slack content. Scope enforcement
lives here: public channels + mentions by default, private sources only when org
opt-in flag is set in `config/`.

- `slack_reader.py` — Real-Time Search API / `conversations.history` pagination,
  channel discovery, mention extraction. Emits normalized message records.
- `topic_extractor.py` — message record → topic signals (keyword/entity extraction;
  keep simple — TF-IDF-ish keywords per message is enough for the hackathon).
- `audit_log.py` — every read the indexer performs writes a BigQuery row
  (who/what/when/scope). Backs the transparency claim with something real.

**Depends on:** Slack API, `config/` scope settings.
**Done when:** running the indexer against the seeded sandbox produces per-user
topic signal records with timestamps, thread metadata, and reply counts.

## `profiles/` — expertise weighting + storage

**Purpose:** turn raw topic signals into ranked per-person expertise profiles.
Pure logic + storage; no Slack calls.

- `builder.py` — the weighting model: topic frequency × recency decay
  (w = Σ f·e^(−λ(T−t))) × thread depth. Thread authorship and replies-received
  weighted separately from raw message count (talkers ≠ experts).
- `store.py` — Firestore read/write for profile documents; opt-out flag filter
  applied at read time so excluded users can never leak into results.

**Depends on:** `indexer/` output shape, Firestore.
**Done when:** query "GDPR" against seeded data returns ranked fake users with
sensible scores, and an opted-out user never appears.

## `mcp_server/` — the agent's tool

**Purpose:** FastAPI service exposing the MCP tool `query_experts(topic, limit)` →
ranked profiles WITH reasoning strings ("authored 3 threads in #legal-compliance
in past 60 days"). This is the interface Agent Builder calls.

- `server.py` — FastAPI app, MCP tool registration, health endpoint for Cloud Run.
- `ranking.py` — turns profile scores into a ranked result set + generates the
  reasoning string + confidence band (high/medium/low). Honest low-confidence
  handling lives here: weak signal must say so, not fabricate certainty.

**Depends on:** `profiles/store.py`.
**Done when:** `query_experts("gdpr", 3)` over HTTP returns ranked, reasoned,
confidence-labeled results from the seeded data.

## `slack_app/` — user-facing Slack surface

**Purpose:** everything the user sees in Slack. Bolt app.

- `app.py` — Bolt entry point, event wiring, Cloud Run compatible.
- `commands.py` — `/collab <topic>`, `/collab opt-out`, `/collab privacy` handlers;
  natural-language invocation via Agent Builder.
- `blocks.py` — Block Kit builders: result card (name, role, confidence badge,
  "why" line, Draft intro + See more buttons), low-confidence variant, opt-out
  confirmation.
- `banner.py` — posts/pins the persistent transparency banner to any channel under
  expanded monitoring; removes it when monitoring is disabled. The webcam light.

**Depends on:** `mcp_server/` (or calls `profiles/` directly if simpler under
deadline), `privacy/`.
**Done when:** end-to-end in sandbox: ask → ranked reasoned answer as Block Kit;
banner appears when opt-in enabled; opt-out works from Slack.

## `privacy/` — consent state + transparency content

**Purpose:** the privacy model as code, one place to point judges at.

- `optout.py` — per-user opt-out state (Firestore), checked by `profiles/store.py`
  at read time and by `indexer/` at ingest time.
- `canvas.py` — creates/updates the plain-English transparency Canvas: what's
  collected, retention, who sees suggestions, how to opt out.

**Depends on:** Firestore, Slack Canvas API.
**Done when:** opt-out round-trips (command → flag → excluded from results) and
the Canvas link resolves from the banner.

## `config/` — deployment + scope settings

- `settings.example.yaml` — org-level settings template: expanded-monitoring opt-in
  flag, monitored channel list, recency half-life λ, confidence thresholds.
  Real settings file is gitignored; example stays in repo for judges.

## `docs/` — submission assets

- `architecture.png` — the Devpost architecture diagram (from
  `Desktop\Vidium\collabfinder-media\05_architecture.png`).
- Devpost writeup drafts, demo video script as they materialize.

## `tests/` — protect the demo

Priority order under deadline: (1) profile weighting math — decay + thread-depth
weighting with fixed fixtures, (2) opt-out exclusion — the one privacy claim that
must never regress, (3) ranking/confidence bands. Skip Slack API mocking unless
time allows.

## `scripts/` — ops

- `deploy.sh` — Cloud Run deploy for mcp_server + slack_app (bash, Mac-compatible,
  LF endings — Elliot uses a Mac).

---

## Build order (maps to workflow phases)

1. `seeding/` → seeded sandbox (Phase 1)
2. `indexer/` + `profiles/` → queryable Firestore (Phase 1)
3. `mcp_server/` → ranked reasoned results over HTTP (Phase 2)
4. `slack_app/` → end-to-end in Slack (Phase 2)
5. `privacy/` + `banner.py` → the pitch's spine (Phase 3)

## Deadline facts (from rules, verified 2026-07-04)

- Due **July 13, 5:00 pm Pacific** (= 1:00 am July 14 UK). Internal deadline July 12.
- Must submit: text description, demo video <3 min (public YouTube/Vimeo),
  architecture diagram, **sandbox URL** (judges look inside the workspace).
- Track: Slack Agents for Orgs. Team ≤4. MIT license chosen; new work ✓.

## Cut lines (if time runs short, in order)

1. Intro-draft button → "what's next"
2. BigQuery audit log → soften writeup claim
3. Org opt-in config → default scope demo only, banner as mockup
4. NEVER cut: end-to-end query, reasoning strings, opt-out.
