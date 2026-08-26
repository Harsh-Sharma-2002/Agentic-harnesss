# src/agents/text2sql/sql_agent/nodes/executor_node.py

from __future__ import annotations

import asyncio
import json

from langchain_core.messages import SystemMessage

from src.agents.text2sql.sql_agent.state import SQLAgentState
from src.agents.text2sql.sql_agent.tools import run_sql


# Maps the active reasoning loop to its
# corresponding short-term memory.
LOOP_MESSAGE_FIELDS = {
    "discovery": "discovery_messages",
    "sql": "sql_messages",
}


async def executor_node(
    state: SQLAgentState,
) -> dict:
    """
    Execute a validated batch of SQL queries.

    Execution logic is shared by both the discovery and SQL loops.

    active_loop is used only to:
    1. Route execution feedback into the correct short-term memory.
    2. Accumulate successful user-facing SQL results when the
       active loop is the SQL loop.
    """

    candidate_queries = state["candidate_sql"]

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

    active_loop = state["active_loop"]

    if active_loop not in LOOP_MESSAGE_FIELDS:
        raise ValueError(
            f"Invalid active_loop for SQL execution: {active_loop}"
        )

    message_field = LOOP_MESSAGE_FIELDS[active_loop]

    # ======================================================
    # Execute independent queries concurrently
    # ======================================================

    results = await asyncio.gather(
        *[
            run_sql.ainvoke({
                "query": query,
            })
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

        return {
            # Latest batch is still preserved for debugging.
            "execution_result": execution_results,

            "error": error,
            "retry_count": state["retry_count"] + 1,

            # Failure feedback goes only to the memory of
            # the reasoning loop that produced the SQL.
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

    update = {
        # Shared field containing only the latest batch.
        "execution_result": execution_results,

        "error": None,

        # Successful database observation is returned to
        # whichever reasoning loop generated the SQL.
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

    # ======================================================
    # Accumulate final SQL-loop evidence
    # ======================================================

    if active_loop == "sql":
        # sql_results uses an `add` reducer in SQLAgentState,
        # so LangGraph appends this batch to previous batches.
        #
        # Discovery results are intentionally excluded.
        update["sql_results"] = execution_results

    return update