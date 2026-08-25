# src/agents/text2sql/sql_agent/nodes/verifier_node.py

from __future__ import annotations

from langchain_core.messages import SystemMessage

from src.agents.text2sql.sql_agent.state import SQLAgentState


# Maps the active reasoning loop to its
# corresponding short-term memory.
LOOP_MESSAGE_FIELDS = {
    "discovery": "discovery_messages",
    "sql": "sql_messages",
}


def _verification_failure(
    state: SQLAgentState,
    error: str,
) -> dict:
    """
    Build a verification failure update.

    Verification logic is shared between both loops.
    active_loop is used only to place feedback into
    the correct short-term memory.
    """

    active_loop = state["active_loop"]

    if active_loop not in LOOP_MESSAGE_FIELDS:
        raise ValueError(
            f"Invalid active_loop for result verification: {active_loop}"
        )

    message_field = LOOP_MESSAGE_FIELDS[active_loop]

    return {
        "verified": False,
        "error": error,
        "retry_count": state["retry_count"] + 1,
        message_field: [
            SystemMessage(
                content=f"SQL result verification failed: {error}"
            )
        ],
    }


async def result_verifier_node(
    state: SQLAgentState,
) -> dict:
    """
    Verify that SQL execution produced structurally valid results.

    This node is shared by both the discovery and SQL loops.

    It performs deterministic verification only. It does not decide
    whether the result semantically satisfies the user's request or
    whether additional discovery is required. Those decisions belong
    to the reasoning loops.
    """

    execution_results = state["execution_result"]

    # ======================================================
    # Results must exist
    # ======================================================

    if not execution_results:
        return _verification_failure(
            state,
            "No SQL execution results were produced.",
        )

    # ======================================================
    # Every executed query must have a result object
    # ======================================================

    for index, item in enumerate(
        execution_results,
        start=1,
    ):
        if "query" not in item:
            return _verification_failure(
                state,
                f"Execution result {index} is missing query provenance.",
            )

        if "result" not in item:
            return _verification_failure(
                state,
                f"Execution result {index} is missing its result payload.",
            )

        result = item["result"]

        # ==================================================
        # Execution must have succeeded
        # ==================================================

        if not result.get("success", False):
            return _verification_failure(
                state,
                (
                    f"Query {index} did not execute successfully: "
                    f"{result.get('error', 'Unknown database error')}"
                ),
            )

        # ==================================================
        # Required result structure must exist
        # ==================================================

        if "columns" not in result:
            return _verification_failure(
                state,
                f"Query {index} result is missing column metadata.",
            )

        if "rows" not in result:
            return _verification_failure(
                state,
                f"Query {index} result is missing rows.",
            )

        if "row_count" not in result:
            return _verification_failure(
                state,
                f"Query {index} result is missing row_count.",
            )

        # ==================================================
        # Result metadata must be internally consistent
        # ==================================================

        if result["row_count"] != len(result["rows"]):
            return _verification_failure(
                state,
                (
                    f"Query {index} returned inconsistent result metadata: "
                    "row_count does not match the number of rows."
                ),
            )

    # ======================================================
    # Verification passed
    # ======================================================

    return {
        "verified": True,
        "error": None,
    }
