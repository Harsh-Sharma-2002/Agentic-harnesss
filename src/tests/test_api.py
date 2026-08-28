# src/tests/test_api.py

from __future__ import annotations

import json
import time
import traceback
from typing import Any

from fastapi.testclient import TestClient

from src.api.app import app


# ==========================================================
# Test Client
# ==========================================================

client = TestClient(app)


# ==========================================================
# Test Cases
# ==========================================================

TEST_CASES: list[dict[str, Any]] = [
    {
        "name": "Text2SQL - Customer Count",
        "query": "How many customers are in the database?",
        "expected_agent": "text2sql",
    },
    {
        "name": "Text2SQL - Customer Filter",
        "query": "Show me customers from California.",
        "expected_agent": "text2sql",
    },
    {
        "name": "Web Search - Current News",
        "query": "What is the latest news about OpenAI?",
        "expected_agent": "web_search",
    },
    {
        "name": "Web Search - Current AI",
        "query": "What are the latest developments in AI?",
        "expected_agent": "web_search",
    },
    {
        "name": "No Suitable Agent",
        "query": "Write me a Python implementation of merge sort.",
        "expected_agent": "none",
    },
]


RESULTS: list[dict[str, Any]] = []


# ==========================================================
# Health Check
# ==========================================================

def test_health() -> None:
    print("\n")
    print("=" * 80)
    print("API HEALTH CHECK")
    print("=" * 80)

    response = client.get(
        "/health"
    )

    assert response.status_code == 200, (
        f"Expected HTTP 200, got "
        f"{response.status_code}."
    )

    body = response.json()

    assert body == {
        "status": "ok"
    }

    print("\nResponse:")
    print(
        json.dumps(
            body,
            indent=2,
        )
    )

    print("\n[PASSED] API Health Check")


# ==========================================================
# Run One Query
# ==========================================================

def run_query_test(
    test_case: dict[str, Any],
) -> None:
    """
    Send one request through the complete HTTP API.

    A failure is recorded without stopping the remaining
    integration tests.
    """

    name = test_case["name"]
    query = test_case["query"]
    expected_agent = test_case[
        "expected_agent"
    ]

    print("\n")
    print("=" * 80)
    print(f"API TEST: {name}")
    print("=" * 80)

    print(
        f"\nQuery: {query}"
    )

    print(
        f"Expected agent: {expected_agent}"
    )

    started = time.perf_counter()

    try:
        # ==================================================
        # HTTP request
        # ==================================================

        response = client.post(
            "/api/v1/query",
            json={
                "query": query,
            },
        )

        duration = (
            time.perf_counter()
            - started
        )

        # ==================================================
        # HTTP validation
        # ==================================================

        assert response.status_code == 200, (
            f"Expected HTTP 200, got "
            f"{response.status_code}.\n\n"
            f"Response:\n{response.text}"
        )

        body = response.json()

        # ==================================================
        # Response contract
        # ==================================================

        assert body[
            "request_id"
        ], (
            "API returned an empty request_id."
        )

        assert (
            body["status"]
            == "SUCCESS"
        ), (
            f"Expected SUCCESS, got "
            f"{body['status']!r}."
        )

        assert (
            body["agent"]
            == expected_agent
        ), (
            f"Expected agent "
            f"{expected_agent!r}, "
            f"got {body['agent']!r}."
        )

        assert isinstance(
            body["answer"],
            str,
        )

        assert body[
            "answer"
        ].strip(), (
            "API returned an empty answer."
        )

        assert isinstance(
            body["metadata"],
            dict,
        )

        # ==================================================
        # Shared routing metadata
        # ==================================================

        metadata = body[
            "metadata"
        ]

        assert metadata.get(
            "intent"
        ), (
            "API response does not contain "
            "routing intent."
        )

        assert (
            metadata.get(
                "confidence"
            )
            is not None
        ), (
            "API response does not contain "
            "routing confidence."
        )

        # ==================================================
        # Text2SQL metadata
        # ==================================================

        if expected_agent == "text2sql":

            assert (
                metadata.get(
                    "database_id"
                )
                == "ecommerce"
            ), (
                "Text2SQL response contains "
                "an unexpected database_id."
            )

            sql = metadata.get(
                "sql"
            )

            assert sql, (
                "Text2SQL response contains "
                "no generated SQL."
            )

            assert isinstance(
                sql,
                list,
            )

            for statement in sql:
                assert isinstance(
                    statement,
                    str,
                )

                assert statement.strip()

            print("\nSQL:")

            for index, statement in enumerate(
                sql,
                start=1,
            ):
                print(
                    f"\nSQL {index}:"
                )

                print(
                    statement
                )

        # ==================================================
        # Web Search metadata
        # ==================================================

        elif expected_agent == "web_search":

            search_query = metadata.get(
                "search_query"
            )

            assert search_query, (
                "Web response contains "
                "no search_query."
            )

            sources = metadata.get(
                "sources"
            )

            assert sources, (
                "Web response contains "
                "no sources."
            )

            assert isinstance(
                sources,
                list,
            )

            print("\nSearch query:")
            print(
                search_query
            )

            print(
                f"\nSources: {len(sources)}"
            )

        # ==================================================
        # No Agent
        # ==================================================

        elif expected_agent == "none":

            assert (
                "No suitable agent"
                in body["answer"]
            ), (
                "Unexpected no-agent response."
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
                "selected_agent": body[
                    "agent"
                ],
                "http_status": (
                    response.status_code
                ),
                "duration_seconds": round(
                    duration,
                    2,
                ),
                "error": None,
            }
        )

        print("\n" + "-" * 80)
        print("API RESPONSE")
        print("-" * 80)

        print(
            json.dumps(
                body,
                indent=2,
                default=str,
            )
        )

        print(
            f"\n[PASSED] {name} "
            f"({duration:.2f}s)"
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
                "http_status": getattr(
                    locals().get("response"),
                    "status_code",
                    None,
                ),
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
        print(f"[FAILED] {name}")
        print("!" * 80)

        print(
            f"\n{type(exc).__name__}: "
            f"{exc}"
        )

        print("\nTRACEBACK:")
        traceback.print_exc()

        print(
            "\nContinuing to next API test..."
        )


# ==========================================================
# Summary
# ==========================================================

def print_summary() -> None:
    print("\n\n")
    print("=" * 80)
    print("API INTEGRATION TEST SUMMARY")
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
            if result["status"] == "PASSED"
            else "FAIL"
        )

        print(
            f"[{symbol}] "
            f"{result['name']:<38} "
            f"{result['duration_seconds']:>8.2f}s"
        )

        print(
            f"       expected="
            f"{result['expected_agent']}"
        )

        if result[
            "selected_agent"
        ] is not None:
            print(
                f"       selected="
                f"{result['selected_agent']}"
            )

        print(
            f"       HTTP="
            f"{result['http_status']}"
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

def main() -> None:
    print("\n")
    print("#" * 80)
    print("AGENT HARNESS API INTEGRATION TEST")
    print("#" * 80)

    # ======================================================
    # Health
    # ======================================================

    try:
        test_health()

    except Exception as exc:
        print(
            f"\n[FAILED] Health Check: "
            f"{type(exc).__name__}: {exc}"
        )

        traceback.print_exc()

    # ======================================================
    # Query tests
    # ======================================================

    for test_case in TEST_CASES:
        run_query_test(
            test_case
        )

    print_summary()


if __name__ == "__main__":
    main()
