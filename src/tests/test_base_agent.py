# src/tests/test_base_agent.py

from __future__ import annotations

import asyncio
import json
import uuid

from src.agents.base.base_agent.graph import base_agent_graph


async def run_test(
    query: str,
) -> None:
    """
    Run one complete Base Agent request and print
    the final shared GlobalState.
    """

    print("\n" + "=" * 70)
    print(f"TEST QUERY: {query}")
    print("=" * 70)

    result = await base_agent_graph.ainvoke(
        {
            "request_id": str(uuid.uuid4()),
            "user_query": query,
            "metadata": {},
        }
    )

    print("\n" + "-" * 70)
    print("FINAL GLOBAL STATE")
    print("-" * 70)

    print(
        json.dumps(
            {
                "request_id": result["request_id"],
                "user_query": result["user_query"],
                "execution": result["execution"],
                "status": result["status"],
                "final_response": result["final_response"],
                "error": result["error"],
                "execution_log": result["execution_log"],
            },
            indent=2,
            default=str,
        )
    )


async def main() -> None:
    """
    Exercise all three Base Agent routing paths.
    """

    # ======================================================
    # Web Search Route
    # ======================================================

    await run_test(
        "What is the latest news about OpenAI?"
    )

    # ======================================================
    # Text2SQL Route
    # ======================================================

    await run_test(
        "How many customers are in the database?"
    )

    # ======================================================
    # No Suitable Agent Route
    # ======================================================

    await run_test(
        "Write me a Python implementation of merge sort."
    )


if __name__ == "__main__":
    asyncio.run(main())
