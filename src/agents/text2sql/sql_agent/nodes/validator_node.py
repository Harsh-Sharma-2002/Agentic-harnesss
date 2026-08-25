# src/agents/text2sql/sql_agent/nodes/validator_node.py

from __future__ import annotations

from langchain_core.messages import HumanMessage

from src.agents.text2sql.sql_agent.state import SQLAgentState


FORBIDDEN_KEYWORDS = {
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "truncate",
    "create",
    "grant",
    "revoke",
}


# Maps the currently active reasoning loop to its
# corresponding LangGraph short-term memory.
LOOP_MESSAGE_FIELDS = {
    "discovery": "discovery_messages",
    "sql": "sql_messages",
}


def _validation_failure(
    state: SQLAgentState,
    error: str,
) -> dict:
    """
    Build a validation failure update.

    Validation remains shared between both loops.
    active_loop is used only to place feedback into
    the correct short-term memory.
    """

    active_loop = state["active_loop"]

    if active_loop not in LOOP_MESSAGE_FIELDS:
        raise ValueError(
            f"Invalid active_loop for SQL validation: {active_loop}"
        )

    message_field = LOOP_MESSAGE_FIELDS[active_loop]

    return {
        "sql_valid": False,
        "error": error,
        "retry_count": state["retry_count"] + 1,
        message_field: [
            HumanMessage(
                content=f"SQL validation failed: {error}"
            )
        ],
    }


def _validate_single_query(
    query: str,
    index: int,
) -> str | None:
    """
    Validate one SQL statement.

    Returns an error message if validation fails,
    otherwise returns None.
    """

    if not query or not query.strip():
        return f"Query {index} is empty."

    normalized_sql = query.strip().lower()

    # ------------------------------------------------------
    # Read-only queries only
    # ------------------------------------------------------

    if not normalized_sql.startswith("select"):
        return (
            f"Query {index} is not read-only. "
            "Only SELECT queries are allowed."
        )

    # ------------------------------------------------------
    # Each list item must contain exactly one statement
    # ------------------------------------------------------

    sql_without_trailing_semicolon = (
        normalized_sql.rstrip(";").strip()
    )

    if ";" in sql_without_trailing_semicolon:
        return (
            f"Query {index} contains multiple SQL statements. "
            "Return each statement as a separate query."
        )

    # ------------------------------------------------------
    # Reject destructive operations
    # ------------------------------------------------------

    tokens = set(
        sql_without_trailing_semicolon
        .replace("(", " ")
        .replace(")", " ")
        .replace(",", " ")
        .split()
    )

    forbidden = tokens.intersection(
        FORBIDDEN_KEYWORDS
    )

    if forbidden:
        return (
            f"Query {index} contains forbidden SQL operations: "
            + ", ".join(sorted(forbidden))
        )

    return None


async def sql_validator_node(
    state: SQLAgentState,
) -> dict:
    """
    Validate a batch of candidate SQL queries before execution.

    This node is shared by both the discovery and SQL reasoning
    loops and does not contain loop-specific validation logic.

    Every query in candidate_sql must pass validation before
    any query in the batch is allowed to execute.
    """

    candidate_queries = state["candidate_sql"]

    # ======================================================
    # Batch must contain at least one query
    # ======================================================

    if not candidate_queries:
        return _validation_failure(
            state,
            "No SQL queries were provided for validation.",
        )

    # ======================================================
    # Validate every query in the batch
    # ======================================================

    for index, query in enumerate(
        candidate_queries,
        start=1,
    ):
        error = _validate_single_query(
            query=query,
            index=index,
        )

        if error:
            return _validation_failure(
                state,
                error,
            )

    # ======================================================
    # Entire batch passed validation
    # ======================================================

    return {
        "sql_valid": True,
        "error": None,
    }