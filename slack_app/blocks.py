"""Block Kit builders. Pure functions: result dict in, Slack blocks out."""

from __future__ import annotations

CONFIDENCE_LABEL = {
    "high": "High confidence",
    "medium": "Medium confidence",
    "low": "Low confidence — thin signal",
}

PRIVACY_FOOTER = (
    "Based on public channel activity only · "
    "`/collab privacy` explains exactly what CollabFinder uses"
)


def expert_results(payload: dict) -> list[dict]:
    """Blocks for a query_experts result."""
    topic = payload["query"]
    results = payload["results"]

    if not results:
        return [
            _section(f"No clear expert signal for *{topic}* in public channels."),
            _context(
                "That's an honest answer, not a failure — nobody has discussed this "
                "publicly enough to rank. Try broader terms, or ask in #general."
            ),
            _context(PRIVACY_FOOTER),
        ]

    blocks = [_section(f"Best matches for *{topic}*:")]
    for i, r in enumerate(results, 1):
        badge = CONFIDENCE_LABEL.get(r["confidence"], r["confidence"])
        blocks.append(_section(f"*{i}. {r['name']}*  ·  {badge}\n_{r['reason']}_"))
    if payload["confidence"] == "low":
        blocks.append(_context(
            "Signal is thin — treat these as leads, not answers."
        ))
    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Draft intro ✍️"},
                "action_id": "draft_intro",
                "value": results[0]["name"],
                "style": "primary",
            },
        ],
    })
    blocks.append(_context(PRIVACY_FOOTER))
    return blocks


def opt_out_confirmation(user_display: str) -> list[dict]:
    return [
        _section(f"Done. *{user_display}* is now excluded from CollabFinder."),
        _context(
            "You will never appear in expertise results. Your messages are not "
            "profiled from this point on, and your existing profile has been removed. "
            "Use `/collab opt-in` to reverse this at any time."
        ),
    ]


def opt_in_confirmation(user_display: str) -> list[dict]:
    return [
        _section(f"Welcome back. *{user_display}* is included in CollabFinder again."),
        _context("Your public-channel activity will be profiled from the next index run."),
    ]


def privacy_summary(canvas_url: str | None = None) -> list[dict]:
    blocks = [
        _section("*What CollabFinder knows, in plain English:*"),
        _section(
            "• *Reads:* public channels and @mentions only. The bot's Slack "
            "permissions make private channels and DMs unreadable — it isn't a "
            "policy, it's a missing key.\n"
            "• *Builds:* a per-person topic map from what you post publicly, "
            "weighted toward threads you author and questions you answer.\n"
            "• *Shows:* names, confidence, and *why* — never message quotes.\n"
            "• *Logs:* every read the indexer performs, to an audit table.\n"
            "• *Opt out:* `/collab opt-out`, effective immediately, reversible."
        ),
    ]
    if canvas_url:
        blocks.append(_section(f"Full data policy: {canvas_url}"))
    return blocks


def transparency_banner() -> list[dict]:
    return [
        _section(
            ":large_yellow_circle: *This channel is AI-monitored for collaboration "
            "suggestions.*"
        ),
        _context(
            "CollabFinder indexes public activity here to help colleagues find each "
            "other. Run `/collab privacy` for exactly what is collected and how to "
            "opt out. If this banner isn't pinned, this channel isn't monitored."
        ),
    ]


def _section(text: str) -> dict:
    return {"type": "section", "text": {"type": "mrkdwn", "text": text}}


def _context(text: str) -> dict:
    return {"type": "context", "elements": [{"type": "mrkdwn", "text": text}]}
