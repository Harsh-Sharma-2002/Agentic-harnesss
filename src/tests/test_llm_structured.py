from __future__ import annotations

import asyncio
from typing import Literal

from pydantic import BaseModel, Field

from src.agents.core.call_llm import get_llm


class RoutingDecision(BaseModel):
    intent: str

    selected_agent: Literal[
        "text2sql",
        "web_search",
        "none",
    ]

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )


PROMPT = """
You are the routing component of an agent system.

Select exactly one agent.

Available agents:

text2sql:
Use for requests that should be answered using the connected
application database.

web_search:
Use for requests requiring public or current web information.

none:
Use when neither agent is suitable.

User request:
{query}

Return:
- intent
- selected_agent
- confidence
"""


async def main():
    llm = get_llm()

    routing_llm = llm.with_structured_output(
        RoutingDecision
    )

    queries = [
        "What is the latest news about OpenAI?",
        "How many customers are in the database?",
        "Write me a Python implementation of merge sort.",
        "How many orders exist in the database?",
        "What happened in the news today?",
    ]

    for index, query in enumerate(
        queries,
        start=1,
    ):
        print(
            f"\n===== CALL {index} =====",
            flush=True,
        )

        print(
            query,
            flush=True,
        )

        try:
            result = await routing_llm.ainvoke(
                PROMPT.format(
                    query=query
                )
            )

            print(
                result.model_dump(),
                flush=True,
            )

        except Exception as exc:
            print(
                f"FAILED: {type(exc).__name__}: {exc}",
                flush=True,
            )


if __name__ == "__main__":
    asyncio.run(main())
