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

from slack_bolt import App, Assistant

from mcp_server.ranking import query_experts
from privacy.optout import OptOutRegistry
from . import blocks

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))
optout = OptOutRegistry()

# --- Agent pane (Slack "Agent experience") ----------------------------------
# Same brain as /collab, conversational surface. One code path, three
# surfaces: slash command, agent pane, MCP for other agents.
assistant = Assistant()


@assistant.thread_started
def greet(say, set_suggested_prompts):
    say("Hi — ask me who to talk to about any topic, e.g. *who knows about GDPR compliance?*")
    set_suggested_prompts(prompts=[
        "Who knows about GDPR compliance?",
        "Who should I talk to about BigQuery?",
        "What does CollabFinder know about me?",
    ])


def respond_to_text(text: str, say) -> None:
    """One responder for every conversational surface (agent thread + DM)."""
    text = (text or "").strip()
    lowered = text.lower()
    if not text:
        say("Give me a topic and I'll find your colleague.")
        return
    if re.search(r"\b(help|how do(es)? (you|this|collabfinder) work|what can you do|hi|hello|hey)\b", lowered):
        say(
            "I find the right colleague for any topic by reading *public* "
            "channel activity — who authors threads, who answers questions, "
            "who gets replies. Ask me things like *who knows about GDPR "
            "compliance?* or just name a topic, e.g. *bigquery*. I'll show "
            "who to talk to and why. Curious what I know about you? Ask "
            "exactly that — or check my Home tab for your own profile and a "
            "one-click opt-out."
        )
        return
    if "know about me" in lowered or "privacy" in lowered:
        say(blocks=blocks.privacy_summary(os.environ.get("COLLABFINDER_CANVAS_URL")),
            text="CollabFinder privacy summary")
        return
    topic = re.sub(r"^(who (knows|should i talk to) about\s+)", "", text, flags=re.I).rstrip("?")
    result = query_experts(topic)
    say(blocks=blocks.expert_results(result), text=f"Best matches for {topic}")


@assistant.user_message
def answer(say, payload):
    respond_to_text(payload.get("text"), say)


app.use(assistant)


@app.event("message")
def handle_dm(event, say):
    """Plain DMs to the bot (Messages tab) get the same brain as the agent
    pane. Assistant-thread messages are consumed by the middleware above and
    never reach this listener."""
    if event.get("channel_type") != "im":
        return
    if event.get("bot_id") or event.get("subtype"):
        return
    respond_to_text(event.get("text"), say)


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


@app.action(re.compile(r"book_external_.*"))
def ack_book_external(ack):
    # URL buttons open the link client-side; Slack still expects an ack.
    ack()


@app.action(re.compile(r"draft_intro(_\d+)?"))
def handle_draft_intro(ack, body, respond, client):
    ack()
    expert = body["actions"][0]["value"]
    asker = _display_name(client, body["user"]["id"])
    draft = (
        f"Hi {expert} — {asker} here. CollabFinder pointed me your way: "
        f"I'm working on something that overlaps with what you've been discussing, "
        f"and I'd value 15 minutes of your time this week. Any slot that suits you?"
    )
    respond(
        text=f"Draft intro to {expert} (copy, tweak, send):\n>{draft}",
        response_type="ephemeral",
        replace_original=False,
    )


# --- App Home tab ------------------------------------------------------------
from .home import build_home_view  # noqa: E402


def _publish_home(client, user_id: str, search_topic: str | None = None):
    name = _display_name(client, user_id)
    client.views_publish(user_id=user_id,
                         view=build_home_view(name, search_topic, optout))


@app.event("app_home_opened")
def handle_home_opened(client, event):
    if event.get("tab") == "home":
        _publish_home(client, event["user"])


@app.action("home_search")
def handle_home_search(ack, client, body):
    ack()
    topic = body["actions"][0]["value"] or ""
    _publish_home(client, body["user"]["id"], topic.strip() or None)


@app.action("home_opt_out")
def handle_home_opt_out(ack, client, body):
    ack()
    optout.opt_out(_display_name(client, body["user"]["id"]))
    _publish_home(client, body["user"]["id"])


@app.action("home_opt_in")
def handle_home_opt_in(ack, client, body):
    ack()
    optout.opt_in(_display_name(client, body["user"]["id"]))
    _publish_home(client, body["user"]["id"])


def main() -> None:
    if os.environ.get("SLACK_APP_TOKEN"):
        from slack_bolt.adapter.socket_mode import SocketModeHandler
        SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
    else:
        app.start(port=int(os.environ.get("PORT", 3000)))


if __name__ == "__main__":
    main()
