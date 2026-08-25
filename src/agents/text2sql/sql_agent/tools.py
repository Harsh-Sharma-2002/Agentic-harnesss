from __future__ import annotations

import asyncio
from typing import Any

import psycopg
from langchain_core.tools import tool


DATABASE_CONFIG = {
    "dbname": "ecommerce",
    "user": "harshsharma",
    "host": "localhost",
    "port": 5432,
}


@tool
async def run_sql(query: str) -> dict[str, Any]:
    """
    Execute a read-only SQL query against PostgreSQL.

    This tool may be used both for database schema discovery
    and for executing the final user query.

    Only SELECT queries are permitted.
    """

    if not query.strip().lower().startswith("select"):
        return {
            "success": False,
            "error": "Only read-only SELECT queries are allowed.",
            "rows": [],
        }

    def _execute() -> dict[str, Any]:

        try:
            with psycopg.connect(
                **DATABASE_CONFIG
            ) as connection:

                with connection.cursor() as cursor:

                    cursor.execute(query)

                    columns = [
                        description.name
                        for description in cursor.description
                    ]

                    rows = cursor.fetchall()

                    result = [
                        dict(zip(columns, row))
                        for row in rows
                    ]

                    return {
                        "success": True,
                        "error": None,
                        "rows": result,
                    }

        except Exception as exc:

            return {
                "success": False,
                "error": str(exc),
                "rows": [],
            }

    return await asyncio.to_thread(_execute)


DISCOVERY_TOOLS = [
    run_sql,
]