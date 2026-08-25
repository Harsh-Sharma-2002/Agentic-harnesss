from __future__ import annotations

import json

from langchain_core.messages import SystemMessage

from src.agents.core.call_llm import get_llm
from src.agents.text2sql.sql_agent.nodes.prompts import DISCOVERY_PROMPT
from src.agents.text2sql.sql_agent.state import SQLAgentState
from src.agents.text2sql.sql_agent.tools import DISCOVERY_TOOLS


async def discovery_node(state: SQLAgentState) -> dict:
    """
    Decide the next database discovery action.

    The context-check node has already determined what information
    is missing. This node uses the discovery tools to decide how
    to obtain that information.

    It does not execute tools itself.
    """

    llm = get_llm()

    discovery_llm = llm.bind_tools(
        DISCOVERY_TOOLS
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
    )

    messages = [
        SystemMessage(content=system_prompt),
        *state["discovery_messages"],
    ]

    response = await discovery_llm.ainvoke(messages)

    return {
        "discovery_messages": [response]
    }