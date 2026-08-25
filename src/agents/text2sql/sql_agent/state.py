from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class SQLAgentState(TypedDict):
    """
    Private state for one Text2SQL Agent invocation.

    Discovery and SQL execution maintain separate short-term
    memories. Persistent database knowledge lives in the
    SchemaRegistry, not in this state.
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

    # Cached + newly discovered schema information relevant
    # to this request.
    schema_context: dict[str, Any]

    context_sufficient: bool

    missing_information: list[str]

    # ======================================================
    # SQL Loop
    # ======================================================

    sql_messages: Annotated[
        list[AnyMessage],
        add_messages,
    ]

    generated_sql: str | None

    execution_result: Any | None

    # Latest actionable failure.
    # Used as repair context by the SQL loop.
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

    execution_records: list[dict[str, Any]]