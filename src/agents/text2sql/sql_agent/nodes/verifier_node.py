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

    Failed results are never promoted into accumulated
    SQL-loop evidence.
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

    It performs deterministic structural verification only.
    It does not decide whether the results semantically satisfy
    the user's request. That decision belongs to the active
    reasoning loop.

    When verification succeeds during the SQL loop, the verified
    execution batch is promoted into sql_results as accumulated
    evidence for the final response.
    """

    execution_results = state["execution_result"]

    # ======================================================
    # Validate active loop
    # ======================================================

    active_loop = state["active_loop"]

    if active_loop not in LOOP_MESSAGE_FIELDS:
        raise ValueError(
            f"Invalid active_loop for result verification: {active_loop}"
        )

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

    update = {
        "verified": True,
        "error": None,
    }

    # ======================================================
    # Promote verified SQL-loop evidence
    # ======================================================

    if active_loop == "sql":
        # sql_results uses an `add` reducer in SQLAgentState.
        # Returning only this verified batch causes LangGraph
        # to append it to previously verified SQL results.
        update["sql_results"] = execution_results

    return update