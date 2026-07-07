"""App Home tab: expertise search + the personal privacy dashboard.

The Home tab is where transparency gets personal: alongside the search box,
every user sees exactly what CollabFinder knows about THEM — their top
indexed topics, their opt-in/out status, and a one-click way out.
"""

from __future__ import annotations

from mcp_server.ranking import query_experts
from privacy.optout import OptOutRegistry
from profiles.store import ProfileStore

from .blocks import CONFIDENCE_LABEL, _context, _section


def build_home_view(user_display: str, search_topic: str | None = None,
                    optout: OptOutRegistry | None = None) -> dict:
    optout = optout or OptOutRegistry()
    blocks: list[dict] = [
        _section("*Find the right colleague for any topic.*"),
        {
            "type": "input",
            "dispatch_action": True,
            "block_id": "home_search_block",
            "element": {
                "type": "plain_text_input",
                "action_id": "home_search",
                "placeholder": {"type": "plain_text",
                                "text": "e.g. GDPR compliance, BigQuery, accessibility…"},
                "dispatch_action_config": {"trigger_actions_on": ["on_enter_pressed"]},
            },
            "label": {"type": "plain_text", "text": "What expertise are you looking for?"},
        },
    ]

    if search_topic:
        result = query_experts(search_topic)
        blocks.append({"type": "divider"})
        if result["results"]:
            blocks.append(_section(f"*Results for “{search_topic}”:*"))
            for i, r in enumerate(result["results"], 1):
                badge = CONFIDENCE_LABEL.get(r["confidence"], r["confidence"])
                blocks.append(_section(f"*{i}. {r['name']}*  ·  {badge}\n_{r['reason']}_"))
        else:
            blocks.append(_section(
                f"No clear expert signal for *{search_topic}* in public channels."
            ))
        for e in result.get("external", []):
            blocks.append(_section(
                f":telescope: *Outside Expert:* {e['name']} · {e['rate']}\n"
                f"_{e['field']}_"
            ))

    # --- personal privacy dashboard -----------------------------------------
    blocks.extend([
        {"type": "divider"},
        _section(f"*What CollabFinder knows about you ({user_display})*"),
    ])

    if optout.is_opted_out(user_display):
        blocks.append(_section(
            ":no_entry: You are *opted out*. Nothing about you is profiled, "
            "stored, or shown to anyone."
        ))
        button_text, button_action = "Opt back in", "home_opt_in"
    else:
        profile = ProfileStore().load_all().get(user_display)
        if profile:
            top = sorted(profile["topics"].items(), key=lambda kv: -kv[1])[:5]
            topics = ", ".join(f"*{t}*" for t, _ in top)
            blocks.append(_section(
                f"Your top indexed topics from public channels: {topics}"
            ))
        else:
            blocks.append(_section(
                "No public activity indexed for you yet — you have no profile."
            ))
        button_text, button_action = "Opt out of profiling", "home_opt_out"

    blocks.append({
        "type": "actions",
        "elements": [{
            "type": "button",
            "text": {"type": "plain_text", "text": button_text},
            "action_id": button_action,
        }],
    })
    blocks.append(_context(
        "Public channels and @mentions only · signals fade with a 90-day "
        "half-life · every indexer read is audit-logged · full policy: "
        "`/collab privacy`"
    ))

    return {"type": "home", "blocks": blocks}
