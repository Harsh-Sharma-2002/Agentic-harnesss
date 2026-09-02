#!/usr/bin/env python3

"""
Smoke test for the Agent Harness ecommerce PostgreSQL database.

Run from the repository root:

    python test_database.py

This test does NOT inspect or pre-populate the Agent Harness schema
registry. It only verifies that the physical PostgreSQL demo database
created by scripts/init_database.py is usable.

Checks:
1. psql is installed and available on PATH.
2. The local PostgreSQL server is reachable.
3. The `ecommerce` database exists and is reachable.
4. The demo SQL created application tables.
5. The demo database contains data.
6. A normal read-only SQL query succeeds.
"""

from __future__ import annotations

import getpass
import os
import shutil
import subprocess
import sys


DATABASE_NAME = "ecommerce"
ADMIN_USER = "postgres"
HOST = "localhost"
PORT = "5432"


def section(title: str) -> None:
    print()
    print("=" * 60)
    print(f" {title}")
    print("=" * 60)
    print()


def passed(message: str) -> None:
    print(f"[PASS] {message}")


def failed(message: str) -> None:
    print(f"[FAIL] {message}")
    raise RuntimeError(message)


def run_psql(
    *,
    database: str,
    password: str,
    sql: str,
) -> str:
    env = os.environ.copy()

    if password:
        env["PGPASSWORD"] = password

    result = subprocess.run(
        [
            "psql",
            "-h",
            HOST,
            "-p",
            PORT,
            "-U",
            ADMIN_USER,
            "-d",
            database,
            "-v",
            "ON_ERROR_STOP=1",
            "-t",
            "-A",
            "-c",
            sql,
        ],
        env=env,
        text=True,
        capture_output=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip()
            or result.stdout.strip()
            or "Unknown psql error."
        )

    return result.stdout.strip()


def main() -> None:
    section("Agent Harness Database Smoke Test")

    failures: list[str] = []

    # ======================================================
    # 1. psql
    # ======================================================

    if shutil.which("psql") is None:
        print("[FAIL] psql was not found on PATH.")
        print()
        print("Run the platform setup script first:")
        print()
        print("  Windows:       .\\scripts\\setup.ps1")
        print("  macOS/Linux:   ./scripts/setup.sh")
        raise SystemExit(1)

    passed("psql is available.")

    try:
        version = subprocess.run(
            ["psql", "--version"],
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()

        print(f"       {version}")

    except subprocess.CalledProcessError:
        failures.append("Could not read the psql version.")

    # ======================================================
    # Credentials
    # ======================================================

    print()
    print("PostgreSQL connection:")
    print(f"  Host:     {HOST}")
    print(f"  Port:     {PORT}")
    print(f"  User:     {ADMIN_USER}")
    print()

    password = getpass.getpass(
        "PostgreSQL administrator password "
        "(press Enter if your local setup requires none): "
    )

    # ======================================================
    # 2. Server connectivity
    # ======================================================

    section("Checking PostgreSQL Server")

    try:
        output = run_psql(
            database="postgres",
            password=password,
            sql="SELECT 1;",
        )

        if output != "1":
            failed(
                f"Unexpected PostgreSQL response: {output!r}"
            )

        passed("PostgreSQL server is reachable.")

    except Exception as exc:
        print(f"[FAIL] PostgreSQL connection failed: {exc}")
        print()
        print("Make sure PostgreSQL is running and the administrator")
        print("password is correct.")
        raise SystemExit(1)

    # ======================================================
    # 3. ecommerce database exists
    # ======================================================

    section("Checking ecommerce Database")

    try:
        output = run_psql(
            database="postgres",
            password=password,
            sql=(
                "SELECT datname "
                "FROM pg_database "
                "WHERE datname = 'ecommerce';"
            ),
        )

        if output != DATABASE_NAME:
            failed(
                "Database 'ecommerce' does not exist. "
                "Run: python scripts/init_database.py"
            )

        passed("Database 'ecommerce' exists.")

    except Exception as exc:
        failures.append(str(exc))
        print(f"[FAIL] {exc}")

    # ======================================================
    # Stop here if the DB itself is absent.
    # ======================================================

    if failures:
        section("Test Failed")

        for failure in failures:
            print(f"- {failure}")

        print()
        print("Run:")
        print()
        print("  python scripts/init_database.py")
        print()
        print("and then rerun this test.")
        raise SystemExit(1)

    # ======================================================
    # 4. Application tables
    # ======================================================

    section("Checking Demo Schema")

    try:
        table_count_raw = run_psql(
            database=DATABASE_NAME,
            password=password,
            sql="""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_type = 'BASE TABLE';
            """,
        )

        table_count = int(table_count_raw)

        if table_count <= 0:
            failed(
                "The ecommerce database contains no public tables. "
                "data/ecommerce.sql may not have been loaded."
            )

        passed(
            f"Demo schema contains {table_count} public table(s)."
        )

    except Exception as exc:
        failures.append(
            f"Schema verification failed: {exc}"
        )
        print(f"[FAIL] Schema verification failed: {exc}")

    # ======================================================
    # 5. Data exists
    #
    # This deliberately does not hardcode table names.
    # We inspect metadata only for the smoke test, then count
    # rows in each discovered public table.
    # ======================================================

    section("Checking Demo Data")

    try:
        table_output = run_psql(
            database=DATABASE_NAME,
            password=password,
            sql="""
                SELECT quote_ident(table_name)
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """,
        )

        tables = [
            line.strip()
            for line in table_output.splitlines()
            if line.strip()
        ]

        total_rows = 0
        populated_tables = 0

        for table in tables:
            count_raw = run_psql(
                database=DATABASE_NAME,
                password=password,
                sql=f'SELECT COUNT(*) FROM public.{table};',
            )

            count = int(count_raw)
            total_rows += count

            if count > 0:
                populated_tables += 1

        if total_rows <= 0:
            failed(
                "Tables exist, but no demo rows were found. "
                "data/ecommerce.sql may not have loaded correctly."
            )

        passed(
            f"Found {total_rows} total row(s) across "
            f"{populated_tables} populated table(s)."
        )

    except Exception as exc:
        failures.append(
            f"Demo-data verification failed: {exc}"
        )
        print(f"[FAIL] Demo-data verification failed: {exc}")

    # ======================================================
    # 6. Generic read-only query
    # ======================================================

    section("Checking Read-Only SQL")

    try:
        output = run_psql(
            database=DATABASE_NAME,
            password=password,
            sql=(
                "SELECT current_database() || ':' || "
                "current_user;"
            ),
        )

        if not output.startswith(
            f"{DATABASE_NAME}:"
        ):
            failed(
                f"Unexpected query result: {output!r}"
            )

        passed("Read-only SQL execution succeeded.")
        print(f"       {output}")

    except Exception as exc:
        failures.append(
            f"Read-only query failed: {exc}"
        )
        print(f"[FAIL] Read-only query failed: {exc}")

    # ======================================================
    # Final result
    # ======================================================

    if failures:
        section("Database Test Failed")

        print(
            f"{len(failures)} check(s) failed:"
        )
        print()

        for failure in failures:
            print(f"  - {failure}")

        print()
        print("Try resetting the demo database with:")
        print()
        print("  python scripts/init_database.py")
        print()

        raise SystemExit(1)

    section("All Database Checks Passed")

    print("The physical ecommerce database is ready.")
    print()
    print(
        "This test did not modify or populate "
        "schema_registry.json."
    )
    print(
        "The Text2SQL agent remains responsible for schema "
        "discovery at runtime."
    )
    print()


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print()
        print("[WARNING] Database test cancelled.")
        sys.exit(130)
