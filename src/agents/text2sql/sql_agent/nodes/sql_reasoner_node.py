# src/agents/text2sql/sql_agent/nodes/sql_reasoner_node.py

from __future__ import annotations

import json

from langchain_core.messages import AIMessage, SystemMessage
from pydantic import BaseModel, Field

from src.agents.core.call_llm import get_llm
from src.agents.text2sql.sql_agent.nodes.prompts import (
    SQL_REASONER_PROMPT,
)
from src.agents.text2sql.sql_agent.state import SQLAgentState
from src.core.events import emit


# ==========================================================
# Structured SQL Decision
# ==========================================================

class SQLDecision(BaseModel):
    """
    Structured decision produced by the SQL reasoner.
    """

    execution_complete: bool = Field(
        description=(
            "True when the SQL execution results already available "
            "contain enough information to answer the user's request."
        )
    )

    queries: list[str] = Field(
        default_factory=list,
        description=(
            "One or more independent read-only PostgreSQL queries "
            "required for the next execution step. Must be empty "
            "when execution_complete is true."
        ),
    )


# ==========================================================
# SQL Reasoner Node
# ==========================================================

async def sql_reasoner_node(
    state: SQLAgentState,
) -> dict:
    """
    Control the SQL reasoning loop.

    The node examines the known database schema, previous SQL attempts,
    execution results, and errors and decides whether:

    1. More database information is required to answer the user, in
       which case it generates the next batch of SQL queries.

    2. The existing SQL execution results are sufficient to answer the
       user, in which case it marks SQL execution as complete.

    This node does not validate, execute, or verify SQL itself.
    """

    # ======================================================
    # SQL reasoning started
    # ======================================================

    emit(
        component="sql_reasoner",
        event="reasoning_started",
        message="Evaluating database evidence and determining the next SQL action.",
        data={
            "database_id": state["database_id"],
            "verified_result_count": len(
                state["sql_results"]
            ),
            "retry_count": state[
                "retry_count"
            ],
            "has_error": bool(
                state["error"]
            ),
        },
    )

    # ======================================================
    # Prepare structured LLM
    # ======================================================

    llm = get_llm()

    sql_llm = llm.with_structured_output(
        SQLDecision
    )

    # ======================================================
    # Build SQL reasoning prompt
    # ======================================================

    system_prompt = SQL_REASONER_PROMPT.format(
        query=state["query"],
        schema_context=json.dumps(
            state["schema_context"],
            indent=2,
        ),
        error=state["error"] or "None",
    )

    messages = [
        SystemMessage(
            content=system_prompt
        ),
        *state["sql_messages"],
    ]

    # ======================================================
    # Ask SQL reasoner
    # ======================================================

    result = await sql_llm.ainvoke(
        messages
    )

    # ======================================================
    # SQL execution complete
    # ======================================================

    if result.execution_complete:

        emit(
            component="sql_reasoner",
            event="execution_complete",
            message=(
                "Sufficient verified database evidence "
                "has been collected."
            ),
            data={
                "database_id": state[
                    "database_id"
                ],
                "verified_result_count": len(
                    state["sql_results"]
                ),
                "retry_count": state[
                    "retry_count"
                ],
            },
        )

        return {
            "active_loop": "sql",
            "execution_complete": True,
            "candidate_sql": [],
            "sql_valid": False,
            "verified": True,
            "error": None,
            "sql_messages": [
                AIMessage(
                    content=json.dumps(
                        {
                            "execution_complete": True,
                            "queries": [],
                        },
                        indent=2,
                    )
                )
            ],
        }

    # ======================================================
    # More SQL execution required
    # ======================================================

    emit(
        component="sql_reasoner",
        event="queries_generated",
        message=(
            "Additional database execution is required."
        ),
        data={
            "database_id": state[
                "database_id"
            ],
            "sql_queries": result.queries,
            "query_count": len(
                result.queries
            ),
            "retry_count": state[
                "retry_count"
            ],
        },
    )

    return {
        "active_loop": "sql",
        "execution_complete": False,
        "candidate_sql": result.queries,

        # New SQL has not passed through the shared
        # execution pipeline yet.
        "sql_valid": False,
        "verified": False,

        "sql_messages": [
            AIMessage(
                content=json.dumps(
                    {
                        "execution_complete": False,
                        "queries": result.queries,
                    },
                    indent=2,
                )
            )
        ],
    }