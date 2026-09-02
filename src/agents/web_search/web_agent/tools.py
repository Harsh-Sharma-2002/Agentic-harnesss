# src/agents/web_search/web_agent/tools.py

from __future__ import annotations

import asyncio
from typing import Any

from langchain_core.tools import tool
from ddgs import DDGS ### Web Search Query


@tool
async def web_search(
    query: str,
) -> dict[str, Any]:
    """
    Search the web for information relevant to the given query.

    Returns a small set of search results containing titles,
    URLs, and text snippets.
    """

    def _search() -> dict[str, Any]:
        try:
            results = list(
                DDGS().text(
                    query,
                    max_results=5,
                )
            )

            search_results = [
                {
                    "title": item.get("title"),
                    "url": item.get("href"),
                    "snippet": item.get("body"),
                }
                for item in results
            ]

            return {
                "success": True,
                "error": None,
                "results": search_results,
            }

        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
                "results": [],
            }

    return await asyncio.to_thread(_search)
