# agentic_harness/harness/state.py

from __future__ import annotations

from operator import add
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


# ==========================================================
# Execution Context
# ==========================================================

class ExecutionContext(TypedDict):
    """
    Routing decisions made by the Harness.

    The orchestrator is responsible for populating this
    exactly once before invoking the selected agent.
    """

    intent: str | None

    selected_agent: str | None

    resource_type: Literal[
        "database",
        "web",
        "none",
    ]

    resource_id: str | None

    confidence: float | None


# ==========================================================
# Execution Record
# ==========================================================

class ExecutionRecord(TypedDict):
    """
    Public execution record emitted by agents.

    Agent internal state is intentionally hidden.
    """

    agent: str

    step: str

    status: Literal[
        "SUCCESS",
        "FAILED",
        "RETRY",
        "INFO",
    ]

    response: dict[str, Any]

    metadata: dict[str, Any]


# ==========================================================
# Global State
# ==========================================================

class GlobalState(TypedDict):
    """
    Shared LangGraph state.

    Every node receives this state and returns
    an updated copy.

    Only shared execution information belongs here.
    Agent-specific implementation details remain private.
    """

    # ======================================================
    # Request
    # ======================================================

    request_id: str

    user_query: str

    messages: Annotated[
        list[AnyMessage],
        add_messages,
    ]

    # ======================================================
    # Routing
    # ======================================================

    execution: ExecutionContext

    # ======================================================
    # Response
    # ======================================================

    final_response: str | None

    status: Literal[
        "CREATED",
        "ROUTING",
        "RUNNING",
        "SUCCESS",
        "FAILED",
    ]

    error: str | None

    # ======================================================
    # Observability
    # ======================================================

    execution_log: Annotated[
        list[ExecutionRecord],
        add,
    ]

    # ======================================================
    # Additional Context
    # ======================================================

    metadata: dict[str, Any]