# src/agents/web_search/web_agent/nodes/search_node.py

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from src.agents.core.call_llm import get_llm
from src.core.events import emit

from ..state import WebAgentState
from ..tools import web_search


class SearchDecision(BaseModel):
    """
    Structured search request generated from the user's query.
    """

    search_query: str = Field(
        description=(
            "A concise web search query optimized to retrieve "
            "information needed to answer the user's request."
        )
    )

    timelimit: Literal["d", "w", "m", "y"] | None = Field(
        default="y",
        description=(
            "How far back search results may go, relative to "
            "today. Use 'd' for breaking/today's news, 'w' for "
            "this week, 'm' for recent developments, 'y' for "
            "anything current but not urgent. Use null only when "
            "the request is about timeless or historical "
            "information (definitions, how something works, "
            "events with a fixed past date) where recency does "
            "not matter. When unsure, prefer 'y' over null."
        ),
    )


async def search_node(
    state: WebAgentState,
) -> dict:
    """
    Generate one web search query and execute it.

    This is intentionally a single-pass search node.
    It does not perform a ReAct loop or decide whether
    additional searches are required.
    """

    # ======================================================
    # Generate search query
    # ======================================================

    emit(
        component="web_search",
        event="query_generation_started",
        message="Generating web search query.",
    )

    llm = get_llm()

    search_llm = llm.with_structured_output(
        SearchDecision
    )

    today: date = datetime.now(timezone.utc).date()

    decision = await search_llm.ainvoke(
        (
            f"Today's date is {today.isoformat()}. Convert the "
            "following user request into one concise web search "
            "query, and choose how far back results may go. "
            "Return only the structured output.\n\n"
            f"User request:\n{state['query']}"
        )
    )

    search_query = decision.search_query.strip()
    timelimit = decision.timelimit

    if not search_query:
        raise ValueError(
            "Web search query generation returned an empty query."
        )

    emit(
        component="web_search",
        event="query_generated",
        message="Web search query generated.",
        data={
            "query": search_query,
            "timelimit": timelimit,
        },
    )

    # ======================================================
    # Execute search
    # ======================================================

    emit(
        component="web_search",
        event="search_started",
        message="Searching the web.",
        data={
            "query": search_query,
            "timelimit": timelimit,
        },
    )

    result = await web_search.ainvoke(
        {
            "query": search_query,
            "timelimit": timelimit,
        }
    )

    # ======================================================
    # Search failure
    # ======================================================

    if not result["success"]:
        error = result["error"] or "Unknown web search error."

        emit(
            component="web_search",
            event="search_failed",
            message="Web search failed.",
            data={
                "query": search_query,
                "error": error,
            },
        )

        return {
            "search_query": search_query,
            "search_results": [],
            "error": error,
        }

    # ======================================================
    # Search succeeded
    # ======================================================

    search_results = result["results"]

    emit(
        component="web_search",
        event="search_completed",
        message="Web search completed.",
        data={
            "query": search_query,
            "row_count": len(search_results),
        },
    )

    return {
        "search_query": search_query,
        "search_results": search_results,
        "error": None,
    }
