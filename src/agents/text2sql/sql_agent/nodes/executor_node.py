# src/agents/text2sql/sql_agent/nodes/executor_node.py

from __future__ import annotations

import asyncio
import json

from langchain_core.messages import SystemMessage

from src.agents.text2sql.sql_agent.state import SQLAgentState
from src.agents.text2sql.sql_agent.tools import run_sql
from src.core.events import emit


# ==========================================================
# Loop Message Mapping
# ==========================================================

# Maps the active reasoning loop to its
# corresponding short-term memory.
LOOP_MESSAGE_FIELDS = {
    "discovery": "discovery_messages",
    "sql": "sql_messages",
}


# ==========================================================
# Executor Node
# ==========================================================

async def executor_node(
    state: SQLAgentState,
) -> dict:
    """
    Execute a validated batch of SQL queries.

    Execution logic is shared by both the discovery and SQL loops.

    active_loop is used only to route execution feedback into the
    appropriate short-term message history.

    Successful execution results are stored in execution_result as
    the latest batch. Promotion into accumulated sql_results happens
    only after deterministic verification succeeds.
    """

    candidate_queries = state[
        "candidate_sql"
    ]

    # ======================================================
    # Preconditions
    # ======================================================

    if not state["sql_valid"]:
        raise ValueError(
            "Executor received SQL that has not passed validation."
        )

    if not candidate_queries:
        raise ValueError(
            "Executor received an empty SQL batch."
        )

    active_loop = state[
        "active_loop"
    ]

    if active_loop not in LOOP_MESSAGE_FIELDS:
        raise ValueError(
            f"Invalid active_loop for SQL execution: {active_loop}"
        )

    message_field = LOOP_MESSAGE_FIELDS[
        active_loop
    ]

    # ======================================================
    # Execution started
    # ======================================================

    emit(
        component="executor",
        event="execution_started",
        message="Executing SQL query batch.",
        data={
            "active_loop": active_loop,
            "sql_queries": candidate_queries,
            "query_count": len(
                candidate_queries
            ),
            "retry_count": state[
                "retry_count"
            ],
        },
    )

    # ======================================================
    # Execute independent queries concurrently
    # ======================================================

    results = await asyncio.gather(
        *[
            run_sql.ainvoke(
                {
                    "query": query,
                }
            )
            for query in candidate_queries
        ]
    )

    # Preserve query -> result provenance.
    execution_results = [
        {
            "query": query,
            "result": result,
        }
        for query, result in zip(
            candidate_queries,
            results,
        )
    ]

    # ======================================================
    # Check for execution failures
    # ======================================================

    failed_queries = [
        item
        for item in execution_results
        if not item["result"]["success"]
    ]

    if failed_queries:
        error = "\n\n".join(
            (
                f"Query: {item['query']}\n"
                f"Error: {item['result']['error']}"
            )
            for item in failed_queries
        )

        # ==================================================
        # Execution failed
        # ==================================================

        emit(
            component="executor",
            event="execution_failed",
            message="SQL execution failed.",
            data={
                "active_loop": active_loop,
                "query_count": len(
                    candidate_queries
                ),
                "failed_query_count": len(
                    failed_queries
                ),
                "error": error,
                "retry_count": (
                    state["retry_count"] + 1
                ),
            },
        )

        return {
            # Preserve the latest attempted batch for
            # debugging and inspection.
            "execution_result": execution_results,

            "error": error,

            "retry_count": (
                state["retry_count"] + 1
            ),

            # Feed the execution failure back into the
            # reasoning loop that generated the SQL.
            message_field: [
                SystemMessage(
                    content=(
                        "SQL execution failed:\n"
                        f"{error}"
                    )
                )
            ],
        }

    # ======================================================
    # Execution succeeded
    # ======================================================

    row_counts = [
        item["result"]["row_count"]
        for item in execution_results
    ]

    total_rows = sum(
        row_counts
    )

    emit(
        component="executor",
        event="execution_completed",
        message="SQL execution completed.",
        data={
            "active_loop": active_loop,
            "query_count": len(
                candidate_queries
            ),
            "row_count": total_rows,
            "row_counts": row_counts,
        },
    )

    return {
        # Latest successfully executed batch.
        #
        # This has NOT yet been promoted into sql_results.
        # The verifier owns that responsibility.
        "execution_result": execution_results,

        "error": None,

        # The reasoning loop can already observe the database
        # result on its next iteration through its message
        # history. Verification determines whether the result
        # is accepted into accumulated final evidence.
        message_field: [
            SystemMessage(
                content=(
                    "SQL execution results:\n"
                    + json.dumps(
                        execution_results,
                        indent=2,
                        default=str,
                    )
                )
            )
        ],
    }