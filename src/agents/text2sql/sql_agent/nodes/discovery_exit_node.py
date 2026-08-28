# src/agents/text2sql/sql_agent/nodes/discovery_exit_node.py

from __future__ import annotations

from src.agents.text2sql.sql_agent.state import SQLAgentState
from src.core.events import emit


def discovery_exit_node(
    state: SQLAgentState,
) -> dict:
    """
    Transition from exhausted schema discovery into the
    SQL reasoning loop.

    No schema knowledge is persisted because discovery did
    not complete normally.

    Discovery-specific execution state is cleared before
    ownership is transferred to the SQL loop.
    """

    if not state["discovery_exhausted"]:
        raise ValueError(
            "Discovery exit attempted before the "
            "discovery budget was exhausted."
        )

    emit(
        component="discovery",
        event="forced_exit",
        message=(
            "Leaving schema discovery with the "
            "currently available schema knowledge."
        ),
        data={
            "database_id": state["database_id"],
            "discovery_iteration": (
                state["discovery_iteration"]
            ),
        },
    )

    return {
        # Transfer ownership to SQL reasoning.
        "active_loop": "sql",

        # Clear the shared execution pipeline.
        "candidate_sql": [],
        "sql_valid": False,
        "execution_result": [],
        "verified": False,

        # Discovery failures/retries must not affect
        # the SQL execution loop.
        "error": None,
        "retry_count": 0,

        # No incomplete discovery output is waiting
        # for persistence.
        "schema_update": {},
    }

