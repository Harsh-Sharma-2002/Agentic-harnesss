# src/agents/text2sql/sql_agent/state.py

from __future__ import annotations

from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class SQLAgentState(TypedDict):
    """
    Private state for one Text2SQL Agent invocation.

    Discovery and SQL execution maintain separate short-term
    memories. Persistent database knowledge lives in the
    schema registry, not in this state.
    """

    # ======================================================
    # Input
    # ======================================================

    query: str
    database_id: str

    # ======================================================
    # Discovery Loop
    # ======================================================

    discovery_messages: Annotated[
        list[AnyMessage],
        add_messages,
    ]

    # Cached + newly discovered database knowledge
    # relevant to the current request.
    schema_context: dict[str, Any]

    context_sufficient: bool

    missing_information: list[str]

    # Whether the discovery reasoner believes enough
# schema information has been collected.
    discovery_complete: bool

# Newly discovered reusable knowledge waiting
# to be persisted into the schema registry.
    schema_update: dict[str, Any]

    # ======================================================
    # SQL Loop
    # ======================================================

    sql_messages: Annotated[
        list[AnyMessage],
        add_messages,
    ]

    # ======================================================
    # Shared SQL Execution
    # ======================================================

    # Identifies which reasoning loop produced candidate_sql.
    # Used for routing after validation/execution failures.
    active_loop: Literal[
        "discovery",
        "sql",
    ] | None

    # SQL currently proposed by either reasoning loop.
    candidate_sql: list[str] 
    sql_valid: bool

    # Final validated SQL used to answer the user.
    # Discovery queries are never stored here.
    final_sql: list[str] 

    # Latest database execution result.
    execution_result: list[dict[str,Any]] 

    # ======================================================
    # Validation / Retry
    # ======================================================

    # Latest actionable validation, execution, or
    # verification error.
    error: str | None

    retry_count: int

    # ======================================================
    # Verification
    # ======================================================

    verified: bool

    # ======================================================
    # Output
    # ======================================================

    response: dict[str, Any] | None

    # Records eventually exposed to the GlobalState
    # for debugging and observability.
    execution_records: list[dict[str, Any]]