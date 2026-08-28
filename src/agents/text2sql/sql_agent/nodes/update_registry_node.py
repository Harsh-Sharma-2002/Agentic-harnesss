# src/agents/text2sql/sql_agent/nodes/update_registry_node.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.agents.text2sql.sql_agent.state import SQLAgentState
from src.core.events import emit


REGISTRY_PATH = (
    Path(__file__).resolve().parents[2]
    / "schema_registry.json"
)


# ==========================================================
# Registry Merge
# ==========================================================

def _deep_merge(
    existing: dict[str, Any],
    update: dict[str, Any],
) -> dict[str, Any]:
    """
    Recursively merge newly discovered schema knowledge
    into existing registry knowledge.

    Dictionaries are recursively merged.

    Lists are extended without duplicate entries.

    New scalar values replace old scalar values.
    """

    merged = existing.copy()

    for key, value in update.items():

        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = _deep_merge(
                merged[key],
                value,
            )

        elif (
            key in merged
            and isinstance(merged[key], list)
            and isinstance(value, list)
        ):
            merged[key] = merged[key].copy()

            for item in value:
                if item not in merged[key]:
                    merged[key].append(item)

        else:
            merged[key] = value

    return merged


# ==========================================================
# SQL Loop Transition
# ==========================================================

def _sql_loop_transition(
    schema_context: dict[str, Any],
) -> dict:
    """
    Build the state update required to leave discovery
    and enter the SQL reasoning loop.

    This transition is shared by both:

    1. Discovery that produced new persistent knowledge.
    2. Discovery that completed without learning anything new.
    """

    return {
        # Schema knowledge available to SQL reasoning.
        "schema_context": schema_context,

        # Discovery is complete.
        "discovery_complete": True,

        # Nothing remains waiting for persistence.
        "schema_update": {},

        # Transfer execution ownership to SQL reasoning.
        "active_loop": "sql",

        # Reset the shared execution pipeline before the
        # SQL reasoning loop begins.
        "candidate_sql": [],
        "sql_valid": False,
        "execution_result": [],
        "verified": False,

        # Discovery errors/retries should not leak into the
        # user-facing SQL execution loop.
        "error": None,
        "retry_count": 0,
    }


# ==========================================================
# Registry Update Node
# ==========================================================

def update_registry_node(
    state: SQLAgentState,
) -> dict:
    """
    Persist completed discovery knowledge and transition
    execution from the discovery loop to the SQL loop.

    Discovery may legitimately complete without producing new
    reusable schema knowledge. In that case, the registry is
    left unchanged and execution proceeds directly to the
    SQL reasoning loop.

    This node performs no LLM reasoning.
    """

    # ======================================================
    # Preconditions
    # ======================================================

    if not state["discovery_complete"]:
        raise ValueError(
            "Registry update attempted before discovery completed."
        )

    schema_update = state[
        "schema_update"
    ]

    database_id = state[
        "database_id"
    ]

    # ======================================================
    # Registry update started
    # ======================================================

    emit(
        component="registry",
        event="update_started",
        message="Processing discovered schema knowledge.",
        data={
            "database_id": database_id,
            "schema_update_available": bool(
                schema_update
            ),
        },
    )

    # ======================================================
    # No new schema knowledge
    # ======================================================

    if not schema_update:

        emit(
            component="registry",
            event="update_skipped",
            message=(
                "No new schema knowledge requires persistence."
            ),
            data={
                "database_id": database_id,
            },
        )

        # Discovery determined that execution can proceed,
        # but nothing new needs to be persisted.
        #
        # Preserve the schema context already available to
        # this invocation and enter the SQL reasoning loop.
        return _sql_loop_transition(
            state["schema_context"]
        )

    # ======================================================
    # Load registry
    # ======================================================

    if REGISTRY_PATH.exists():

        with REGISTRY_PATH.open(
            "r",
            encoding="utf-8",
        ) as file:
            registry = json.load(
                file
            )

    else:
        registry = {}

    # ======================================================
    # Load existing database knowledge
    # ======================================================

    existing_context = registry.get(
        database_id,
        {},
    )

    # ======================================================
    # Merge newly discovered knowledge
    # ======================================================

    merged_context = _deep_merge(
        existing_context,
        schema_update,
    )

    registry[
        database_id
    ] = merged_context

    # ======================================================
    # Persist registry
    # ======================================================

    with REGISTRY_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            registry,
            file,
            indent=2,
            ensure_ascii=False,
        )

    # ======================================================
    # Registry update completed
    # ======================================================

    tables = merged_context.get(
        "tables",
        {},
    )

    relationships = merged_context.get(
        "relationships",
        [],
    )

    emit(
        component="registry",
        event="update_completed",
        message="Schema registry updated successfully.",
        data={
            "database_id": database_id,
            "table_count": len(
                tables
            ),
            "relationship_count": len(
                relationships
            ),
        },
    )

    # ======================================================
    # Exit discovery / enter SQL loop
    # ======================================================

    return _sql_loop_transition(
        merged_context
    )