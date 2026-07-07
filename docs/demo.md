# Demo: setup + video script

## Remaining manual setup (Slack app config UI — one-time)

These are UI-only steps at api.slack.com/apps → CollabFinder:

1. **Socket Mode token** (lets the Bolt app run without a public URL):
   - Basic Information → App-Level Tokens → Generate Token
   - Name: `socket`, scope: `connections:write` → Generate
   - Copy the `xapp-...` token → set as `SLACK_APP_TOKEN` env var
   - Settings → Socket Mode → toggle **Enable Socket Mode** on
2. **Slash command:**
   - Features → Slash Commands → Create New Command
   - Command: `/collab`
   - Description: `Find the right colleague for any topic`
   - Usage hint: `<topic> | opt-out | opt-in | privacy`
   - Save. (With Socket Mode on, no Request URL is needed.)
3. **Reinstall** when prompted (scope/feature changes require it):
   - Settings → Install App → Reinstall to Workspace → Allow
4. **Banner demo prerequisite:** add `pins:write` to Bot Token Scopes
   (OAuth & Permissions) before the reinstall in step 3 — one reinstall
   covers both changes.

Run the app: `SLACK_BOT_TOKEN=... SLACK_APP_TOKEN=... python -m slack_app.app`

## Agent Builder wiring

The MCP server must be publicly reachable first (scripts/deploy.sh → Cloud
Run). Then in Slack: Agent Builder → new agent → add tool → MCP server →
`https://<cloud-run-url>/mcp` → the `query_experts_tool` appears. System
prompt for the agent:

> You help people find the right colleague. When asked who knows about a
> topic, call query_experts_tool and present its results faithfully —
> including its confidence level. Never invent expertise it didn't report.
> If confidence is low or results are empty, say so plainly.

## Video script (target 2:50, hard cap 3:00)

**Beat 1 — the problem (0:00–0:15).** Screen: the seeded workspace, busy
channels. VO: "This is a company. Nine channels, ten people, months of
conversation. Somewhere in here is the answer to the most common unanswered
question at work: who should I talk to about this?"

**Beat 2 — the agent (0:15–0:55).** Screen: open the CollabFinder agent
pane from the top bar; the greeting and suggested prompts appear. Click
*"Who knows about GDPR compliance?"* Card appears. VO: "CollabFinder is a
Slack agent. Ask it in plain language and you get a person, not a list —
with the reason: Sarah authored the GDPR threads other people reply to,
high confidence. And the person who merely *asked* about GDPR? Ranked low,
labeled honestly — asking is interest, not expertise." Click **Draft
intro** → show the draft.

**Beat 3 — volume ≠ expertise (0:55–1:20).** Screen: scroll a channel
showing Chris Taylor posting constantly, then a query where the quieter
expert outranks him. VO: "The loudest voice isn't ranked first.
CollabFinder weighs threads people author and questions they answer — not
message count. Talking a lot doesn't make you an expert here."

**Beat 4 — no expert? Outside Experts (1:20–1:40).** Screen: `/collab
patent law` → honest empty + Rachel Goldman card with rate and Book
consult button. VO: "And when nobody in the org has the answer, it says so
honestly — then offers a vetted outside consultant from the company's own
directory. Booked directly with them; payment never touches CollabFinder."

**Beat 5 — the privacy spine (1:40–2:25).** Screen: the pinned banner in
#legal-compliance → the Home tab: "What CollabFinder knows about you," the
opt-out button clicked live, panel flips to opted-out → `/collab privacy`.
VO: "Public channels only — the bot's own Slack permissions make private
content unreadable. Monitored channels carry a pinned banner, always: no
banner, no monitoring, like the light on a webcam. Every person sees
exactly what it knows about them, and opting out is one click, effective
immediately."

**Beat 6 — close (2:25–2:50).** Screen: architecture diagram. VO: "Under
the hood: Slack's Real-Time Search feeds an expertise index; the agent
queries it through an MCP server on Cloud Run — the same endpoint any
agent can use, registered with Slack's MCP integration. Built for the
Slack Agent Builder Challenge. CollabFinder — because ambition without
guidance is a path to career stagnation."

## Demo-day checklist

- [ ] Re-run indexer just before recording (fresh profiles)
- [ ] `/collab who knows about GDPR compliance?` → Sarah Okafor, high confidence
- [ ] `/collab bigquery` → Deepak Rao ranked first
- [ ] `/collab quantum knitting` → honest empty answer
- [ ] Banner pinned in demo channel; removed from others
- [ ] Opt-out round-trip works live
- [ ] Judges invited (slackhack@salesforce.com in; testing@devpost.com pending accept)
