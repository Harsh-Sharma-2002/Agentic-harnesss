# src/agents/text2sql/sql_agent/nodes/context_check.py

from __future__ import annotations

import json

from pydantic import BaseModel, Field

from src.agents.core.call_llm import get_llm
from src.agents.text2sql.sql_agent.nodes.prompts import (
    CONTEXT_CHECK_PROMPT,
)
from src.agents.text2sql.sql_agent.state import SQLAgentState
from src.core.events import emit


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


async def context_check_node(
    state: SQLAgentState,
) -> dict:
    """
    Determine whether the schema knowledge currently available
    in schema_context is sufficient to answer the user's query.

    If no cached schema knowledge exists, discovery is required
    immediately and the LLM call is skipped.
    """

    schema_context = state["schema_context"]

    # ======================================================
    # Context check started
    # ======================================================

    emit(
        component="context_check",
        event="check_started",
        message="Checking whether cached schema context is sufficient.",
        data={
            "database_id": state["database_id"],
        },
    )

    # ======================================================
    # No cached context
    # ======================================================

    if not schema_context:
        missing_information = [
            "Database schema is currently unknown."
        ]

        emit(
            component="context_check",
            event="discovery_required",
            message="No cached schema context available. Discovery required.",
            data={
                "missing_information": missing_information,
            },
        )

        return {
            "context_sufficient": False,
            "missing_information": missing_information,
        }

    # ======================================================
    # Ask LLM whether cached context is sufficient
    # ======================================================

    emit(
        component="context_check",
        event="llm_check_started",
        message="Evaluating cached schema knowledge.",
        data={
            "database_id": state["database_id"],
        },
    )

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

    decision = await structured_llm.ainvoke(
        prompt
    )

    # ======================================================
    # Cached context is sufficient
    # ======================================================

    if decision.sufficient:
        emit(
            component="context_check",
            event="context_sufficient",
            message=(
                "Cached schema context is sufficient. "
                "Discovery will be skipped."
            ),
        )

        return {
            "context_sufficient": True,
            "missing_information": [],
        }

    # ======================================================
    # Additional discovery required
    # ======================================================

    emit(
        component="context_check",
        event="discovery_required",
        message="Cached schema context is incomplete. Discovery required.",
        data={
            "missing_information": decision.missing_information,
        },
    )

    return {
        "context_sufficient": False,
        "missing_information": decision.missing_information,
    }