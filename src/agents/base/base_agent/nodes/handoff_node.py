# src/agents/base/base_agent/nodes/handoff_node.py

from __future__ import annotations

from langchain_core.messages import AIMessage

from src.agents.text2sql.sql_agent.graph import sql_agent_graph
from src.agents.web_search.web_agent.graph import web_agent_graph
from src.core.events import emit

from ..state import GlobalState


# ==========================================================
# Temporary configuration
# ==========================================================

# The current Text2SQL implementation targets one database.
# Move this into application configuration when multiple
# database resources are introduced.
DEFAULT_DATABASE_ID = "ecommerce"


async def handoff_node(
    state: GlobalState,
) -> dict:
    """
    Hand the request to the agent selected by the Base Agent.

    This node is the boundary between shared GlobalState and
    agent-private execution state.

    Responsibilities:

    1. Inspect the orchestrator's selected agent.
    2. Translate GlobalState into that agent's private input.
    3. Invoke the private agent graph.
    4. Translate the private result back into GlobalState.
    5. Handle the no-suitable-agent path.

    Private agent state is never copied directly into GlobalState.
    """

    selected_agent = state["execution"]["selected_agent"]
    request_id = state["request_id"]
    user_query = state["user_query"]

    # ======================================================
    # Preconditions
    # ======================================================

    if selected_agent is None:
        raise ValueError(
            "Handoff attempted before an agent was selected."
        )

    # ======================================================
    # No suitable agent
    # ======================================================

    if selected_agent == "none":
        response = (
            "No suitable agent is currently available "
            "to handle this request."
        )

        emit(
            component="base_agent",
            event="no_agent_available",
            message="No suitable agent was found for the request.",
            data={
                "request_id": request_id,
            },
        )

        return {
            "messages": [
                AIMessage(
                    content=response
                )
            ],
            "final_response": response,
            "status": "SUCCESS",
            "error": None,
            "execution_log": [
                {
                    "agent": "base_agent",
                    "step": "handoff",
                    "status": "INFO",
                    "response": {
                        "selected_agent": "none",
                        "message": response,
                    },
                    "metadata": {
                        "intent": state["execution"]["intent"],
                        "confidence": state["execution"]["confidence"],
                    },
                }
            ],
        }

    # ======================================================
    # Handoff started
    # ======================================================

    emit(
        component="base_agent",
        event="handoff_started",
        message=f"Handing request to {selected_agent}.",
        data={
            "request_id": request_id,
        },
    )

    # ======================================================
    # Text2SQL
    # ======================================================

    if selected_agent == "text2sql":
        result = await sql_agent_graph.ainvoke(
            {
                "query": user_query,
                "database_id": DEFAULT_DATABASE_ID,
            }
        )

        private_response = result.get("response")

        if not private_response:
            raise ValueError(
                "Text2SQL agent completed without producing a response."
            )

        answer = private_response.get("answer")

        if not answer:
            raise ValueError(
                "Text2SQL agent response does not contain an answer."
            )

        execution_metadata = {
            "database_id": DEFAULT_DATABASE_ID,
            "sql": result.get(
                "final_sql",
                [],
            ),
        }

    # ======================================================
    # Web Search
    # ======================================================

    elif selected_agent == "web_search":
        result = await web_agent_graph.ainvoke(
            {
                "query": user_query,
            }
        )

        private_response = result.get("response")

        if not private_response:
            raise ValueError(
                "Web search agent completed without producing a response."
            )

        answer = private_response.get("answer")

        if not answer:
            raise ValueError(
                "Web search agent response does not contain an answer."
            )

        execution_metadata = {
            "search_query": result.get(
                "search_query"
            ),
            "sources": private_response.get(
                "sources",
                [],
            ),
        }

    # ======================================================
    # Invalid routing decision
    # ======================================================

    else:
        raise ValueError(
            f"Unsupported selected agent: {selected_agent}"
        )

    # ======================================================
    # Handoff completed
    # ======================================================

    emit(
        component="base_agent",
        event="handoff_completed",
        message=f"{selected_agent} completed successfully.",
        data={
            "request_id": request_id,
        },
    )

    # ======================================================
    # Translate private result -> GlobalState
    # ======================================================

    return {
        "messages": [
            AIMessage(
                content=answer
            )
        ],

        "final_response": answer,

        "status": "SUCCESS",

        "error": None,

        "execution_log": [
            {
                "agent": selected_agent,
                "step": "execution",
                "status": "SUCCESS",
                "response": {
                    "answer": answer,
                },
                "metadata": execution_metadata,
            }
        ],
    }
