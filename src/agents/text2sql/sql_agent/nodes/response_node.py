# src/agents/text2sql/sql_agent/nodes/response_node.py

from __future__ import annotations

import json

from pydantic import BaseModel, Field

from src.agents.core.call_llm import get_llm
from src.agents.text2sql.sql_agent.nodes.prompts import (
    RESPONSE_PROMPT,
)
from src.agents.text2sql.sql_agent.state import SQLAgentState
from src.core.events import emit


# ==========================================================
# Structured SQL Response
# ==========================================================

class SQLResponse(BaseModel):
    """
    Final user-facing response produced from verified SQL results.
    """

    answer: str = Field(
        description=(
            "A concise natural-language answer to the user's request "
            "grounded only in the provided SQL execution results."
        )
    )


# ==========================================================
# Response Node
# ==========================================================

async def response_node(
    state: SQLAgentState,
) -> dict:
    """
    Generate the final user-facing answer from accumulated SQL results.

    This node runs only after the SQL reasoner has determined that
    execution is complete.

    It does not generate, validate, or execute additional SQL.
    """

    # ======================================================
    # Preconditions
    # ======================================================

    if not state["execution_complete"]:
        raise ValueError(
            "Response generation attempted before SQL execution completed."
        )

    sql_results = state[
        "sql_results"
    ]

    if not sql_results:
        raise ValueError(
            "Response generation attempted without SQL results."
        )

    # ======================================================
    # Collect final SQL
    # ======================================================

    final_sql = [
        item["query"]
        for item in sql_results
    ]

    # ======================================================
    # Response generation started
    # ======================================================

    emit(
        component="response",
        event="generation_started",
        message="Generating final Text2SQL response.",
        data={
            "database_id": state["database_id"],
            "sql_count": len(
                final_sql
            ),
            "result_count": len(
                sql_results
            ),
            "retry_count": state[
                "retry_count"
            ],
        },
    )

    # ======================================================
    # Build response prompt
    # ======================================================

    prompt = RESPONSE_PROMPT.format(
        query=state["query"],
        sql_results=json.dumps(
            sql_results,
            indent=2,
            default=str,
        ),
    )

    # ======================================================
    # Generate final answer
    # ======================================================

    llm = get_llm()

    response_llm = llm.with_structured_output(
        SQLResponse
    )

    result = await response_llm.ainvoke(
        prompt
    )

    # ======================================================
    # Response completed
    # ======================================================

    emit(
        component="response",
        event="response_completed",
        message="Final Text2SQL response generated.",
        data={
            "database_id": state["database_id"],
            "sql_count": len(
                final_sql
            ),
            "result_count": len(
                sql_results
            ),
        },
    )

    # ======================================================
    # Finalize private agent state
    # ======================================================

    return {
        "final_sql": final_sql,

        "response": {
            "answer": result.answer,
            "sql": final_sql,
            "results": sql_results,
        },

        "error": None,
    }