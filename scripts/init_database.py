#!/usr/bin/env python3

"""
Initialize the local PostgreSQL database used by Agent Harness.

This script:
1. Loads database settings from .env.
2. Connects using a PostgreSQL administrator account.
3. Creates the project role if it does not exist.
4. Creates the project database if it does not exist.
5. Grants the project role access to the project database.
6. Verifies that the project account can connect.

It does NOT:
- Download datasets.
- Create application-specific tables.
- Grant PostgreSQL superuser privileges to the agent account.

Usage:
    python scripts/init_database.py

Optional administrator overrides:
    POSTGRES_ADMIN_USER
    POSTGRES_ADMIN_PASSWORD
    POSTGRES_ADMIN_HOST
    POSTGRES_ADMIN_PORT
"""

from __future__ import annotations

import getpass
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

try:
    import psycopg
    from psycopg import sql
except ImportError as exc:
    raise SystemExit(
        "psycopg is not installed.\n"
        "Activate the project virtual environment and run:\n\n"
        "    python -m pip install -r requirements.txt\n"
    ) from exc


# ==========================================================
# Paths
# ==========================================================

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
ENV_FILE = REPO_ROOT / ".env"


# ==========================================================
# Output Helpers
# ==========================================================

def section(title: str) -> None:
    print()
    print("=" * 60)
    print(f" {title}")
    print("=" * 60)
    print()


def ok(message: str) -> None:
    print(f"[OK] {message}")


def warn(message: str) -> None:
    print(f"[WARNING] {message}")


def fail(message: str) -> None:
    print()
    print(f"[ERROR] {message}")
    print()
    raise SystemExit(1)


# ==========================================================
# Configuration
# ==========================================================

def require_env(name: str) -> str:
    value = os.getenv(name)

    if value is None or not value.strip():
        fail(
            f"{name} is missing from .env.\n"
            f"Add {name} and run this script again."
        )

    return value.strip()


def load_configuration() -> dict[str, str]:
    if not ENV_FILE.exists():
        fail(
            f".env was not found at:\n{ENV_FILE}\n\n"
            "Run the platform setup script first or create "
            ".env from .env.example."
        )

    load_dotenv(ENV_FILE)

    return {
        "host": require_env("DATABASE_HOST"),
        "port": require_env("DATABASE_PORT"),
        "database": require_env("DATABASE_NAME"),
        "user": require_env("DATABASE_USER"),
        "password": require_env("DATABASE_PASSWORD"),
    }


# ==========================================================
# Administrator Connection
# ==========================================================

def get_admin_configuration(
    project_config: dict[str, str],
) -> dict[str, str]:
    """
    Resolve administrator connection settings.

    The normal project account is intentionally separate from
    the PostgreSQL administrator account.

    Administrator values may be provided through environment
    variables. If no administrator password is supplied, the
    script prompts without echoing the password.
    """

    admin_user = os.getenv(
        "POSTGRES_ADMIN_USER",
        "postgres",
    ).strip()

    admin_host = os.getenv(
        "POSTGRES_ADMIN_HOST",
        project_config["host"],
    ).strip()

    admin_port = os.getenv(
        "POSTGRES_ADMIN_PORT",
        project_config["port"],
    ).strip()

    admin_password = os.getenv(
        "POSTGRES_ADMIN_PASSWORD",
        "",
    )

    if not admin_password:
        print(
            "PostgreSQL administrator credentials are required "
            "only to initialize the project database."
        )
        print()
        print(f"Administrator user: {admin_user}")
        print(f"Host:               {admin_host}")
        print(f"Port:               {admin_port}")
        print()

        admin_password = getpass.getpass(
            "PostgreSQL administrator password "
            "(press Enter if local auth requires none): "
        )

    return {
        "user": admin_user,
        "password": admin_password,
        "host": admin_host,
        "port": admin_port,
    }


def connect_as_admin(
    admin: dict[str, str],
) -> psycopg.Connection:
    """
    Connect to PostgreSQL's maintenance database.

    autocommit is required because CREATE DATABASE cannot run
    inside a transaction block.
    """

    try:
        connection = psycopg.connect(
            host=admin["host"],
            port=admin["port"],
            dbname="postgres",
            user=admin["user"],
            password=admin["password"] or None,
            autocommit=True,
        )

        ok("Connected to PostgreSQL administrator database.")

        return connection

    except Exception as exc:
        fail(
            "Could not connect as the PostgreSQL administrator.\n\n"
            f"Details: {exc}\n\n"
            "Check that PostgreSQL is running and that the "
            "administrator username/password are correct."
        )


# ==========================================================
# Role Initialization
# ==========================================================

def role_exists(
    connection: psycopg.Connection,
    role_name: str,
) -> bool:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 1
            FROM pg_roles
            WHERE rolname = %s;
            """,
            (role_name,),
        )

        return cursor.fetchone() is not None


def create_or_update_role(
    connection: psycopg.Connection,
    role_name: str,
    password: str,
) -> None:
    """
    Create the application role or synchronize its password.

    The role receives LOGIN but no SUPERUSER, CREATEDB, or
    CREATEROLE privileges.
    """

    with connection.cursor() as cursor:
        if role_exists(connection, role_name):
            cursor.execute(
                sql.SQL(
                    """
                    ALTER ROLE {}
                    WITH
                        LOGIN
                        NOSUPERUSER
                        NOCREATEDB
                        NOCREATEROLE
                        NOREPLICATION
                        PASSWORD %s;
                    """
                ).format(
                    sql.Identifier(role_name)
                ),
                (password,),
            )

            ok(
                f"Project role '{role_name}' already exists; "
                "credentials synchronized."
            )

        else:
            cursor.execute(
                sql.SQL(
                    """
                    CREATE ROLE {}
                    WITH
                        LOGIN
                        NOSUPERUSER
                        NOCREATEDB
                        NOCREATEROLE
                        NOREPLICATION
                        PASSWORD %s;
                    """
                ).format(
                    sql.Identifier(role_name)
                ),
                (password,),
            )

            ok(f"Created project role '{role_name}'.")


# ==========================================================
# Database Initialization
# ==========================================================

def database_exists(
    connection: psycopg.Connection,
    database_name: str,
) -> bool:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 1
            FROM pg_database
            WHERE datname = %s;
            """,
            (database_name,),
        )

        return cursor.fetchone() is not None


def create_database(
    connection: psycopg.Connection,
    database_name: str,
    owner: str,
) -> None:
    if database_exists(connection, database_name):
        ok(f"Database '{database_name}' already exists.")
        return

    with connection.cursor() as cursor:
        cursor.execute(
            sql.SQL(
                """
                CREATE DATABASE {}
                OWNER {};
                """
            ).format(
                sql.Identifier(database_name),
                sql.Identifier(owner),
            )
        )

    ok(f"Created database '{database_name}'.")


def configure_database(
    admin: dict[str, str],
    project: dict[str, str],
) -> None:
    """
    Apply database-level defaults and schema permissions.
    """

    try:
        connection = psycopg.connect(
            host=admin["host"],
            port=admin["port"],
            dbname=project["database"],
            user=admin["user"],
            password=admin["password"] or None,
            autocommit=True,
        )

    except Exception as exc:
        fail(
            "Project database was created/found, but the "
            "administrator could not connect to it.\n\n"
            f"Details: {exc}"
        )

    try:
        with connection.cursor() as cursor:
            # Ensure the project role owns the database.
            cursor.execute(
                sql.SQL(
                    "ALTER DATABASE {} OWNER TO {};"
                ).format(
                    sql.Identifier(project["database"]),
                    sql.Identifier(project["user"]),
                )
            )

            # The public schema is sufficient for the local
            # classroom/demo database.
            cursor.execute(
                sql.SQL(
                    "GRANT USAGE, CREATE ON SCHEMA public TO {};"
                ).format(
                    sql.Identifier(project["user"])
                )
            )

        ok("Project database permissions configured.")

    finally:
        connection.close()


# ==========================================================
# Verification
# ==========================================================

def verify_project_connection(
    project: dict[str, str],
) -> None:
    try:
        connection = psycopg.connect(
            host=project["host"],
            port=project["port"],
            dbname=project["database"],
            user=project["user"],
            password=project["password"],
        )

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    current_database(),
                    current_user;
                """
            )

            database_name, user_name = cursor.fetchone()

        connection.close()

        ok(
            "Project account connection verified: "
            f"database={database_name}, user={user_name}"
        )

    except Exception as exc:
        fail(
            "The database was initialized, but the project "
            "account could not connect.\n\n"
            f"Details: {exc}"
        )


# ==========================================================
# Main
# ==========================================================

def main() -> None:
    section("Agent Harness Database Initialization")

    project = load_configuration()

    print("Project database configuration:")
    print(f"  Host:     {project['host']}")
    print(f"  Port:     {project['port']}")
    print(f"  Database: {project['database']}")
    print(f"  User:     {project['user']}")
    print("  Password: ********")
    print()

    if project["user"] == "postgres":
        fail(
            "DATABASE_USER is set to the PostgreSQL "
            "administrator account 'postgres'.\n\n"
            "Use a dedicated project account instead."
        )

    admin = get_admin_configuration(project)

    section("Creating Project Role and Database")

    admin_connection = connect_as_admin(admin)

    try:
        create_or_update_role(
            admin_connection,
            project["user"],
            project["password"],
        )

        create_database(
            admin_connection,
            project["database"],
            project["user"],
        )

    finally:
        admin_connection.close()

    configure_database(
        admin,
        project,
    )

    section("Verifying Project Database")

    verify_project_connection(project)

    section("Database Initialization Complete")

    print("The local Agent Harness PostgreSQL database is ready.")
    print()
    print("Configured:")
    print(f"  Database: {project['database']}")
    print(f"  User:     {project['user']}")
    print(f"  Host:     {project['host']}")
    print(f"  Port:     {project['port']}")
    print()
    print(
        "Application-specific tables or demo datasets can now "
        "be loaded into this database."
    )
    print()
    print(
        "Run this script again if you change the local project "
        "database password in .env."
    )


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print()
        warn("Database initialization cancelled.")
        sys.exit(130)