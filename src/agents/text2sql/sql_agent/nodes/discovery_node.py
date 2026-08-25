# src/agents/text2sql/sql_agent/nodes/discovery_node.py

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AIMessage, SystemMessage
from pydantic import BaseModel, Field

from src.agents.core.call_llm import get_llm
from src.agents.text2sql.sql_agent.nodes.prompts import DISCOVERY_PROMPT
from src.agents.text2sql.sql_agent.state import SQLAgentState


class DiscoveryDecision(BaseModel):
    """
    Structured decision produced by the discovery reasoner.
    """

    discovery_complete: bool = Field(
        description=(
            "True when enough database information has been discovered "
            "to construct the SQL required for the user's request."
        )
    )

    queries: list[str] = Field(
        default_factory=list,
        description=(
            "One or more independent read-only PostgreSQL metadata "
            "queries required for the next discovery step. Must be "
            "empty when discovery is complete."
        ),
    )

    schema_update: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Rich reusable database knowledge learned during discovery. "
            "Include database and table descriptions, table schemas with "
            "column names, data types, nullability and key information "
            "when observed, short factual column descriptions, and "
            "discovered relationships. Preserve structural metadata "
            "together with semantic descriptions. Do not invent "
            "unsupported facts."
        ),
    )


async def discovery_node(
    state: SQLAgentState,
) -> dict:
    """
    Control the database discovery loop.

    The node examines all schema knowledge and previous discovery
    results and decides whether:

    1. More information is required, in which case it generates
       the next batch of metadata SQL queries.

    2. Enough information has been discovered, in which case it
       returns a rich schema update for persistent storage.

    This node does not validate SQL, execute SQL, or persist the
    schema registry itself.
    """

    llm = get_llm()

    discovery_llm = llm.with_structured_output(
        DiscoveryDecision
    )

    system_prompt = DISCOVERY_PROMPT.format(
        query=state["query"],
        schema_context=json.dumps(
            state["schema_context"],
            indent=2,
        ),
        missing_information=json.dumps(
            state["missing_information"],
            indent=2,
        ),
        error=state["error"] or "None",
    )

    messages = [
        SystemMessage(content=system_prompt),
        *state["discovery_messages"],
    ]

    result = await discovery_llm.ainvoke(messages)

    # ======================================================
    # Discovery complete
    # ======================================================

    if result.discovery_complete:
        return {
            "active_loop": "discovery",
            "discovery_complete": True,
            "candidate_sql": [],
            "schema_update": result.schema_update,
            "error": None,
            "discovery_messages": [
                AIMessage(
                    content=json.dumps(
                        {
                            "discovery_complete": True,
                            "schema_update": result.schema_update,
                        },
                        indent=2,
                    )
                )
            ],
        }

    # ======================================================
    # More discovery required
    # ======================================================

    return {
        "active_loop": "discovery",
        "discovery_complete": False,
        "candidate_sql": result.queries,
        "schema_update": {},
        "discovery_messages": [
            AIMessage(
                content=json.dumps(
                    {
                        "discovery_complete": False,
                        "queries": result.queries,
                    },
                    indent=2,
                )
            )
        ],
    }