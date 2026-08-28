# src/agents/web_search/web_agent/state.py

from __future__ import annotations

from typing import Any, TypedDict


class WebAgentState(TypedDict):
    """
    Private state for one Web Search Agent invocation.

    The v1 web agent performs a single web search operation
    and produces a final response from the retrieved results.

    Search/reasoning state remains private to this agent.
    """

    # ======================================================
    # Input
    # ======================================================

    # Original user request.
    query: str

    # ======================================================
    # Search
    # ======================================================

    # Search query sent to the web search tool.
    #
    # For v1 this may simply be derived once from the
    # original user request.
    search_query: str | None

    # Raw results returned by the web search tool.
    search_results: list[dict[str, Any]]

    # ======================================================
    # Output
    # ======================================================

    # Final structured result returned by the private
    # web-search graph.
    response: dict[str, Any] | None

    # Latest actionable error, if execution fails.
    error: str | None

    # Records eventually exposed to GlobalState for
    # debugging and observability.
    execution_records: list[dict[str, Any]]