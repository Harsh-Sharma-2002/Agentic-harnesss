# src/agents/web_search/web_agent/nodes/init_node.py

from __future__ import annotations

from src.core.events import emit

from ..state import WebAgentState


async def init_node(
    state: WebAgentState,
) -> dict:
    """
    Initialize request-scoped Web Search Agent state.

    The original query is preserved while all internal search
    and output fields are reset for the current invocation.
    """

    # ======================================================
    # Emit initialization event
    # ======================================================

    emit(
        component="web_search",
        event="request_initialized",
        message="Web search request initialized.",
        data={
            "query": state["query"],
        },
    )

    # ======================================================
    # Initialize private state
    # ======================================================

    return {
        "search_query": None,
        "search_results": [],
        "response": None,
        "error": None,
        "execution_records": [],
    }
