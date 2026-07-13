# Video scripts — actions + voiceover

Two passes: record the screen actions first (Script 1, silent), then record
the voiceover (Script 2) over the assembled timeline. Target 2:50 total.

## Before recording (one-time setup)

- [ ] Windows: Win+N → Do Not Disturb ON
- [ ] Sandbox open in browser, zoom 110–125% (Ctrl and +)
- [ ] Bolt app running (`/collab bigquery` answers = it's up)
- [ ] Banner pinned in #legal-compliance
- [ ] Open the CollabFinder Home tab, click away to Messages, back to Home —
      confirms it renders fresh with no stale search
- [ ] Close all browser tabs except Slack; hide bookmarks bar (Ctrl+Shift+B)
- [ ] Have `collabfinder-media/05_architecture.png` open in a background tab

---

## SCRIPT 1 — SCREEN ACTIONS

Record each beat as its own clip. Move the mouse slowly; hold still wherever
a "HOLD" appears — that space is for the voiceover.

**CLIP 1 — The workspace (≈15s)**
1. Start in #general. Scroll down slowly through messages (~5s).
2. Click #legal-compliance. Scroll slowly (~5s).
3. Click #data-eng. HOLD 3s.

**CLIP 2 — Ask the agent (≈40s)**
1. Open the CollabFinder conversation (Apps → CollabFinder → Messages).
2. Type slowly: `Who knows about GDPR compliance?` — HOLD 1s before Enter.
3. Press Enter. Wait for the card. HOLD 5s on the full card.
4. Move cursor to rest 1 — Sarah Okafor / High confidence — trace the
   evidence line slowly with the cursor. HOLD 3s.
5. Move cursor to result 2 — Tom Hardwick / "asked about this" / Low. HOLD 3s.
6. Click **Draft intro ✍️** on Sarah's row. Wait for the draft. HOLD 5s.

**CLIP 3 — Volume ≠ expertise (≈25s)**
1. Click #general. Scroll to a stretch where Chris Taylor appears repeatedly
   (he's the most frequent poster). Scroll slowly past 4–5 of his messages.
2. Return to the CollabFinder conversation.
3. Type: `accessibility` → Enter. Wait for card.
4. HOLD 5s on Maya Chen at #1. (Chris appears nowhere — that's the point.)

**CLIP 4 — Outside Experts (≈20s)**
1. Still in the conversation, type: `trademark strategy` → Enter.
2. Wait for the response. HOLD 4s on "No clear expert signal".
3. Move cursor down to the Outside Experts section — Rachel Goldman card.
4. Click **Book consult ↗** — the CollabFinder booking page opens (rate,
   verification, commission line). HOLD 5s on the page, then close the tab.

**CLIP 5 — Privacy (≈45s)**
1. Click #legal-compliance. Click the pinned message bar at the top of the
   channel so the banner is visible. HOLD 4s on the banner text.
2. Go to Apps → CollabFinder → **Home** tab (should render fresh).
3. Click the search box, type: `bigquery` → Enter. HOLD 4s on Deepak's result.
4. Scroll down to "What CollabFinder knows about you". HOLD 3s.
5. Click **Opt out of profiling**. Wait for the panel to flip. HOLD 4s on
   the opted-out state.
6. Click **Opt back in**. HOLD 3s.

**CLIP 6 — The marketplace: rate your Expert Experience (≈25s)**
Coordinate with Claude: say "fire the rating card" right before recording —
the deal-close event sends the card to your DM within a second or two.
1. Be in the CollabFinder DM. The "Rate your Expert Experience" card for
   Rachel Goldman arrives. HOLD 3s.
2. Click the ★★★★★ (5-star) button. The card is replaced by the thank-you
   line. HOLD 3s.
3. Type `trademark strategy` → Enter. Rachel's card now shows
   "★ 5.0 (1)" next to her verified crest. HOLD 4s on that line.

**CLIP 7 — Close (≈15s)**
1. Switch to the browser tab with the architecture diagram.
2. Hold full screen, still. HOLD 10s minimum.

---

## SCRIPT 2 — VOICEOVER

Read at a relaxed pace. Each block matches its clip; if you finish a line
early, let the screen breathe — don't rush into the next block.

**CLIP 1 (15s)**
> This is a company Slack. Nine channels, ten people, months of
> conversation. Somewhere in here is the answer to the most common
> unanswered question at work: who should I talk to about this?

**CLIP 2 (40s)**
> CollabFinder answers it. Ask in plain language — who knows about GDPR
> compliance — and you get a person, not a list. Sarah authored the GDPR
> threads other people replied to. High confidence, and it shows its
> evidence. Second place is instructive: Tom only *asked* about GDPR, so
> he's ranked low and labeled honestly — asking is interest, not
> expertise. One click drafts the intro message, so reaching out stops
> being the hard part.

**CLIP 3 (25s)**
> The loudest person in this workspace posts everywhere, constantly. He
> never ranks first. CollabFinder weighs threads people author and
> questions they answer — not message count. When we ask about
> accessibility, the quieter engineer who actually did the work comes
> out on top.

**CLIP 4 (20s)**
> And when nobody in the company has the answer, it says so — no fake
> confidence. Then CollabFinder's own directory of trusted, verified
> experts steps in. Booking and payment run through CollabFinder — we vet
> the expert, we process the payment, and we take our commission on every
> booking.

**CLIP 5 (45s)**
> Privacy is enforced, not promised. The bot's own Slack permissions make
> private channels and DMs unreadable — it only sees public activity. Any
> channel under expanded monitoring carries this pinned banner: no banner,
> no monitoring. And every person can see exactly what CollabFinder knows
> about them — their own topics, on their own Home tab — with a one-click
> opt-out that takes effect immediately, at indexing and at query time.
> Opting back in is just as easy.

**CLIP 6 (25s)**
> The expert directory is a real marketplace. Experts set their own
> commission bid — it breaks ties between equally-matched experts, and
> they can change it any time as demand shifts. At signup they see live
> demand data for their field. And when a deal closes, both sides rate
> the experience — one tap for the buyer, right in Slack — and that
> rating follows the expert onto every future card.

**CLIP 7 (15s)**
> One ranking engine, four surfaces, an MCP server any agent can call,
> and a marketplace behind it. Built for the Slack Agent Builder
> Challenge. CollabFinder — because ambition without guidance is a path
> to career stagnation.

---

**Assembly:** trim clip heads/tails, join in order, lay the seven VO blocks
over their clips, nudge holds to fit. Budget: 15+40+25+20+45+25+15 = 185s —
that is 3:05, so tighten in edit: shave ~5s each from Clips 2 and 5 (the
long holds) to land ≈2:55. HARD CAP 3:00. Export 1080p MP4. Upload to
YouTube as **Public**.
