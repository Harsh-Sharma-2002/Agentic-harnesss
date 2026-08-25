# src/agents/text2sql/sql_agent/nodes/context_check_node.py

from __future__ import annotations

import json

from pydantic import BaseModel, Field

from src.agents.core.call_llm import get_llm
from src.agents.text2sql.sql_agent.nodes.prompts import CONTEXT_CHECK_PROMPT
from src.agents.text2sql.sql_agent.state import SQLAgentState


class ContextDecision(BaseModel):
    """
    Structured output returned by the context sufficiency checker.
    """

    sufficient: bool = Field(
        description=(
            "True if the currently known database context contains "
            "enough information to construct the required SQL query."
        )
    )

    missing_information: list[str] = Field(
        default_factory=list,
        description=(
            "Specific database information that still needs "
            "to be discovered."
        ),
    )


async def context_check_node(state: SQLAgentState) -> dict:
    """
    Determine whether the schema knowledge currently available
    in schema_context is sufficient to answer the user's query.

    If no cached schema knowledge exists, discovery is required
    immediately and the LLM call is skipped.
    """

    schema_context = state["schema_context"]

    # No persistent knowledge exists for this database yet.
    # Discovery is therefore required without asking the LLM.
    if not schema_context:
        return {
            "context_sufficient": False,
            "missing_information": [
                "Database schema is currently unknown."
            ],
        }

    prompt = CONTEXT_CHECK_PROMPT.format(
        query=state["query"],
        schema_context=json.dumps(
            schema_context,
            indent=2,
        ),
    )

    llm = get_llm()

    structured_llm = llm.with_structured_output(
        ContextDecision
    )

    decision = await structured_llm.ainvoke(prompt)

    return {
        "context_sufficient": decision.sufficient,
        "missing_information": decision.missing_information,
    }