# src/agents/text2sql/sql_agent/nodes/load_registry_node.py

import json
from pathlib import Path

from ..state import SQLAgentState


# schema_registry.json lives two levels above nodes/
REGISTRY_PATH = (
    Path(__file__).resolve().parents[2]
    / "schema_registry.json"
)


def load_registry_node(state: SQLAgentState) -> dict:
    """
    Load persistent schema knowledge for the current database.

    The registry acts as long-term memory across Text2SQL requests.
    Only knowledge associated with the current database is copied
    into this invocation's private schema_context.
    """

    # Registry does not exist yet.
    if not REGISTRY_PATH.exists():
        return {
            "schema_context": {}
        }

    # Load persistent schema memory.
    with REGISTRY_PATH.open("r", encoding="utf-8") as file:
        registry = json.load(file)

    # Retrieve only knowledge belonging to this database.
    schema_context = registry.get(
        state["database_id"],
        {},
    )

    return {
        "schema_context": schema_context
    }