# src/agents/web_search/web_agent/nodes/search_node.py

from __future__ import annotations

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

    decision = await search_llm.ainvoke(
        (
            "Convert the following user request into one concise "
            "web search query. Return only the structured output.\n\n"
            f"User request:\n{state['query']}"
        )
    )

    search_query = decision.search_query.strip()

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
        },
    )

    result = await web_search.ainvoke(
        {
            "query": search_query,
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
