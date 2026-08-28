# src/agents/text2sql/sql_agent/nodes/discovery_node.py

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AIMessage, SystemMessage
from pydantic import BaseModel, Field

from src.agents.core.call_llm import get_llm
from src.agents.text2sql.sql_agent.nodes.prompts import (
    DISCOVERY_PROMPT,
)
from src.agents.text2sql.sql_agent.state import SQLAgentState
from src.core.events import emit


# ==========================================================
# Discovery Configuration
# ==========================================================

MAX_DISCOVERY_ITERATIONS = 4


# ==========================================================
# Structured Discovery Decision
# ==========================================================

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


# ==========================================================
# Discovery Node
# ==========================================================

async def discovery_node(
    state: SQLAgentState,
) -> dict:
    """
    Control the database discovery loop.

    The node examines known schema information and previous
    discovery results and decides whether:

    1. More metadata discovery is required.

    2. Enough schema information has been discovered.

    Discovery is bounded by MAX_DISCOVERY_ITERATIONS.

    If the discovery budget is exhausted before the reasoner
    declares completion, discovery exits gracefully and the
    SQL reasoning loop proceeds using the schema knowledge
    currently available.

    This node does not validate SQL, execute SQL, or persist
    the schema registry itself.
    """

    # ======================================================
    # Current Discovery Iteration
    # ======================================================

    current_iteration = (
        state["discovery_iteration"] + 1
    )

    remaining_iterations = max(
        MAX_DISCOVERY_ITERATIONS
        - current_iteration,
        0,
    )

    # ======================================================
    # Defensive Invariant
    # ======================================================

    if current_iteration > MAX_DISCOVERY_ITERATIONS:

        emit(
            component="discovery",
            event="invalid_iteration",
            message=(
                "Discovery node was invoked after its "
                "iteration budget was exhausted."
            ),
            data={
                "database_id": state["database_id"],
                "discovery_iteration": (
                    current_iteration
                ),
                "max_discovery_iterations": (
                    MAX_DISCOVERY_ITERATIONS
                ),
            },
        )

        raise RuntimeError(
            "Discovery node was invoked after its "
            "iteration budget had already been exhausted."
        )

    # ======================================================
    # Discovery Reasoning Started
    # ======================================================

    emit(
        component="discovery",
        event="reasoning_started",
        message=(
            "Evaluating missing database schema knowledge."
        ),
        data={
            "database_id": state["database_id"],
            "missing_information": state[
                "missing_information"
            ],
            "retry_count": state[
                "retry_count"
            ],
            "discovery_iteration": (
                current_iteration
            ),
            "max_discovery_iterations": (
                MAX_DISCOVERY_ITERATIONS
            ),
            "remaining_discovery_iterations": (
                remaining_iterations
            ),
        },
    )

    # ======================================================
    # Prepare Structured LLM
    # ======================================================

    llm = get_llm()

    discovery_llm = llm.with_structured_output(
        DiscoveryDecision
    )

    # ======================================================
    # Build Discovery Prompt
    # ======================================================

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

        # Discovery budget information.
        current_iteration=current_iteration,
        max_iterations=MAX_DISCOVERY_ITERATIONS,
        remaining_iterations=remaining_iterations,
    )

    messages = [
        SystemMessage(
            content=system_prompt
        ),
        *state["discovery_messages"],
    ]

    # ======================================================
    # Ask Discovery Reasoner
    # ======================================================

    result = await discovery_llm.ainvoke(
        messages
    )

    # ======================================================
    # Discovery Complete
    # ======================================================

    if result.discovery_complete:

        tables = result.schema_update.get(
            "tables",
            {},
        )

        relationships = result.schema_update.get(
            "relationships",
            [],
        )

        emit(
            component="discovery",
            event="discovery_completed",
            message=(
                "Required database schema knowledge "
                "has been discovered."
            ),
            data={
                "database_id": state[
                    "database_id"
                ],
                "discovery_iteration": (
                    current_iteration
                ),
                "max_discovery_iterations": (
                    MAX_DISCOVERY_ITERATIONS
                ),
                "remaining_discovery_iterations": (
                    remaining_iterations
                ),
                "table_count": len(
                    tables
                ),
                "relationship_count": len(
                    relationships
                ),
                "schema_update_available": bool(
                    result.schema_update
                ),
            },
        )

        return {
            "active_loop": "discovery",

            "discovery_iteration": (
                current_iteration
            ),

            "discovery_complete": True,

            "discovery_exhausted": False,

            "candidate_sql": [],

            "schema_update": (
                result.schema_update
            ),

            "error": None,

            "discovery_messages": [
                AIMessage(
                    content=json.dumps(
                        {
                            "discovery_complete": True,
                            "discovery_exhausted": False,
                            "queries": [],
                            "schema_update": (
                                result.schema_update
                            ),
                        },
                        indent=2,
                    )
                )
            ],
        }

    # ======================================================
    # Discovery Budget Exhausted
    # ======================================================

    if (
        current_iteration
        >= MAX_DISCOVERY_ITERATIONS
    ):

        emit(
            component="discovery",
            event="iteration_limit_reached",
            message=(
                "Discovery iteration limit reached. "
                "Proceeding with available schema knowledge."
            ),
            data={
                "database_id": state[
                    "database_id"
                ],
                "discovery_iteration": (
                    current_iteration
                ),
                "max_discovery_iterations": (
                    MAX_DISCOVERY_ITERATIONS
                ),
                "remaining_discovery_iterations": 0,
                "discarded_query_count": len(
                    result.queries
                ),
                "retry_count": state[
                    "retry_count"
                ],
            },
        )

        return {
            "active_loop": "discovery",

            "discovery_iteration": (
                current_iteration
            ),

            # Discovery did not genuinely complete.
            "discovery_complete": False,

            # The discovery budget has instead been exhausted.
            "discovery_exhausted": True,

            # Do not execute another metadata query batch.
            "candidate_sql": [],

            # Do not persist incomplete schema knowledge.
            "schema_update": {},

            "error": None,

            "discovery_messages": [
                AIMessage(
                    content=json.dumps(
                        {
                            "discovery_complete": False,
                            "discovery_exhausted": True,
                            "queries": [],
                        },
                        indent=2,
                    )
                )
            ],
        }

    # ======================================================
    # More Discovery Required
    # ======================================================

    emit(
        component="discovery",
        event="queries_generated",
        message=(
            "Additional schema discovery queries "
            "are required."
        ),
        data={
            "database_id": state[
                "database_id"
            ],
            "discovery_iteration": (
                current_iteration
            ),
            "max_discovery_iterations": (
                MAX_DISCOVERY_ITERATIONS
            ),
            "remaining_discovery_iterations": (
                remaining_iterations
            ),
            "sql_queries": result.queries,
            "query_count": len(
                result.queries
            ),
        },
    )

    return {
        "active_loop": "discovery",

        "discovery_iteration": (
            current_iteration
        ),

        "discovery_complete": False,

        "discovery_exhausted": False,

        "candidate_sql": result.queries,

        "schema_update": {},

        "discovery_messages": [
            AIMessage(
                content=json.dumps(
                    {
                        "discovery_complete": False,
                        "discovery_exhausted": False,
                        "queries": result.queries,
                    },
                    indent=2,
                )
            )
        ],
    }