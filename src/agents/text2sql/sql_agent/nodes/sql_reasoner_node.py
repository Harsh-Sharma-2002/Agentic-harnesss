# src/agents/text2sql/sql_agent/nodes/sql_reasoner_node.py

from __future__ import annotations

import json

from langchain_core.messages import AIMessage, SystemMessage
from pydantic import BaseModel, Field

from src.agents.core.call_llm import get_llm
from src.agents.text2sql.sql_agent.nodes.prompts import SQL_REASONER_PROMPT
from src.agents.text2sql.sql_agent.state import SQLAgentState


class SQLQueryBatch(BaseModel):
    """
    Structured SQL proposal produced by the SQL reasoner.
    """

    queries: list[str] = Field(
        description=(
            "One or more independent read-only PostgreSQL queries "
            "required to answer the user's request."
        )
    )


async def sql_reasoner_node(
    state: SQLAgentState,
) -> dict:
    """
    Generate the SQL required to answer the user's request.

    The node reasons over the known schema context, previous SQL
    attempts, execution results, and errors.

    It does not validate or execute SQL itself.
    """

    llm = get_llm()

    sql_llm = llm.with_structured_output(
        SQLQueryBatch
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

    return {
        "active_loop": "sql",
        "candidate_sql": result.queries,
        "sql_valid": False,
        "verified": False,
        "error": None,
        "sql_messages": [
            AIMessage(
                content=json.dumps(
                    {
                        "queries": result.queries,
                    },
                    indent=2,
                )
            )
        ],
    }
