# Devpost submission text (paste-ready)

## Inspiration

Finding the right person to ask inside a company depends on informal networks. New hires don't have them. The information needed to route these questions already exists in Slack message history.

## What it does

CollabFinder indexes public Slack channels and builds a per-person expertise profile from message activity. Users query it and get ranked people with the evidence behind the ranking and a confidence level.

Query surfaces: `/collab <topic>`, DM, the agent pane, an App Home search box, and an MCP tool (`query_experts`) callable by other agents. All use the same ranking code.

Scoring: authored threads weigh 3.0 (plus a bonus per reply received), thread replies 2.0, standalone messages 1.0, questions 0.5. Scores decay with a 90-day half-life. Results state the evidence ("authored 3 threads in #legal-compliance, drew 12 replies") and a confidence band. A profile whose only evidence is asking questions is capped at low confidence. Queries with no matching signal return an empty result.

Results can also include a consultant from CollabFinder's own trusted-expert directory: name, credentials, rate, rating, and a booking link. Experts are recruited and credential-verified by the platform; only verified entries are shown. The directory is a marketplace: each expert sets their own commission bid (10% floor, changeable any time), relevance ranks the results, and the bid breaks ties between equally-matched experts. Prospective experts see recent query volume for their field at signup, so bids track real demand. Booking and payment run through CollabFinder's hosted page; the platform withholds the commission and pays out the expert (Stripe capture is the launch build). At deal close, buyer and seller both rate the experience — one tap in Slack for the buyer — and averages show on every card.

Privacy controls: only public channels and @mentions are read, which the bot's OAuth scopes enforce (`search:read.public`, `channels:history`). Message content is never quoted in results. Channels under org-configured expanded monitoring get a pinned notice. `/collab opt-out` removes a user from indexing and results immediately; the App Home tab shows each user their own indexed topics and opt-out state. Indexer reads are logged.

## How we built it

- Indexer: Python, Slack Web API, public channels only, writes an audit log
- Profile store: local JSON; Firestore and BigQuery attach via env vars
- MCP server: FastAPI, streamable HTTP at `/mcp` plus REST, deployed on Cloud Run, registered via Slack's MCP Servers integration
- Slack app: Bolt (Python) over Socket Mode — slash command, agent pane, DM, App Home, pinned banner
- Demo data: deterministic seeder generates 10 personas and ~500 threaded messages across 9 channels, including a high-volume/low-expertise persona as a ranking control
- 19 tests cover the decay math, question weighting, opt-out enforcement, ranking, and directory filtering

## Challenges we ran into

- First live index ranked the noisiest persona #1 because the seed corpus let non-experts post answer-type replies. Fixed the corpus generator and re-seeded.
- Questions are thread parents, so askers scored as authors. Added question detection (0.5 weight) and separate evidence tracking.
- Substring topic matching matched "access review" to "accessibility". Switched to whole-word matching.
- Slack's agent threads, DMs, and Home tab are separate event surfaces; unified them behind one responder.
- Enterprise sandbox rate limits interrupted seeding; made the seeder resume-safe (reads existing messages, posts only the difference).

## Accomplishments that we're proud of

- All demo queries return the correct expert with accurate evidence strings, verified against the live workspace
- Opt-out enforced at both write and read paths, with tests
- Ranking is not gameable by message volume, demonstrated by the control persona
- Reproducible pipeline: wipe → seed → index → query

## What we learned

Reply and thread structure carries more expertise signal than message frequency. Most of the effort went into making the evidence strings accurate rather than into the ranking itself; overstated evidence was the most common bug.

## What's next for CollabFinder

- Stripe checkout on the booking page: automatic commission withholding and expert payouts
- Team gap analysis against a project brief
- Onboarding suggestions for new hires
- Alerts when a topic's only active expert goes inactive
- Swap keyword extraction for embeddings
