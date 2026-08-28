# src/agents/text2sql/sql_agent/graph.py

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .state import SQLAgentState

from .nodes import (
    context_check_node,
    discovery_exit_node,
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

       Discovery is bounded by a fixed reasoning budget.

       If that budget is exhausted, execution passes through
       a dedicated discovery-exit transition before entering
       the SQL reasoning loop.

    2. SQL loop

       Generates and executes user-facing SQL until enough
       verified database evidence exists to answer the request.

    Both loops share the same validator, executor, and verifier.
    """

    graph = StateGraph(
        SQLAgentState
    )

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
        "discovery_exit",
        discovery_exit_node,
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
            # Cached schema is incomplete.
            "discovery": "discovery",

            # Cached schema is already sufficient.
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
            # More metadata discovery is required.
            "validator": "validator",

            # Discovery completed normally.
            # Persist reusable knowledge before entering
            # the SQL reasoning loop.
            "update_registry": "update_registry",

            # Discovery budget was exhausted.
            # Cleanly transition out of discovery without
            # persisting incomplete schema knowledge.
            "discovery_exit": "discovery_exit",
        },
    )

    # ======================================================
    # Discovery -> SQL Transitions
    # ======================================================

    # Normal discovery completion:
    #
    # discovery
    #     -> update_registry
    #     -> sql_reasoner

    graph.add_edge(
        "update_registry",
        "sql_reasoner",
    )

    # Exhausted discovery:
    #
    # discovery
    #     -> discovery_exit
    #     -> sql_reasoner

    graph.add_edge(
        "discovery_exit",
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
            # Successful verification returns control to the
            # active reasoner so it can determine semantic
            # sufficiency.
            #
            # Verification failures also return to the active
            # reasoner with actionable feedback.
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
            # Additional database execution is required.
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