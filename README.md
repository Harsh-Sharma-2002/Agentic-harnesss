# Agent Harness

A modular multi-agent orchestration harness built with **LangGraph**, **LangChain**, **FastAPI**, and **Streamlit**.

The system accepts a user request, determines which specialized agent should handle it, executes that agent through an isolated private graph, and returns a unified response through a shared orchestration layer.

The current harness includes:

- **Base Orchestrator** for intent classification and agent routing
- **Text2SQL Agent** with bounded schema discovery and iterative SQL reasoning
- **Web Search Agent** for current and external information
- **FastAPI** HTTP interface
- **Streamlit** conversational UI
- **LangSmith** tracing and observability
- Structured semantic execution events for runtime visibility

---

## Architecture

```text
                           User
                            │
                            ▼
                     Streamlit UI
                            │
                         HTTP
                            │
                            ▼
                       FastAPI
                            │
                            ▼
                     ┌────────────┐
                     │ Base Agent │
                     └─────┬──────┘
                           │
                     Orchestrator
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
          Text2SQL     Web Search      None
              │            │
              ▼            ▼
       Private Graph   Private Graph
              │
              ▼
       Agent Response
              │
              └────────────┐
                           ▼
                     Global State
                           │
                           ▼
                        FastAPI
                           │
                           ▼
                          User
```

The Base Agent owns orchestration but does not perform specialized work itself.

Each specialized agent maintains its own private state and execution graph. Only public results are translated back into the shared `GlobalState`.

---

## Core Design Principles

### Orchestrator, not monolith

The Base Agent is intentionally small.

Its responsibilities are limited to:

1. Initializing shared request state
2. Classifying the request
3. Selecting an available agent
4. Handing execution to that agent
5. Translating the private result back into public state

Agent-specific reasoning remains isolated inside private graphs.

### Private agent state

Specialized agents do not directly modify the global orchestration state.

```text
GlobalState
    │
    ▼
Handoff Adapter
    │
    ▼
Private Agent State
    │
    ▼
Agent Execution
    │
    ▼
Public Result
    │
    ▼
GlobalState
```

This prevents implementation details from leaking between agents and makes additional agents easier to integrate.

### State is execution truth

LangGraph state represents the current execution state of each agent.

LLMs make bounded reasoning decisions, while deterministic nodes handle validation, execution, verification, routing, and persistence.

### Structured LLM outputs

Reasoning and routing decisions use Pydantic structured outputs instead of parsing arbitrary natural-language responses.

The shared LLM layer also provides bounded retries for malformed structured responses.

---

# Agents

## Base Agent

The Base Agent routes requests to one of the currently available agents:

| Agent | Responsibility |
|---|---|
| `text2sql` | Queries the connected application database |
| `web_search` | Retrieves current/public information from the web |
| `none` | Used when no available agent can safely handle the request |

Example routing:

```text
"How many customers are in the database?"
                    │
                    ▼
                 text2sql
```

```text
"What are the latest developments in agentic AI?"
                    │
                    ▼
                web_search
```

```text
"Write a Python implementation of merge sort."
                    │
                    ▼
                   none
```

The orchestrator returns a structured routing decision containing:

```json
{
  "intent": "database_query",
  "selected_agent": "text2sql",
  "confidence": 0.95
}
```

---

# Text2SQL Agent

The Text2SQL agent is the most involved execution graph in the harness.

It combines:

- Persistent schema knowledge
- Schema-context sufficiency checking
- Bounded database discovery
- Iterative SQL reasoning
- Deterministic SQL validation
- Database execution
- Result verification
- Final grounded response generation

## Text2SQL Flow

```text
                      START
                        │
                        ▼
                       Init
                        │
                        ▼
                 Load Registry
                        │
                        ▼
                 Context Check
                        │
              ┌─────────┴─────────┐
              │                   │
         insufficient         sufficient
              │                   │
              ▼                   │
          Discovery               │
              │                   │
       ┌──────┴──────┐            │
       │             │            │
    incomplete    complete         │
       │             │            │
       ▼             ▼            │
   Validator    Update Registry    │
       │             │            │
       ▼             │            │
   Executor          │            │
       │             │            │
       ▼             │            │
   Verifier          │            │
       │             │            │
       └── Discovery │            │
                     │            │
                     └─────┬──────┘
                           ▼
                     SQL Reasoner
                           │
                    ┌──────┴──────┐
                    │             │
                 more SQL      complete
                    │             │
                    ▼             ▼
                Validator      Response
                    │             │
                    ▼             ▼
                Executor         END
                    │
                    ▼
                Verifier
                    │
                    └──────► SQL Reasoner
```

---

## Persistent Schema Registry

Text2SQL maintains reusable database knowledge in:

```text
src/agents/text2sql/schema_registry.json
```

The registry acts as lightweight long-term schema memory.

For every request:

1. Existing schema knowledge is loaded.
2. The Context Check determines whether that knowledge is sufficient.
3. Discovery is skipped when the required schema is already known.
4. Missing schema information is discovered when necessary.
5. Newly discovered reusable application-schema knowledge is merged into the registry.

This avoids rediscovering the same database structure on every request.

---

## Bounded Schema Discovery

Schema discovery is intentionally bounded.

```text
MAX_DISCOVERY_ITERATIONS = 4
```

The discovery reasoner receives its current budget:

```text
Current discovery iteration: 3
Maximum discovery iterations: 4
Remaining discovery iterations after this one: 1
```

This encourages targeted metadata discovery instead of unrestricted exploration.

Discovery is instructed to:

- Discover only information necessary for the current SQL request
- Reuse metadata already present in conversation history
- Avoid repeated catalog queries
- Treat confirmed absence as useful information
- Avoid attempting to reconstruct the entire database schema
- Never fabricate schema information when the budget is ending

---

## Shared SQL Execution Pipeline

Both schema discovery and user-facing SQL reasoning reuse the same deterministic execution pipeline:

```text
Reasoner
   │
   ▼
Validator
   │
   ▼
Executor
   │
   ▼
Verifier
   │
   ▼
Reasoner
```

The currently active loop determines where execution returns.

```text
active_loop = "discovery"
```

or:

```text
active_loop = "sql"
```

This avoids maintaining duplicate validation/execution logic.

---

## SQL Safety

Candidate SQL is validated before execution.

The current validator enforces:

- Read-only `SELECT` statements
- One statement per candidate query
- No destructive SQL operations

Forbidden operations include:

```text
INSERT
UPDATE
DELETE
DROP
ALTER
TRUNCATE
CREATE
GRANT
REVOKE
```

SQL is executed only after validation succeeds.

Execution results then pass through deterministic structural verification before becoming trusted evidence for the final response.

---

## Iterative SQL Reasoning

The SQL reasoner does not assume that one database query will always be sufficient.

It can repeatedly:

```text
Reason
  ↓
Generate SQL
  ↓
Validate
  ↓
Execute
  ↓
Verify
  ↓
Reason again
```

Verified SQL results accumulate across iterations until enough evidence exists to answer the complete user request.

Only verified results are used for final response generation.

---

# Web Search Agent

The Web Search Agent handles requests requiring external or current information.

Example:

```text
"What are the latest developments in agentic AI?"
```

Flow:

```text
Request
   │
   ▼
Generate Search Query
   │
   ▼
Web Search
   │
   ▼
Collect Sources
   │
   ▼
Generate Grounded Answer
   │
   ▼
Response
```

The response includes both the synthesized answer and the underlying sources.

---

# HTTP API

The harness exposes an HTTP interface using FastAPI.

## Health

```http
GET /health
```

Example response:

```json
{
  "status": "ok"
}
```

The health endpoint intentionally avoids invoking agents, Ollama, PostgreSQL, or external search services.

## Query

```http
POST /api/v1/query
```

Example:

```json
{
  "query": "How many customers are in the database?"
}
```

The API creates a unique request ID and invokes the Base Agent.

A request then follows:

```text
HTTP Request
     │
     ▼
Base Agent
     │
     ▼
Agent Selection
     │
     ▼
Private Agent
     │
     ▼
Result Translation
     │
     ▼
HTTP Response
```

---

# Streamlit UI

A lightweight conversational frontend is provided using Streamlit.

The UI displays:

- User messages
- Agent responses
- Selected agent
- Intent
- Routing confidence
- Generated SQL for database requests
- Web sources for search requests
- Request ID
- Execution details

Run it with:

```bash
streamlit run ui/streamlit_app.py
```

---

# Observability

The harness uses two complementary observability mechanisms.

## Semantic Runtime Events

Components emit structured execution events:

```python
emit(
    component="executor",
    event="execution_completed",
    message="SQL execution completed.",
    data={
        "query_count": 1,
        "row_count": 5,
    },
)
```

These provide readable runtime information such as:

```text
[Base Agent] Selecting an agent for the request.

[Context Check] Cached schema context is sufficient.

[Sql Reasoner] Additional database execution is required.

[Validator] SQL validation passed.

[Executor] SQL execution completed.
Rows: 1

[Verifier] SQL execution results verified.

[Response] Final Text2SQL response generated.
```

## LangSmith

LangSmith provides native tracing for the LangGraph/LangChain execution stack.

A complete request trace exposes:

```text
Base Graph
│
├── init
│
├── orchestrator
│   └── ChatOllama
│
└── handoff
    │
    └── Text2SQL
        ├── init
        ├── load_registry
        ├── context_check
        │   └── ChatOllama
        ├── sql_reasoner
        │   └── ChatOllama
        ├── validator
        ├── executor
        ├── verifier
        └── response
            └── ChatOllama
```

LangSmith provides visibility into:

- Graph execution hierarchy
- Nested agent execution
- Node latency
- LLM latency
- Model information
- Token usage
- Inputs and outputs
- Structured-output operations
- Failures and exceptions

This avoids maintaining a custom tracing backend while preserving detailed visibility into harness execution.

---

# Project Structure

```text
Agent_Harness/
├── data/
│   └── ecommerce.sql
│
├── src/
│   ├── agents/
│   │   ├── base/
│   │   │   └── base_agent/
│   │   │
│   │   ├── core/
│   │   │   └── call_llm.py
│   │   │
│   │   ├── text2sql/
│   │   │   ├── schema_registry.json
│   │   │   └── sql_agent/
│   │   │       ├── nodes/
│   │   │       ├── decisions.py
│   │   │       ├── graph.py
│   │   │       ├── state.py
│   │   │       └── tools.py
│   │   │
│   │   └── web_search/
│   │       └── web_agent/
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   └── query.py
│   │   ├── app.py
│   │   └── models.py
│   │
│   ├── core/
│   │   └── events.py
│   │
│   ├── observer/
│   │   ├── observer.py
│   │   ├── console.py
│   │   └── langsmith.py
│   │
│   └── tests/
│
├── ui/
│   └── streamlit_app.py
│
├── .env.example
├── requirements.txt
└── README.md
```

---

# Setup

## 1. Clone the repository

```bash
git clone <repository-url>
cd Agent_Harness
```

## 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

Windows:

```bash
venv\Scripts\activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

# Local LLM

The current harness uses Ollama with:

```text
qwen3.5:4b
```

Install Ollama and pull the model:

```bash
ollama pull qwen3.5:4b
```

Verify:

```bash
ollama list
```

The shared model configuration lives in:

```text
src/agents/core/call_llm.py
```

The LLM layer centralizes:

- Model configuration
- Structured-output generation
- Structured-output retries
- Raw response inspection
- Failure handling

---

# Environment Configuration

Create:

```text
.env
```

Do not commit this file.

Example:

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=<your-langsmith-api-key>
LANGSMITH_PROJECT=agent-harness

LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=<your-langsmith-api-key>
LANGCHAIN_PROJECT=agent-harness
```

Add any database/search credentials required by your local configuration as appropriate.

The application loads environment configuration before initializing the LangChain/LangGraph stack so API-originated requests are included in LangSmith tracing.

---

# Database

The repository contains the example ecommerce SQL data under:

```text
data/ecommerce.sql
```

Configure the PostgreSQL connection expected by the Text2SQL tools before running database queries.

The current Text2SQL implementation uses:

```text
database_id = ecommerce
```

as its default database identifier.

---

# Running the Harness

## Start the API

From the repository root:

```bash
uvicorn src.api.app:app
```

Development mode:

```bash
uvicorn src.api.app:app --reload
```

The API is available at:

```text
http://127.0.0.1:8000
```

Check:

```bash
curl http://127.0.0.1:8000/health
```

## Start the UI

In another terminal:

```bash
streamlit run ui/streamlit_app.py
```

The Streamlit application communicates with the FastAPI backend rather than invoking agents directly.

---

# Example Queries

## Database

```text
How many customers are in the database?
```

```text
Show me customers from California.
```

```text
Which states have the most customers? Show the top 5.
```

```text
Which five customers have placed the most orders?
```

## Web

```text
What are the latest developments in agentic AI?
```

```text
What are the latest major announcements from OpenAI?
```

## Unsupported

```text
Write me a Python implementation of merge sort.
```

When no available agent is appropriate, the Base Agent selects:

```text
none
```

rather than forcing the request into an unrelated agent.

---

# Testing

Tests are located under:

```text
src/tests/
```

The suite includes coverage for:

- Base Agent routing
- Structured LLM behavior
- Text2SQL execution
- Multi-loop SQL reasoning
- Web Search
- API behavior
- Full-system integration

Example:

```bash
PYTHONPATH=. python src/tests/test_system.py
```

Individual components can also be tested independently.

---

# Example End-to-End Execution

Request:

```text
How many customers are in the database?
```

Execution:

```text
User
 │
 ▼
FastAPI
 │
 ▼
Base Agent
 │
 ├── classify request
 │
 └── select text2sql
        │
        ▼
    Text2SQL
        │
        ├── load registry
        ├── check schema context
        ├── generate SQL
        │
        │   SELECT COUNT(*) FROM customers;
        │
        ├── validate SQL
        ├── execute SQL
        ├── verify result
        └── generate response
                │
                ▼
"There are 100 customers in the database."
```

The complete execution can simultaneously be inspected through LangSmith.

---

# Current Scope

Agent Harness v1 currently focuses on:

- Modular multi-agent orchestration
- Private agent execution graphs
- Text-to-SQL
- Web search
- Bounded schema discovery
- Persistent schema memory
- Deterministic SQL safety checks
- Structured LLM outputs
- HTTP serving
- Conversational UI
- Execution telemetry
- LangSmith tracing

The architecture is intentionally designed so additional specialized agents can be introduced without expanding the Base Agent into a monolithic reasoning system.

---

# Future Improvements

Potential extensions include:

- Additional specialized agents
- Configurable model providers
- Multiple database connections
- Stronger SQL parsing and AST-based validation
- SQL reasoning iteration limits
- Human-in-the-loop approval
- Streaming agent activity to the UI
- Richer semantic LangSmith annotations
- Authentication and authorization
- Persistent conversation sessions
- Deployment configuration
- Evaluation datasets and regression testing

---

## Status

**Agent Harness v1 — functional baseline complete.**

The current version supports end-to-end execution from:

```text
Streamlit
   ↓
FastAPI
   ↓
Base Orchestrator
   ↓
Specialized Agent
   ↓
Tools / LLM / Database
   ↓
Unified Response
```

with native LangSmith observability across the LangGraph execution hierarchy.