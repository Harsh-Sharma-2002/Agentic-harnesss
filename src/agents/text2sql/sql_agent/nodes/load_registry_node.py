# src/agents/text2sql/sql_agent/nodes/load_registry_node.py

from __future__ import annotations

import json
from pathlib import Path

from src.core.events import emit

from ..state import SQLAgentState


# schema_registry.json lives two levels above nodes/
REGISTRY_PATH = (
    Path(__file__).resolve().parents[2]
    / "schema_registry.json"
)


def load_registry_node(
    state: SQLAgentState,
) -> dict:
    """
    Load persistent schema knowledge for the current database.

    The registry acts as long-term memory across Text2SQL requests.
    Only knowledge associated with the current database is copied
    into this invocation's private schema_context.
    """

    database_id = state["database_id"]

    # ======================================================
    # Registry lookup started
    # ======================================================

    emit(
        component="registry",
        event="load_started",
        message="Loading cached database knowledge.",
        data={
            "database_id": database_id,
        },
    )

    # ======================================================
    # Registry file does not exist
    # ======================================================

    if not REGISTRY_PATH.exists():
        emit(
            component="registry",
            event="cache_miss",
            message="Schema registry does not exist. Starting cold.",
            data={
                "database_id": database_id,
            },
        )

        return {
            "schema_context": {}
        }

    # ======================================================
    # Load persistent schema memory
    # ======================================================

    with REGISTRY_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        registry = json.load(file)

    # ======================================================
    # Retrieve database-specific knowledge
    # ======================================================

    schema_context = registry.get(
        database_id,
        {},
    )

    # ======================================================
    # Cache miss
    # ======================================================

    if not schema_context:
        emit(
            component="registry",
            event="cache_miss",
            message="No cached schema knowledge found for this database.",
            data={
                "database_id": database_id,
            },
        )

        return {
            "schema_context": {}
        }

    # ======================================================
    # Cache hit
    # ======================================================

    emit(
        component="registry",
        event="cache_hit",
        message="Cached schema knowledge loaded.",
        data={
            "database_id": database_id,
            "table_count": len(
                schema_context.get(
                    "tables",
                    {},
                )
            ),
        },
    )

    return {
        "schema_context": schema_context
    }