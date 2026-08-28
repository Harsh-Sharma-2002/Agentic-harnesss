# src/agents/web_search/web_agent/nodes/response_node.py

from __future__ import annotations

import json

from src.agents.core.call_llm import get_llm
from src.core.events import emit

from ..state import WebAgentState


async def response_node(
    state: WebAgentState,
) -> dict:
    """
    Generate the final user-facing answer from web search results.

    This node performs no additional searches. It synthesizes
    the results already retrieved by the search node.
    """

    # ======================================================
    # Preconditions
    # ======================================================

    if state["error"]:
        raise ValueError(
            f"Cannot generate web response after search failure: "
            f"{state['error']}"
        )

    search_results = state["search_results"]

    if not search_results:
        raise ValueError(
            "Cannot generate web response without search results."
        )

    # ======================================================
    # Response generation started
    # ======================================================

    emit(
        component="web_search",
        event="response_generation_started",
        message="Generating answer from web search results.",
    )

    # ======================================================
    # Build prompt
    # ======================================================

    prompt = f"""
You are the response component of a web search agent.

Answer the user's request using only the provided web search results.

User request:
{state["query"]}

Web search results:
{json.dumps(search_results, indent=2, default=str)}

Rules:
1. Answer the user's request directly.
2. Use only information supported by the search results.
3. Do not invent facts that are not present in the results.
4. When useful, mention the source associated with a claim.
5. If the search results do not contain enough information, say so.
6. Keep the answer concise unless the request requires detail.
7. Return only the natural-language answer.
"""

    # ======================================================
    # Generate response
    # ======================================================

    llm = get_llm()

    result = await llm.ainvoke(prompt)

    answer = str(result.content).strip()

    if not answer:
        raise ValueError(
            "Web response LLM returned an empty answer."
        )

    # ======================================================
    # Response completed
    # ======================================================

    emit(
        component="web_search",
        event="response_completed",
        message="Web search response generated.",
    )

    # ======================================================
    # Finalize private state
    # ======================================================

    return {
        "response": {
            "answer": answer,
            "search_query": state["search_query"],
            "sources": search_results,
        },
        "error": None,
    }
