"""CollabFinder MCP server.

Exposes one tool — query_experts(topic, limit) — over two surfaces:

  * MCP (streamable HTTP) at /mcp — what Slack Agent Builder connects to.
  * Plain REST at /query_experts — for the Bolt app, curl debugging, and demos.

Run locally:  uvicorn mcp_server.server:app --port 8080
Cloud Run:    scripts/deploy.sh (same entrypoint)
"""

from __future__ import annotations

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

from .external import _load_directory
from .ranking import query_experts

app = FastAPI(title="CollabFinder", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/query_experts")
def query_experts_rest(
    topic: str = Query(..., min_length=2, description="What expertise are you looking for?"),
    limit: int = Query(3, ge=1, le=10),
) -> dict:
    """REST twin of the MCP tool. Same code path, same answer."""
    return query_experts(topic, limit)


@app.get("/market/demand")
def market_demand(field: str = Query(..., min_length=2)) -> dict:
    """Shown to experts at signup: recent query volume for their field, so
    bids can price demand rationally."""
    from .marketplace import demand
    return demand(field)


@app.post("/expert/{slug}/bid")
def change_bid(slug: str, percent: int = Query(..., ge=1, le=100),
               key: str = Query(...)) -> dict:
    """Expert self-serve bid adjustment — the marketplace lever. Clamped to
    the 10-50% platform band, effective immediately."""
    from fastapi import HTTPException
    from .marketplace import update_bid
    try:
        return update_bid(slug, percent, key)
    except PermissionError:
        raise HTTPException(status_code=403, detail="invalid bid key")
    except KeyError:
        raise HTTPException(status_code=404, detail="unknown expert")


@app.post("/booking/{slug}/close")
def close_booking(slug: str, slack_user_id: str = Query(...),
                  booking_ref: str = Query("")) -> dict:
    """Deal close: trigger the Rate-your-Expert-Experience flow. The buyer
    gets a rating card in Slack; the seller rates via POST /rating."""
    import os as _os
    from slack_sdk import WebClient
    client = WebClient(token=_os.environ["SLACK_BOT_TOKEN"])
    expert = next((e for e in _load_directory() if e.get("slug") == slug), None)
    if not expert:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="unknown expert")
    client.chat_postMessage(
        channel=slack_user_id,
        text=f"How was your consultation with {expert['name']}?",
        blocks=[
            {"type": "section", "text": {"type": "mrkdwn", "text":
                f"*Rate your Expert Experience*\nYour consultation with "
                f"*{expert['name']}* is closed. How was it?"}},
            {"type": "actions", "elements": [
                {"type": "button", "action_id": f"rate_expert_{n}",
                 "text": {"type": "plain_text", "text": "★" * n},
                 "value": f"{slug}|{n}|{booking_ref}"}
                for n in range(1, 6)
            ]},
        ],
    )
    return {"status": "rating_requested", "expert": slug}


@app.post("/rating")
def post_rating(expert: str = Query(...), stars: int = Query(..., ge=1, le=5),
                rater: str = Query(...), booking_ref: str = Query("")) -> dict:
    """Both sides of the deal rate at close; the seller (expert) posts here
    from their payout page, the buyer usually rates via the Slack card."""
    from .marketplace import add_rating
    return add_rating(expert, stars, rater, booking_ref)


@app.get("/book/{slug}", response_class=HTMLResponse)
def booking_page(slug: str, q: str = "") -> str:
    """CollabFinder's own booking page. All consultation payments run through
    the platform: client pays CollabFinder, commission is withheld, expert is
    paid out. Payment capture (Stripe) launches post-hackathon; this page
    records the booking request and shows the money flow."""
    expert = next((e for e in _load_directory() if e.get("slug") == slug), None)
    if not expert:
        return HTMLResponse("<h1>Expert not found</h1>", status_code=404)
    commission = expert.get("commission_percent", 15)
    return f"""
    <html><head><title>Book {expert['name']} — CollabFinder</title></head>
    <body style="font-family:Segoe UI,sans-serif;background:#1a1d29;color:#fff;
                 display:flex;justify-content:center;padding-top:60px">
      <div style="max-width:560px;background:#232738;border-radius:16px;padding:40px">
        <p style="color:#2eb67d;font-weight:700;margin:0">CollabFinder · Outside Experts</p>
        <h1 style="margin:8px 0">{expert['name']}</h1>
        <p style="color:#aab2c8;font-style:italic">{expert['field']}</p>
        <p>{expert['credentials']}</p>
        <p style="color:#f0c05a">🛡 Verified by CollabFinder · {expert.get('verified_on','')}</p>
        <hr style="border-color:#3d4257">
        <p style="font-size:22px;font-weight:700">{expert['rate']}</p>
        <p style="color:#aab2c8;font-size:14px">Booked and paid through CollabFinder.
           The platform retains a {commission}% commission; the expert receives the
           remainder. One invoice, one receipt, one place to resolve disputes.</p>
        <button style="background:#2eb67d;color:#fff;border:0;border-radius:8px;
                       padding:14px 28px;font-size:16px;font-weight:700;cursor:pointer"
                onclick="this.outerHTML='<p style=\\'color:#2eb67d;font-weight:700\\'>Booking request recorded — payment capture launches with our Stripe integration.</p>'">
          Proceed to payment
        </button>
        <p style="color:#6b7390;font-size:12px">Query: {q or "direct"}</p>
      </div>
    </body></html>
    """


# --- MCP surface (Agent Builder connects here) ------------------------------
try:
    from mcp.server.fastmcp import FastMCP

    _mcp = FastMCP("collabfinder", stateless_http=True)

    @_mcp.tool()
    def query_experts_tool(topic: str, limit: int = 3) -> dict:
        """Find colleagues with expertise on a topic, ranked, with reasoning.

        Args:
            topic: the expertise being sought, e.g. "GDPR compliance".
            limit: max number of people to return (default 3).

        Returns ranked people with a reason string and a confidence band
        (high/medium/low). Results only ever draw on public-channel activity;
        opted-out users never appear.
        """
        return query_experts(topic, limit)

    app.mount("/mcp", _mcp.streamable_http_app())
except ImportError:
    # mcp package not installed — REST surface still works; the MCP mount
    # simply doesn't exist. requirements.txt includes it for real deploys.
    pass
