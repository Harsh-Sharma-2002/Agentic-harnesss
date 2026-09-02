# LangChain Message Types

Every message in LangChain inherits from **BaseMessage**.

```text
BaseMessage
│
├── SystemMessage
├── HumanMessage
├── AIMessage
└── ToolMessage ...
```

The conversation history is simply

```python
list[AnyMessage]
```

where `AnyMessage` means "any valid LangChain message."

---

# BaseMessage (Common Fields)

Every message contains these important fields.

```python
class BaseMessage:
    content: str | list
    id: str | None
    name: str | None
    response_metadata: dict
    additional_kwargs: dict
    type: str
```

| Field | Purpose |
|--------|---------|
| `content` | The actual message text (or multimodal content). |
| `id` | Optional unique identifier. |
| `name` | Optional sender name. |
| `response_metadata` | Metadata returned by the model (token usage, finish reason, etc.). |
| `additional_kwargs` | Extra provider-specific information (tool calls, function calls, etc.). |
| `type` | Message type (`human`, `ai`, `system`, ...). |

---

# HumanMessage

Represents user input.

```python
HumanMessage(
    content="What are the latest developments in agentic AI?"
)
```

```text
type = "human"
```

---

# AIMessage

Represents the LLM's response.

```python
AIMessage(
    content="OpenAI recently announced..."
)
```

Can also contain:

- tool calls
- response metadata
- model-specific information

```text
type = "ai"
```

---

# SystemMessage

Instructions given to the model.

```python
SystemMessage(
    content="You are a helpful assistant."
)
```

Not written by the user.

Used to control model behavior.

```text
type = "system"
```

---

# AnyMessage

```python
messages: list[AnyMessage]
```

Allows the conversation history to contain different message types.

Example

```python
messages = [
    SystemMessage(...),
    HumanMessage(...),
    AIMessage(...),
]
```

---

# In Your GlobalState

```python
messages: Annotated[
    list[AnyMessage],
    add_messages,
]
```

- `list[AnyMessage]` → Conversation history.
- `add_messages` → Merge new messages into the existing history instead of replacing it.

```python
Current:
[HumanMessage("Hello")]

Node returns:
[AIMessage("Hi!")]

Result:
[
    HumanMessage("Hello"),
    AIMessage("Hi!")
]
```