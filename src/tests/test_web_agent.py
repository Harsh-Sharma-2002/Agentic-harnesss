# src/tests/test_web_agent.py

import asyncio
import json

from src.agents.web_search.web_agent.graph import web_agent_graph


async def main():
    result = await web_agent_graph.ainvoke(
        {
            "query": "What is the latest news about OpenAI?"
        }
    )

    print(
        json.dumps(
            {
                "search_query": result["search_query"],
                "search_results": result["search_results"],
                "response": result["response"],
                "error": result["error"],
            },
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())