# src/agents/text2sql/sql_agent/state.py

from __future__ import annotations



from operator import add
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

    # Cached database knowledge relevant to this request.
    schema_context: dict[str, Any]

    # Result of the initial registry-context sufficiency check.
    context_sufficient: bool

    # Database information missing from the cached context.
    missing_information: list[str]

    # Whether the discovery reasoner believes enough schema
    # information has been collected.
    discovery_complete: bool

    # Newly discovered reusable knowledge waiting to be
    # persisted into the schema registry.
    schema_update: dict[str, Any]

    # ======================================================
    # SQL Loop
    # ======================================================

    sql_messages: Annotated[
        list[AnyMessage],
        add_messages,
    ]

    # Whether the SQL reasoner believes the accumulated
    # execution results are sufficient to answer the user.
    execution_complete: bool

    # Successful SQL-loop results accumulated across
    # multiple reasoning/execution iterations.
    #
    # Unlike execution_result, this does not contain
    # discovery-query results.
    sql_results: Annotated[
    list[dict[str, Any]],
    add,
    ]

    # ======================================================
    # Shared SQL Execution Pipeline
    # ======================================================

    # Identifies which reasoning loop currently owns the
    # shared validator -> executor -> verifier pipeline.
    active_loop: Literal[
        "discovery",
        "sql",
    ] | None

    # SQL batch currently proposed by the active reasoning loop.
    candidate_sql: list[str]

    # Whether candidate_sql passed the shared validator.
    sql_valid: bool

    # Final SQL statements associated with the completed
    # user-facing SQL execution.
    final_sql: list[str]

    # Results from the latest execution batch.
    #
    # This field is shared by discovery and SQL execution.
    # SQL-loop results are additionally accumulated in sql_results.
    execution_result: list[dict[str, Any]]

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

    # Whether the latest execution_result passed the
    # deterministic result verifier.
    verified: bool

    # ======================================================
    # Output
    # ======================================================

    response: dict[str, Any] | None

    # Records eventually exposed to the GlobalState
    # for debugging and observability.
    execution_records: list[dict[str, Any]]