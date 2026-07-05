"""CollabFinder Bolt app — the /collab command and interactive buttons.

Subcommands:
    /collab <topic>      find experts on a topic
    /collab opt-out      exclude yourself from profiling (immediate)
    /collab opt-in       re-include yourself
    /collab privacy      plain-English data policy

Runs in Socket Mode locally (SLACK_APP_TOKEN set) or HTTP mode on Cloud Run.
"""

from __future__ import annotations

import os
import re

from slack_bolt import App

from mcp_server.ranking import query_experts
from privacy.optout import OptOutRegistry
from . import blocks

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))
optout = OptOutRegistry()


def _display_name(client, user_id: str) -> str:
    profile = client.users_info(user=user_id)["user"]["profile"]
    return profile.get("display_name") or profile.get("real_name") or user_id


@app.command("/collab")
def handle_collab(ack, respond, command, client):
    ack()
    text = (command.get("text") or "").strip()
    user_id = command["user_id"]

    if not text or text in ("help", "?"):
        respond(
            "Usage: `/collab <topic>` to find experts, `/collab privacy` for the "
            "data policy, `/collab opt-out` / `/collab opt-in` to control whether "
            "you appear in results."
        )
        return

    if text == "opt-out":
        name = _display_name(client, user_id)
        optout.opt_out(name)
        respond(blocks=blocks.opt_out_confirmation(name), response_type="ephemeral")
        return

    if text == "opt-in":
        name = _display_name(client, user_id)
        optout.opt_in(name)
        respond(blocks=blocks.opt_in_confirmation(name), response_type="ephemeral")
        return

    if text == "privacy":
        respond(blocks=blocks.privacy_summary(os.environ.get("COLLABFINDER_CANVAS_URL")),
                response_type="ephemeral")
        return

    # Anything else is a topic query. Strip a leading question phrasing.
    topic = re.sub(r"^(who (knows|should i talk to) about\s+)", "", text, flags=re.I).rstrip("?")
    result = query_experts(topic)
    respond(blocks=blocks.expert_results(result), response_type="ephemeral")


@app.action("draft_intro")
def handle_draft_intro(ack, body, respond):
    ack()
    expert = body["actions"][0]["value"]
    asker = body["user"]["id"]
    draft = (
        f"Hi {expert} — <@{asker}> here. CollabFinder pointed me your way: "
        f"I'm working on something that overlaps with what you've been discussing, "
        f"and I'd value 15 minutes of your time this week. Any slot that suits you?"
    )
    respond(
        text=f"Draft intro (copy, tweak, send):\n>{draft}",
        response_type="ephemeral",
        replace_original=False,
    )


def main() -> None:
    if os.environ.get("SLACK_APP_TOKEN"):
        from slack_bolt.adapter.socket_mode import SocketModeHandler
        SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
    else:
        app.start(port=int(os.environ.get("PORT", 3000)))


if __name__ == "__main__":
    main()
