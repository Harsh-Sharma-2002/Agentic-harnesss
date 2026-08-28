# src/agents/text2sql/sql_agent/nodes/init_node.py

from langchain_core.messages import HumanMessage

from src.core.events import emit

from ..state import SQLAgentState


async def init_node(
    state: SQLAgentState,
) -> dict:
    """
    Initialize request-scoped Text2SQL state.

    Creates independent short-term memories for the discovery
    and SQL loops and resets all execution-specific fields.
    """

    # ======================================================
    # Emit initialization event
    # ======================================================

    emit(
        component="text2sql",
        event="request_initialized",
        message="Text2SQL request initialized.",
        data={
            "database_id": state["database_id"],
        },
    )

    # ======================================================
    # Initialize private state
    # ======================================================

    return {
        # ==================================================
        # Discovery loop memory
        # ==================================================

        "discovery_messages": [
            HumanMessage(
                content=state["query"]
            )
        ],

        # ==================================================
        # SQL loop memory
        # ==================================================

        "sql_messages": [
            HumanMessage(
                content=state["query"]
            )
        ],

        # ==================================================
        # Discovery state
        # ==================================================

        "schema_context": {},
        "context_sufficient": False,
        "missing_information": [],

        # Discovery has not completed normally.
        "discovery_complete": False,

        # Discovery budget has not been exhausted.
        "discovery_exhausted": False,

        # No discovery reasoning iteration has run yet.
        "discovery_iteration": 0,

        "schema_update": {},

        # ==================================================
        # SQL loop state
        # ==================================================

        "execution_complete": False,
        "sql_results": [],

        # ==================================================
        # Shared SQL execution state
        # ==================================================

        "active_loop": None,
        "candidate_sql": [],
        "sql_valid": False,
        "final_sql": [],
        "execution_result": [],

        # ==================================================
        # Validation / retry
        # ==================================================

        "error": None,
        "retry_count": 0,

        # ==================================================
        # Verification
        # ==================================================

        "verified": False,

        # ==================================================
        # Output
        # ==================================================

        "response": None,
        "execution_records": [],
    }