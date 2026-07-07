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

## Video script (target 2:30, hard cap 3:00)

**Beat 1 — the problem (0:00–0:20).** Screen: the seeded workspace, busy
channels. VO: "This is a company. Nine channels, ten people, months of
conversation. Somewhere in here is the answer to the most common unanswered
question at work: who should I talk to about this?"

**Beat 2 — the answer (0:20–1:00).** Screen: type `/collab who knows about
GDPR compliance?` in #general. Response card appears. VO: "CollabFinder
answers it in one message. Not just a name — the reason. Sarah authored the
GDPR threads other people reply to. That's expertise you can act on." Click
**Draft intro** → show the drafted DM.

**Beat 3 — volume ≠ expertise (1:00–1:30).** Screen: scroll #general
showing Chris Taylor posting constantly, then `/collab` result where the
quieter expert outranks him. VO: "The loudest person isn't ranked first.
CollabFinder weighs threads people start and questions they answer, not raw
message count."

**Beat 4 — the privacy spine (1:30–2:15).** Screen: `/collab privacy`
response, then the pinned banner in a channel, then `/collab opt-out`
followed by the same query with that person absent. VO: "Public channels
only — the bot's own Slack permissions make private content unreadable.
Org-level monitoring means a pinned banner, always. Like a webcam light: no
light, no camera. And anyone can opt out — effective immediately."

**Beat 5 — close (2:15–2:40).** Screen: architecture diagram. VO: "Slack
Real-Time Search feeds an expertise index; an Agent Builder agent queries
it over MCP. Built for the Slack Agent Builder Challenge — CollabFinder,
because ambition without guidance is a path to career stagnation."

## Demo-day checklist

- [ ] Re-run indexer just before recording (fresh profiles)
- [ ] `/collab who knows about GDPR compliance?` → Sarah Okafor, high confidence
- [ ] `/collab bigquery` → Deepak Rao ranked first
- [ ] `/collab quantum knitting` → honest empty answer
- [ ] Banner pinned in demo channel; removed from others
- [ ] Opt-out round-trip works live
- [ ] Judges invited (slackhack@salesforce.com in; testing@devpost.com pending accept)
