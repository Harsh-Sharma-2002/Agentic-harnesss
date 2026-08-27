# src/agents/text2sql/sql_agent/graph.py

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .state import SQLAgentState

from .nodes import (
    context_check_node,
    discovery_node,
    executor_node,
    init_node,
    load_registry_node,
    response_node,
    result_verifier_node,
    sql_reasoner_node,
    sql_validator_node,
    update_registry_node,
)

from .decisions import (
    route_after_context_check,
    route_after_discovery,
    route_after_execution,
    route_after_sql_reasoner,
    route_after_validation,
    route_after_verification,
)


def build_sql_agent_graph():
    """
    Build and compile the private Text-to-SQL agent graph.

    The graph contains two reasoning loops:

    1. Discovery loop
       Discovers missing database knowledge and persists
       reusable schema information into the schema registry.

    2. SQL loop
       Generates and executes user-facing SQL until enough
       verified database evidence exists to answer the request.

    Both loops share the same validator, executor, and verifier.
    """

    graph = StateGraph(SQLAgentState)

    # ======================================================
    # Nodes
    # ======================================================

    graph.add_node(
        "init",
        init_node,
    )

    graph.add_node(
        "load_registry",
        load_registry_node,
    )

    graph.add_node(
        "context_check",
        context_check_node,
    )

    graph.add_node(
        "discovery",
        discovery_node,
    )

    graph.add_node(
        "validator",
        sql_validator_node,
    )

    graph.add_node(
        "executor",
        executor_node,
    )

    graph.add_node(
        "verifier",
        result_verifier_node,
    )

    graph.add_node(
        "update_registry",
        update_registry_node,
    )

    graph.add_node(
        "sql_reasoner",
        sql_reasoner_node,
    )

    graph.add_node(
        "response",
        response_node,
    )

    # ======================================================
    # Entry
    # ======================================================

    graph.add_edge(
        START,
        "init",
    )

    graph.add_edge(
        "init",
        "load_registry",
    )

    graph.add_edge(
        "load_registry",
        "context_check",
    )

    # ======================================================
    # Initial Context Routing
    # ======================================================

    graph.add_conditional_edges(
        "context_check",
        route_after_context_check,
        {
            "discovery": "discovery",
            "sql_reasoner": "sql_reasoner",
        },
    )

    # ======================================================
    # Discovery Loop
    # ======================================================

    graph.add_conditional_edges(
        "discovery",
        route_after_discovery,
        {
            "validator": "validator",
            "update_registry": "update_registry",
        },
    )

    # Once discovery is complete and its reusable knowledge
    # has been persisted, enter the actual SQL loop.
    graph.add_edge(
        "update_registry",
        "sql_reasoner",
    )

    # ======================================================
    # Shared Validator
    # ======================================================

    graph.add_conditional_edges(
        "validator",
        route_after_validation,
        {
            # Valid candidate SQL proceeds to execution.
            "executor": "executor",

            # Invalid SQL returns to whichever reasoner
            # generated the current candidate batch.
            "discovery": "discovery",
            "sql_reasoner": "sql_reasoner",
        },
    )

    # ======================================================
    # Shared Executor
    # ======================================================

    graph.add_conditional_edges(
        "executor",
        route_after_execution,
        {
            # Successful database execution must be verified.
            "verifier": "verifier",

            # Execution failures return to the active reasoner.
            "discovery": "discovery",
            "sql_reasoner": "sql_reasoner",
        },
    )

    # ======================================================
    # Shared Verifier
    # ======================================================

    graph.add_conditional_edges(
        "verifier",
        route_after_verification,
        {
            # Both successful verification and verification
            # failure return control to the active reasoner.
            #
            # On success, the reasoner determines semantic
            # sufficiency.
            #
            # On failure, the reasoner receives the error and
            # generates a repaired attempt.
            "discovery": "discovery",
            "sql_reasoner": "sql_reasoner",
        },
    )

    # ======================================================
    # SQL Reasoning Loop
    # ======================================================

    graph.add_conditional_edges(
        "sql_reasoner",
        route_after_sql_reasoner,
        {
            # More database information is required.
            "validator": "validator",

            # Enough verified SQL evidence exists.
            "response": "response",
        },
    )

    # ======================================================
    # Exit
    # ======================================================

    graph.add_edge(
        "response",
        END,
    )

    # ======================================================
    # Compile
    # ======================================================

    return graph.compile()


sql_agent_graph = build_sql_agent_graph()