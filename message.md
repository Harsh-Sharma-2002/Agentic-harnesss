# LangChain Message Schemas

In LangChain, all conversation messages inherit from a common base type called `AnyMessage`.

Think of it like this:

```text
                BaseMessage
                     │
      ┌──────────────┼──────────────┐
      │              │              │
SystemMessage   HumanMessage    AIMessage
                     │
                     └──────► AnyMessage
```

`AnyMessage` is simply a union of all supported message types.

---

# AnyMessage

```python
AnyMessage

= HumanMessage
| AIMessage
| SystemMessage
| ToolMessage
| FunctionMessage
| ...
```

It allows the conversation history to contain different kinds of messages.

Example:

```python
messages = [
    SystemMessage(...),
    HumanMessage(...),
    AIMessage(...),
]
```

---

# HumanMessage

Represents something the **user** says.

## Simplified Schema

```python
class HumanMessage:
    content: str
```

## Example

```python
HumanMessage(
    content="What are the latest developments in agentic AI?"
)
```

---

# AIMessage

Represents something produced by the **LLM**.

## Simplified Schema

```python
class AIMessage:
    content: str
```

## Example

```python
AIMessage(
    content="OpenAI recently announced..."
)
```

---

# SystemMessage

Represents **instructions** given to the model.

The user never sees this message.

It controls the model's behavior.

## Simplified Schema

```python
class SystemMee a helpful assistant.
Always answer using bullet points.
"""
)
```

---

# BaseMessage (Simplified)

Internally, all message types inherit from the same base class.

```python
class BaseMessage:
    content: str
    type: str
```

Examples:

```text
HumanMessage
type = "human"

AIMessage
type = "ai"

SystemMessage
type = "system"
```

---

# Why use message objects instead of strings?

Instead of storing

```python
[
    "Hello",
    "Hi",
    "How are you?"
]
```

LangChain stores

```python
[
    HumanMessage("Hello"),
    AIMessage("Hi"),
    HumanMessage("How are you?")
]
```

Now the framework knows **who said what**.

That becomes important when sending conversation history to an LLM.

---

# How this appears in your GlobalState

```python
messages: Annotated[
    list[AnyMessage],
    add_messages,
]
```

This means:

- `list[AnyMessage]` → the conversation history can contain different message types.
- `add_messages` → when a node returns new messages, LangGraph merges them into the existing conversation instead of replacing it.

Example:

Current state

```python
messages = [
    HumanMessage("Hello")
]
```

Node returns

```python
messages = [
    AIMessage("Hi!")
]
```

After the reducer

```python
messages = [
    HumanMessage("Hello"),
    AIMessage("Hi!")
]
```

The conversation history is preserved automatically.

---

# Mental Model

```text
SystemMessage
│
├── Instructions to the LLM
│

HumanMessage
│
├── User input
│

AIMessage
│
├── Model output
│

AnyMessage
│
└── A list that can contain all of the above
```
