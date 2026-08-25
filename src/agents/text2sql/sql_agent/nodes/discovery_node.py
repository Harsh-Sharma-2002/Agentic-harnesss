# src/agents/text2sql/sql_agent/nodes/discovery_node.py

from __future__ import annotations

import json

from langchain_core.messages import AIMessage, SystemMessage
from pydantic import BaseModel, Field

from src.agents.core.call_llm import get_llm
from src.agents.text2sql.sql_agent.nodes.prompts import DISCOVERY_PROMPT
from src.agents.text2sql.sql_agent.state import SQLAgentState


class DiscoveryQuery(BaseModel):
    queries: list[str] = Field(
        description=(
            "One or more independent read-only PostgreSQL "
            "metadata queries required for the next discovery step."
        )
    )


async def discovery_node(state: SQLAgentState) -> dict:
    """
    Generate the next SQL query required for database discovery.

    The context-check node has already determined what information
    is missing. This node decides what metadata query should be run
    next, but does not validate or execute it.
    """

    llm = get_llm()

    discovery_llm = llm.with_structured_output(
        DiscoveryQuery
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

    return {
    "active_loop": "discovery",
    "candidate_sql": result.queries,
    "discovery_messages": [
        AIMessage(
            content=json.dumps(
                {"queries": result.queries},
                indent=2,
                )
            )
        ],
    }