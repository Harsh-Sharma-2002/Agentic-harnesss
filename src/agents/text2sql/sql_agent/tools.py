# src/agents/text2sql/sql_agent/tools.py

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
    Execute a SQL query against PostgreSQL.

    SQL validation and safety checks are performed by the
    validator node before this tool is called.
    """

    def _execute() -> dict[str, Any]:
        try:
            with psycopg.connect(
                **DATABASE_CONFIG
            ) as connection:

                # Defense in depth.
                # Even if application validation fails,
                # PostgreSQL will reject write operations.
                connection.execute(
                    "SET TRANSACTION READ ONLY"
                )

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
                        "columns": columns,
                        "rows": result,
                        "row_count": len(result),
                    }

        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
                "columns": [],
                "rows": [],
                "row_count": 0,
            }

    return await asyncio.to_thread(_execute)