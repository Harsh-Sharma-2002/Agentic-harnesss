import asyncio
import json

from src.agents.text2sql.sql_agent.graph import sql_agent_graph


async def main():
    result = await sql_agent_graph.ainvoke(
        {
            "query": "How many customers are there?",
            "database_id": "ecommerce",
        }
    )

    print(
        json.dumps(
            {
                "response": result["response"],
                "final_sql": result["final_sql"],
                "sql_results": result["sql_results"],
                "retry_count": result["retry_count"],
            },
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
