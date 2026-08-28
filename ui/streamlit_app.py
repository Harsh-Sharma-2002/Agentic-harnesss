# ui/streamlit_app.py

from __future__ import annotations

import os
from typing import Any

import httpx
import streamlit as st


# ==========================================================
# Configuration
# ==========================================================

API_BASE_URL = os.getenv(
    "AGENT_HARNESS_API_URL",
    "http://127.0.0.1:8000",
)

QUERY_ENDPOINT = (
    f"{API_BASE_URL}/api/v1/query"
)

HEALTH_ENDPOINT = (
    f"{API_BASE_URL}/health"
)

# Agent execution can take a while locally.
REQUEST_TIMEOUT = 180.0


# ==========================================================
# Page Configuration
# ==========================================================

st.set_page_config(
    page_title="Agent Harness",
    page_icon="🤖",
    layout="centered",
)


# ==========================================================
# Session State
# ==========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []


# ==========================================================
# API Helpers
# ==========================================================

def check_backend_health() -> bool:
    """
    Check whether the FastAPI service is reachable.

    This checks only the lightweight /health endpoint.
    """

    try:
        response = httpx.get(
            HEALTH_ENDPOINT,
            timeout=5.0,
        )

        return (
            response.status_code == 200
            and response.json().get("status")
            == "ok"
        )

    except (
        httpx.HTTPError,
        ValueError,
    ):
        return False


def send_query(
    query: str,
) -> dict[str, Any]:
    """
    Send one user query to the Agent Harness API.

    Streamlit communicates only with FastAPI and has no
    knowledge of LangGraph or private agents.
    """

    response = httpx.post(
        QUERY_ENDPOINT,
        json={
            "query": query,
        },
        timeout=None,
    )

    response.raise_for_status()

    return response.json()


# ==========================================================
# Rendering Helpers
# ==========================================================

def get_agent_label(
    agent: str,
) -> str:
    """
    Return a human-readable label for an agent.
    """

    labels = {
        "text2sql": "Text2SQL",
        "web_search": "Web Search",
        "none": "No Suitable Agent",
    }

    return labels.get(
        agent,
        agent,
    )


def render_sql_details(
    metadata: dict[str, Any],
) -> None:
    """
    Render public Text2SQL execution metadata.
    """

    sql_queries = metadata.get(
        "sql",
        [],
    )

    database_id = metadata.get(
        "database_id"
    )

    if database_id:
        st.caption(
            f"Database: {database_id}"
        )

    if not sql_queries:
        return

    st.markdown("**Generated SQL**")

    for index, sql in enumerate(
        sql_queries,
        start=1,
    ):
        if len(sql_queries) > 1:
            st.caption(
                f"Query {index}"
            )

        st.code(
            sql,
            language="sql",
        )


def render_web_details(
    metadata: dict[str, Any],
) -> None:
    """
    Render public Web Search execution metadata.
    """

    search_query = metadata.get(
        "search_query"
    )

    sources = metadata.get(
        "sources",
        [],
    )

    if search_query:
        st.markdown(
            "**Search query**"
        )

        st.code(
            search_query,
            language=None,
        )

    if not sources:
        return

    st.markdown(
        "**Sources**"
    )

    for source in sources:

        title = source.get(
            "title",
            "Source",
        )

        url = source.get(
            "url"
        )

        snippet = source.get(
            "snippet"
        )

        if url:
            st.markdown(
                f"- [{title}]({url})"
            )
        else:
            st.markdown(
                f"- {title}"
            )

        if snippet:
            st.caption(
                snippet
            )


def render_execution_details(
    *,
    agent: str,
    metadata: dict[str, Any],
) -> None:
    """
    Render public agent-specific execution details.
    """

    with st.expander(
        "Execution details",
        expanded=False,
    ):

        intent = metadata.get(
            "intent"
        )

        confidence = metadata.get(
            "confidence"
        )

        st.markdown(
            f"**Agent:** "
            f"{get_agent_label(agent)}"
        )

        if intent:
            st.markdown(
                f"**Intent:** `{intent}`"
            )

        if confidence is not None:
            st.markdown(
                f"**Routing confidence:** "
                f"{confidence:.2f}"
            )

        st.divider()

        if agent == "text2sql":
            render_sql_details(
                metadata
            )

        elif agent == "web_search":
            render_web_details(
                metadata
            )

        elif agent == "none":
            st.caption(
                "The orchestrator determined that "
                "none of the currently available agents "
                "could handle this request."
            )


def render_assistant_message(
    message: dict[str, Any],
) -> None:
    """
    Render one stored assistant response.
    """

    st.markdown(
        message["content"]
    )

    agent = message.get(
        "agent"
    )

    metadata = message.get(
        "metadata",
        {},
    )

    request_id = message.get(
        "request_id"
    )

    if agent:
        st.caption(
            f"Handled by "
            f"{get_agent_label(agent)}"
        )

    if agent:
        render_execution_details(
            agent=agent,
            metadata=metadata,
        )

    if request_id:
        st.caption(
            f"Request ID: {request_id}"
        )


# ==========================================================
# Header
# ==========================================================

st.title(
    "Agent Harness"
)

st.caption(
    "Ask questions across connected data and the web."
)


# ==========================================================
# Backend Status
# ==========================================================

backend_healthy = (
    check_backend_health()
)

if backend_healthy:
    st.success(
        "Backend connected",
        icon="✅",
    )

else:
    st.error(
        (
            "Backend is unavailable. "
            "Start the FastAPI server and refresh."
        ),
        icon="🚨",
    )


# ==========================================================
# Existing Conversation
# ==========================================================

for message in st.session_state.messages:

    role = message["role"]

    with st.chat_message(
        role
    ):

        if role == "assistant":
            render_assistant_message(
                message
            )

        else:
            st.markdown(
                message["content"]
            )


# ==========================================================
# Chat Input
# ==========================================================

prompt = st.chat_input(
    "Ask a question...",
    disabled=not backend_healthy,
)


# ==========================================================
# Handle New Request
# ==========================================================

if prompt:

    normalized_prompt = (
        prompt.strip()
    )

    if normalized_prompt:

        # ==================================================
        # Store + render user message
        # ==================================================

        user_message = {
            "role": "user",
            "content": normalized_prompt,
        }

        st.session_state.messages.append(
            user_message
        )

        with st.chat_message(
            "user"
        ):
            st.markdown(
                normalized_prompt
            )

        # ==================================================
        # Execute API request
        # ==================================================

        with st.chat_message(
            "assistant"
        ):

            with st.spinner(
                "Working on your request..."
            ):

                try:
                    response = send_query(
                        normalized_prompt
                    )

                # ==========================================
                # HTTP status error
                # ==========================================

                except httpx.HTTPStatusError as exc:

                    status_code = (
                        exc.response.status_code
                    )

                    try:
                        error_body = (
                            exc.response.json()
                        )

                        detail = error_body.get(
                            "detail",
                            "Request failed.",
                        )

                    except ValueError:
                        detail = (
                            "Request failed."
                        )

                    error_message = (
                        f"Backend request failed "
                        f"(HTTP {status_code}): "
                        f"{detail}"
                    )

                    st.error(
                        error_message
                    )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": error_message,
                        }
                    )

                # ==========================================
                # Network / timeout error
                # ==========================================

                except httpx.RequestError as exc:

                    error_message = (
                        "Could not communicate with "
                        "the Agent Harness API."
                    )

                    if isinstance(
                        exc,
                        httpx.TimeoutException,
                    ):
                        error_message = (
                            "The agent request timed out. "
                            "The backend may still be processing it."
                        )

                    st.error(
                        error_message
                    )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": error_message,
                        }
                    )

                # ==========================================
                # Unexpected response
                # ==========================================

                except Exception:

                    error_message = (
                        "An unexpected frontend error occurred."
                    )

                    st.error(
                        error_message
                    )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": error_message,
                        }
                    )

                # ==========================================
                # Success
                # ==========================================

                else:

                    answer = response.get(
                        "answer",
                        ""
                    )

                    agent = response.get(
                        "agent"
                    )

                    metadata = response.get(
                        "metadata",
                        {},
                    )

                    request_id = response.get(
                        "request_id"
                    )

                    assistant_message = {
                        "role": "assistant",
                        "content": answer,
                        "agent": agent,
                        "metadata": metadata,
                        "request_id": request_id,
                    }

                    st.session_state.messages.append(
                        assistant_message
                    )

                    render_assistant_message(
                        assistant_message
                    )


# ==========================================================
# Sidebar
# ==========================================================

with st.sidebar:

    st.header(
        "Agent Harness"
    )

    st.caption(
        "Available agents"
    )

    st.markdown(
        """
- **Text2SQL** — connected database queries
- **Web Search** — current and external information
"""
    )

    st.divider()

    st.caption(
        f"API: {API_BASE_URL}"
    )

    if st.button(
        "Clear conversation",
        use_container_width=True,
    ):
        st.session_state.messages = []
        st.rerun()