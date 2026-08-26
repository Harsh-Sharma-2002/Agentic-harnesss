# src/agents/text2sql/sql_agent/nodes/update_registry_node.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.agents.text2sql.sql_agent.state import SQLAgentState


REGISTRY_PATH = (
    Path(__file__).resolve().parents[2]
    / "schema_registry.json"
)


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


def update_registry_node(
    state: SQLAgentState,
) -> dict:
    """
    Persist completed discovery knowledge and transition
    execution from the discovery loop to the SQL loop.

    This node performs no LLM reasoning.
    """

    # ======================================================
    # Preconditions
    # ======================================================

    if not state["discovery_complete"]:
        raise ValueError(
            "Registry update attempted before discovery completed."
        )

    schema_update = state["schema_update"]

    if not schema_update:
        raise ValueError(
            "Discovery completed without producing schema knowledge."
        )

    database_id = state["database_id"]

    # ======================================================
    # Load registry
    # ======================================================

    if REGISTRY_PATH.exists():
        with REGISTRY_PATH.open(
            "r",
            encoding="utf-8",
        ) as file:
            registry = json.load(file)
    else:
        registry = {}

    # ======================================================
    # Merge knowledge
    # ======================================================

    existing_context = registry.get(
        database_id,
        {},
    )

    merged_context = _deep_merge(
        existing_context,
        schema_update,
    )

    registry[database_id] = merged_context

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
    # Exit discovery / enter SQL loop
    # ======================================================

    return {
        # Make newly learned knowledge immediately available
        # to the SQL reasoning loop.
        "schema_context": merged_context,

        # Discovery is finished.
        "discovery_complete": True,
        "schema_update": {},

        # Hand execution ownership to the SQL loop.
        "active_loop": "sql",

        # Reset shared pipeline state before SQL reasoning.
        "candidate_sql": [],
        "sql_valid": False,
        "execution_result": [],
        "verified": False,
        "error": None,
        "retry_count": 0,
    }
