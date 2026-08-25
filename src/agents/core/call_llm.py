from langchain_ollama import ChatOllama


_llm = ChatOllama(
    model="qwen3:4b",
    temperature=0,
)


def get_llm() -> ChatOllama:
    """
    Return the shared LLM client used by agents.
    """
    return _llm


async def call_llm(messages):
    """
    Invoke the shared LLM asynchronously.
    """
    return await _llm.ainvoke(messages)
