# src/tests/test_sql_multiloop.py

from __future__ import annotations

import asyncio
import json
import time
import traceback

from src.agents.text2sql.sql_agent.graph import (
    sql_agent_graph,
)


QUERY = """
Which state has the most customers, and then show me the
3 most recently signed-up customers from that state?
""".strip()


async def main() -> None:

    print("\n")
    print("=" * 80)
    print("TEXT2SQL MULTI-LOOP TEST")
    print("=" * 80)

    print("\nQUERY:")
    print(QUERY)

    started = time.perf_counter()

    try:
        result = await sql_agent_graph.ainvoke(
            {
                "query": QUERY,
                "database_id": "ecommerce",
            }
        )

    except Exception as exc:
        duration = (
            time.perf_counter()
            - started
        )

        print("\n" + "!" * 80)
        print("TEST FAILED")
        print("!" * 80)

        print(
            f"\n{type(exc).__name__}: {exc}"
        )

        print("\nTRACEBACK:")
        traceback.print_exc()

        print(
            f"\nDuration: {duration:.2f}s"
        )

        return

    duration = (
        time.perf_counter()
        - started
    )

    # ======================================================
    # Basic completion assertions
    # ======================================================

    assert result["error"] is None, (
        f"Agent completed with error: "
        f"{result['error']!r}"
    )

    assert result[
        "execution_complete"
    ], (
        "SQL reasoner did not mark execution complete."
    )

    assert result[
        "verified"
    ], (
        "Final SQL execution was not verified."
    )

    assert result[
        "response"
    ], (
        "No final response was produced."
    )

    assert result[
        "response"
    ]["answer"], (
        "Final answer is empty."
    )

    # ======================================================
    # Accumulated SQL evidence
    # ======================================================

    sql_results = result[
        "sql_results"
    ]

    assert sql_results, (
        "No verified SQL results were accumulated."
    )

    final_sql = result[
        "final_sql"
    ]

    assert final_sql, (
        "No final SQL was recorded."
    )

    # ======================================================
    # Multi-loop assertion
    # ======================================================

    assert len(sql_results) >= 2, (
        "Expected this request to require at least "
        "two verified SQL execution batches, but only "
        f"{len(sql_results)} result(s) were accumulated.\n\n"
        "The model may have solved the request using one "
        "SQL query instead of exercising the multi-loop path."
    )

    # ======================================================
    # Inspect generated SQL
    # ======================================================

    combined_sql = " ".join(
        item["query"]
        for item in sql_results
    ).lower()

    # First part should require aggregation by state.
    assert "state" in combined_sql, (
        "Generated SQL never referenced state."
    )

    assert "count" in combined_sql, (
        "Generated SQL never counted customers."
    )

    assert "group by" in combined_sql, (
        "Expected a GROUP BY operation to determine "
        "the state with the most customers."
    )

    # Second part should involve signup ordering.
    assert "signup_date" in combined_sql, (
        "Generated SQL never used signup_date."
    )

    assert "order by" in combined_sql, (
        "Generated SQL never performed ordering."
    )

    assert "desc" in combined_sql, (
        "Expected descending ordering for the most "
        "recently signed-up customers."
    )

    # ======================================================
    # Print execution evidence
    # ======================================================

    print("\n")
    print("-" * 80)
    print("VERIFIED SQL EXECUTIONS")
    print("-" * 80)

    for index, item in enumerate(
        sql_results,
        start=1,
    ):

        print(
            f"\nEXECUTION {index}:"
        )

        print("\nSQL:")
        print(
            item["query"]
        )

        print("\nRESULT:")

        print(
            json.dumps(
                item["result"],
                indent=2,
                default=str,
            )
        )

    # ======================================================
    # SQL conversation
    # ======================================================

    print("\n")
    print("-" * 80)
    print("SQL REASONER MESSAGE HISTORY")
    print("-" * 80)

    for index, message in enumerate(
        result["sql_messages"],
        start=1,
    ):
        print(
            f"\nMESSAGE {index} "
            f"({type(message).__name__}):"
        )

        print(
            message.content
        )

    # ======================================================
    # Final result
    # ======================================================

    print("\n")
    print("-" * 80)
    print("FINAL RESULT")
    print("-" * 80)

    print(
        json.dumps(
            {
                "execution_complete": result[
                    "execution_complete"
                ],
                "verified": result[
                    "verified"
                ],
                "verified_sql_count": len(
                    sql_results
                ),
                "final_sql": final_sql,
                "retry_count": result[
                    "retry_count"
                ],
                "answer": result[
                    "response"
                ]["answer"],
                "duration_seconds": round(
                    duration,
                    2,
                ),
            },
            indent=2,
            default=str,
        )
    )

    print("\n" + "=" * 80)
    print("TEST PASSED")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(
        main()
    )
