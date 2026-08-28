# src/tests/test_integration.py

from __future__ import annotations

import asyncio
import json
import time
import traceback
import uuid
from typing import Any

from src.agents.base.base_agent.graph import base_agent_graph


# ==========================================================
# Integration Test Cases
# ==========================================================

TEST_CASES = [
    # ------------------------------------------------------
    # 1. Web Search - current information
    # ------------------------------------------------------
    {
        "name": "Web Search - Current News",
        "query": "What is the latest news about OpenAI?",
        "expected_agent": "web_search",
    },

    # ------------------------------------------------------
    # 2. Text2SQL - simple aggregate
    # ------------------------------------------------------
    {
        "name": "Text2SQL - Customer Count",
        "query": "How many customers are in the database?",
        "expected_agent": "text2sql",
    },

    # ------------------------------------------------------
    # 3. Text2SQL - record retrieval
    # ------------------------------------------------------
    {
        "name": "Text2SQL - Customer Records",
        "query": "Show me the first 5 customers in the database.",
        "expected_agent": "text2sql",
    },

    # ------------------------------------------------------
    # 4. No suitable agent
    # ------------------------------------------------------
    {
        "name": "No Agent - Code Generation",
        "query": "Write me a Python implementation of merge sort.",
        "expected_agent": "none",
    },

    # ------------------------------------------------------
    # 5. Web Search - external factual request
    # ------------------------------------------------------
    {
        "name": "Web Search - External Information",
        "query": (
            "Search the web for recent developments "
            "in artificial intelligence."
        ),
        "expected_agent": "web_search",
    },
]


# ==========================================================
# Test Results
# ==========================================================

RESULTS: list[dict[str, Any]] = []


# ==========================================================
# Run One Test
# ==========================================================

async def run_test(
    test_case: dict[str, str],
) -> None:
    """
    Execute one complete request through the Base Agent.

    Every test is isolated. A failure is recorded and execution
    continues with the remaining integration tests.
    """

    name = test_case["name"]
    query = test_case["query"]
    expected_agent = test_case[
        "expected_agent"
    ]

    request_id = str(uuid.uuid4())

    print("\n")
    print("=" * 80)
    print(f"INTEGRATION TEST: {name}")
    print("=" * 80)

    print(
        f"\nRequest ID: {request_id}"
    )

    print(
        f"Query: {query}"
    )

    print(
        f"Expected agent: {expected_agent}"
    )

    started = time.perf_counter()

    try:
        # ==================================================
        # Execute complete system
        # ==================================================

        result = await base_agent_graph.ainvoke(
            {
                "request_id": request_id,
                "user_query": query,
                "metadata": {
                    "integration_test": True,
                    "test_name": name,
                },
            }
        )

        duration = (
            time.perf_counter()
            - started
        )

        # ==================================================
        # Common state validation
        # ==================================================

        assert (
            result["request_id"]
            == request_id
        ), (
            "Request ID changed during execution."
        )

        assert (
            result["user_query"]
            == query
        ), (
            "Original user query changed during execution."
        )

        # ==================================================
        # Routing validation
        # ==================================================

        execution = result["execution"]

        selected_agent = execution[
            "selected_agent"
        ]

        assert (
            selected_agent
            == expected_agent
        ), (
            f"Expected agent {expected_agent!r}, "
            f"but selected {selected_agent!r}."
        )

        assert execution["intent"], (
            "Orchestrator did not produce an intent."
        )

        assert (
            execution["confidence"]
            is not None
        ), (
            "Orchestrator did not produce confidence."
        )

        # ==================================================
        # Lifecycle validation
        # ==================================================

        assert (
            result["status"]
            == "SUCCESS"
        ), (
            f"Expected SUCCESS, got "
            f"{result['status']!r}."
        )

        assert result["error"] is None, (
            f"Request completed with error: "
            f"{result['error']!r}"
        )

        # ==================================================
        # Response validation
        # ==================================================

        final_response = result[
            "final_response"
        ]

        assert isinstance(
            final_response,
            str,
        ), (
            "final_response must be a string."
        )

        assert final_response.strip(), (
            "final_response is empty."
        )

        # ==================================================
        # Conversation validation
        # ==================================================

        messages = result["messages"]

        assert len(messages) >= 2, (
            "Expected user and assistant messages "
            "in GlobalState."
        )

        # ==================================================
        # Execution log validation
        # ==================================================

        execution_log = result[
            "execution_log"
        ]

        assert execution_log, (
            "execution_log is empty."
        )

        routing_records = [
            record
            for record in execution_log
            if (
                record["agent"]
                == "base_agent"
                and record["step"]
                == "agent_selection"
            )
        ]

        assert routing_records, (
            "Base Agent routing record missing."
        )

        # ==================================================
        # Text2SQL-specific validation
        # ==================================================

        if expected_agent == "text2sql":

            sql_records = [
                record
                for record in execution_log
                if record["agent"]
                == "text2sql"
            ]

            assert sql_records, (
                "Text2SQL execution record missing."
            )

            sql_metadata = sql_records[-1][
                "metadata"
            ]

            assert (
                sql_metadata.get(
                    "database_id"
                )
                == "ecommerce"
            ), (
                "Incorrect Text2SQL database ID."
            )

            final_sql = sql_metadata.get(
                "sql"
            )

            assert final_sql, (
                "Text2SQL completed without "
                "producing final SQL."
            )

            assert isinstance(
                final_sql,
                list,
            )

            for query_sql in final_sql:
                assert isinstance(
                    query_sql,
                    str,
                )

                assert query_sql.strip(), (
                    "Empty SQL statement returned."
                )

            print("\nFINAL SQL:")

            for index, query_sql in enumerate(
                final_sql,
                start=1,
            ):
                print(
                    f"\nSQL {index}:"
                )

                print(
                    query_sql
                )

        # ==================================================
        # Web-specific validation
        # ==================================================

        elif expected_agent == "web_search":

            web_records = [
                record
                for record in execution_log
                if record["agent"]
                == "web_search"
            ]

            assert web_records, (
                "Web Search execution record missing."
            )

            web_metadata = web_records[-1][
                "metadata"
            ]

            assert web_metadata.get(
                "search_query"
            ), (
                "Web Search did not expose "
                "its search query."
            )

            sources = web_metadata.get(
                "sources"
            )

            assert sources, (
                "Web Search returned no sources."
            )

            assert isinstance(
                sources,
                list,
            )

            print("\nSEARCH QUERY:")

            print(
                web_metadata["search_query"]
            )

            print(
                f"\nSOURCES: {len(sources)}"
            )

        # ==================================================
        # None-route validation
        # ==================================================

        elif expected_agent == "none":

            assert (
                "No suitable agent"
                in final_response
            ), (
                "No-agent route returned an "
                "unexpected response."
            )

            no_agent_records = [
                record
                for record in execution_log
                if (
                    record["agent"]
                    == "base_agent"
                    and record["step"]
                    == "handoff"
                )
            ]

            assert no_agent_records, (
                "No-agent handoff record missing."
            )

        # ==================================================
        # Passed
        # ==================================================

        RESULTS.append(
            {
                "name": name,
                "status": "PASSED",
                "expected_agent": (
                    expected_agent
                ),
                "selected_agent": (
                    selected_agent
                ),
                "duration_seconds": round(
                    duration,
                    2,
                ),
                "error": None,
            }
        )

        print("\n" + "-" * 80)
        print("RESULT")
        print("-" * 80)

        print(
            json.dumps(
                {
                    "selected_agent": (
                        selected_agent
                    ),
                    "intent": execution[
                        "intent"
                    ],
                    "confidence": execution[
                        "confidence"
                    ],
                    "status": result[
                        "status"
                    ],
                    "final_response": (
                        final_response
                    ),
                    "duration_seconds": round(
                        duration,
                        2,
                    ),
                },
                indent=2,
                default=str,
            )
        )

        print(
            f"\n[PASSED] {name}"
        )

    # ======================================================
    # Failed
    # ======================================================

    except Exception as exc:

        duration = (
            time.perf_counter()
            - started
        )

        RESULTS.append(
            {
                "name": name,
                "status": "FAILED",
                "expected_agent": (
                    expected_agent
                ),
                "selected_agent": None,
                "duration_seconds": round(
                    duration,
                    2,
                ),
                "error": (
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ),
            }
        )

        print("\n" + "!" * 80)

        print(
            f"[FAILED] {name}"
        )

        print("!" * 80)

        print(
            f"\n{type(exc).__name__}: {exc}"
        )

        print("\nTRACEBACK:")

        traceback.print_exc()

        print(
            "\nContinuing to next "
            "integration test..."
        )


# ==========================================================
# Final Summary
# ==========================================================

def print_summary() -> None:

    print("\n\n")
    print("=" * 80)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 80)

    passed = sum(
        result["status"] == "PASSED"
        for result in RESULTS
    )

    failed = sum(
        result["status"] == "FAILED"
        for result in RESULTS
    )

    total_duration = sum(
        result["duration_seconds"]
        for result in RESULTS
    )

    for result in RESULTS:

        symbol = (
            "PASS"
            if result["status"]
            == "PASSED"
            else "FAIL"
        )

        print(
            f"[{symbol}] "
            f"{result['name']:<40} "
            f"{result['duration_seconds']:>8.2f}s"
        )

        print(
            f"       expected="
            f"{result['expected_agent']}"
        )

        if result["selected_agent"]:
            print(
                f"       selected="
                f"{result['selected_agent']}"
            )

        if result["error"]:
            print(
                f"       error="
                f"{result['error']}"
            )

    print("-" * 80)

    print(
        f"Passed: {passed}"
    )

    print(
        f"Failed: {failed}"
    )

    print(
        f"Total:  {len(RESULTS)}"
    )

    print(
        f"Runtime: {total_duration:.2f}s"
    )

    print("=" * 80)


# ==========================================================
# Main
# ==========================================================

async def main() -> None:

    print("\n")
    print("#" * 80)
    print("AGENT HARNESS END-TO-END INTEGRATION TEST")
    print("#" * 80)

    print(
        f"\nRunning {len(TEST_CASES)} "
        "integration tests..."
    )

    for test_case in TEST_CASES:
        await run_test(
            test_case
        )

    print_summary()


if __name__ == "__main__":
    asyncio.run(main())