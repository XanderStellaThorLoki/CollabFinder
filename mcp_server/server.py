"""CollabFinder MCP server.

Exposes one tool — query_experts(topic, limit) — over two surfaces:

  * MCP (streamable HTTP) at /mcp — what Slack Agent Builder connects to.
  * Plain REST at /query_experts — for the Bolt app, curl debugging, and demos.

Run locally:  uvicorn mcp_server.server:app --port 8080
Cloud Run:    scripts/deploy.sh (same entrypoint)
"""

from __future__ import annotations

from fastapi import FastAPI, Query

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
