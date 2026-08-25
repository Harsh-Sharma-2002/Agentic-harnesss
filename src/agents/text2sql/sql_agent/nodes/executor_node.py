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
    active_loop is used only to route execution feedback into the
    appropriate short-term message history.
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

    # Keep each result associated with the SQL
    # statement that produced it.
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
            "execution_result": execution_results,
            "error": error,
            "retry_count": state["retry_count"] + 1,
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

    return {
        "execution_result": execution_results,
        "error": None,
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