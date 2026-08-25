# init_node.py

from langchain_core.messages import HumanMessage

from ..state import SQLAgentState


async def init_node(state: SQLAgentState) -> dict:
    """Initialize request-scoped Text2SQL state."""

    return {
        "discovery_messages": [
            HumanMessage(content=state["query"])
        ],
        "sql_messages": [
            HumanMessage(content=state["query"])
        ],
        "schema_context": {},
        "context_sufficient": False,
        "missing_information": [],
        "generated_sql": None,
        "execution_result": None,
        "error": None,
        "retry_count": 0,
        "verified": False,
        "response": None,
        "execution_records": [],
    }