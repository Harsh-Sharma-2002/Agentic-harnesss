# src/agents/text2sql/sql_agent/decisions.py

from __future__ import annotations

from typing import Literal

from src.agents.text2sql.sql_agent.state import SQLAgentState


# ==========================================================
# Initial Context Routing
# ==========================================================

def route_after_context_check(
    state: SQLAgentState,
) -> Literal[
    "discovery",
    "sql_reasoner",
]:
    """
    Decide whether database discovery is required.

    If the cached schema context already contains enough
    information for the user's request, discovery is skipped
    and execution enters the SQL reasoning loop directly.
    """

    if state["context_sufficient"]:
        return "sql_reasoner"

    return "discovery"


# ==========================================================
# Discovery Loop Routing
# ==========================================================

def route_after_discovery(
    state: SQLAgentState,
) -> Literal[
    "validator",
    "update_registry",
    "sql_reasoner",
]:
    """
    Decide what happens after one discovery reasoning step.

    Normal incomplete discovery produces candidate metadata SQL
    that must pass through the shared execution pipeline.

    Successfully completed discovery proceeds through registry
    update before entering the SQL reasoning loop.

    If the discovery iteration budget has been exhausted,
    discovery is stopped and execution proceeds directly to
    the SQL reasoner using the schema knowledge currently
    available.
    """

    # ======================================================
    # Discovery completed normally
    # ======================================================

    if state["discovery_complete"]:
        return "update_registry"

    # ======================================================
    # Discovery budget exhausted
    # ======================================================

    if state["discovery_exhausted"]:
        return "sql_reasoner"

    # ======================================================
    # More metadata discovery required
    # ======================================================

    return "validator"


# ==========================================================
# Shared Validator Routing
# ==========================================================

def route_after_validation(
    state: SQLAgentState,
) -> Literal[
    "executor",
    "discovery",
    "sql_reasoner",
]:
    """
    Route after shared SQL validation.

    Valid SQL proceeds to execution.

    Invalid SQL returns to whichever reasoning loop generated
    the candidate SQL so that the LLM can repair it.
    """

    if state["sql_valid"]:
        return "executor"

    return _active_reasoner(
        state
    )


# ==========================================================
# Shared Executor Routing
# ==========================================================

def route_after_execution(
    state: SQLAgentState,
) -> Literal[
    "verifier",
    "discovery",
    "sql_reasoner",
]:
    """
    Route after database execution.

    Successful execution proceeds to deterministic result
    verification.

    Failed execution returns to the active reasoning loop
    with the database error already stored in that loop's
    short-term memory.
    """

    if state["error"] is None:
        return "verifier"

    return _active_reasoner(
        state
    )


# ==========================================================
# Shared Verifier Routing
# ==========================================================

def route_after_verification(
    state: SQLAgentState,
) -> Literal[
    "discovery",
    "sql_reasoner",
]:
    """
    Return control to the reasoning loop that owns the
    shared execution pipeline.

    On verification success, the reasoner evaluates whether
    the returned information is semantically sufficient.

    On verification failure, the reasoner receives the
    verification error and can repair its next attempt.
    """

    return _active_reasoner(
        state
    )


# ==========================================================
# SQL Loop Routing
# ==========================================================

def route_after_sql_reasoner(
    state: SQLAgentState,
) -> Literal[
    "validator",
    "response",
]:
    """
    Decide whether the SQL reasoning loop requires another
    database execution or is ready to produce the final answer.
    """

    if state["execution_complete"]:
        return "response"

    return "validator"


# ==========================================================
# Internal Routing Helper
# ==========================================================

def _active_reasoner(
    state: SQLAgentState,
) -> Literal[
    "discovery",
    "sql_reasoner",
]:
    """
    Resolve the reasoning node that currently owns the
    shared validator -> executor -> verifier pipeline.
    """

    active_loop = state[
        "active_loop"
    ]

    if active_loop == "discovery":
        return "discovery"

    if active_loop == "sql":
        return "sql_reasoner"

    raise ValueError(
        f"Cannot route shared SQL pipeline with "
        f"active_loop={active_loop!r}."
    )