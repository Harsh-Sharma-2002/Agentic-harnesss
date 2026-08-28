# src/agents/web_search/web_agent/graph.py

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .nodes import (
    init_node,
    response_node,
    search_node,
)
from .state import WebAgentState


def build_web_agent_graph():
    """
    Build and compile the private Web Search Agent graph.

    The placeholder v1 agent performs a single search pass:

    init -> search -> response

    No ReAct loop, retries, or repeated searches are performed.
    """

    graph = StateGraph(WebAgentState)

    # ======================================================
    # Nodes
    # ======================================================

    graph.add_node(
        "init",
        init_node,
    )

    graph.add_node(
        "search",
        search_node,
    )

    graph.add_node(
        "response",
        response_node,
    )

    # ======================================================
    # Flow
    # ======================================================

    graph.add_edge(
        START,
        "init",
    )

    graph.add_edge(
        "init",
        "search",
    )

    graph.add_edge(
        "search",
        "response",
    )

    graph.add_edge(
        "response",
        END,
    )

    # ======================================================
    # Compile
    # ======================================================

    return graph.compile()


web_agent_graph = build_web_agent_graph()
