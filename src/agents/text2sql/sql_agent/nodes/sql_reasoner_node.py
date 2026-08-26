# src/agents/text2sql/sql_agent/nodes/sql_reasoner_node.py

from __future__ import annotations

import json

from langchain_core.messages import AIMessage, SystemMessage
from pydantic import BaseModel, Field

from src.agents.core.call_llm import get_llm
from src.agents.text2sql.sql_agent.nodes.prompts import SQL_REASONER_PROMPT
from src.agents.text2sql.sql_agent.state import SQLAgentState


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

    llm = get_llm()

    sql_llm = llm.with_structured_output(
        SQLDecision
    )

    system_prompt = SQL_REASONER_PROMPT.format(
        query=state["query"],
        schema_context=json.dumps(
            state["schema_context"],
            indent=2,
        ),
        error=state["error"] or "None",
    )

    messages = [
        SystemMessage(content=system_prompt),
        *state["sql_messages"],
    ]

    result = await sql_llm.ainvoke(messages)

    # ======================================================
    # SQL execution complete
    # ======================================================

    if result.execution_complete:
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