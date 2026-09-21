---
name: text2sql-native-loop
description: >
  Answer a natural-language question about the ecommerce Postgres database
  by exploring its schema and querying it directly. Use when the user asks
  something like "how many customers are there" or "which state has the
  most orders" and wants a grounded, data-backed answer. This is a sample
  implementation of the same task the repo's Text2SQL LangGraph agent
  performs (src/agents/text2sql/sql_agent/), rebuilt as the plain unbounded
  agent loop described in the lecture's last slide (assemble context ->
  model decides -> tool call executes -> result recorded -> repeat) instead
  of a hand-built bounded state machine.
---

# Text2SQL via the native agent loop

**Why this exists:** the repo's `sql_agent` graph does this same job with 11
LangGraph nodes, four `with_structured_output` calls
(`ContextDecision`/`DiscoveryDecision`/`SQLDecision`/`SQLResponse`), an
explicit `active_loop` dispatcher, a hard `MAX_DISCOVERY_ITERATIONS = 4`
cap, and a persistent `schema_registry.json` written/read across requests.
None of that is being reimplemented here. This skill leans entirely on the
loop you (the agent reading this) already run natively — read state, decide,
act, observe, repeat, until you have nothing left to call a tool for. The
graph's four booleans (`sufficient`, `discovery_complete`,
`execution_complete`, and the final answer) collapse into one thing: you
deciding, turn by turn, whether to run another query or give the answer.

There is no fixed iteration budget. Keep going — inspect schema, run
queries, re-check results — for as long as it genuinely takes. Stop the
moment you can answer confidently, not before.

## Connecting

The database is the same `ecommerce` Postgres instance the rest of this
repo uses. Read credentials the same way the app does — prefer
`.env.local` (native run) and fall back to `.env` (Docker defaults) if it
doesn't exist:

```bash
cd <repo_root>
ENV_FILE=".env.local"; [ -f "$ENV_FILE" ] || ENV_FILE=".env"
set -a && source "$ENV_FILE" && set +a

psql "host=$DATABASE_HOST port=$DATABASE_PORT dbname=$DATABASE_NAME \
      user=$DATABASE_USER password=$DATABASE_PASSWORD"
```

Every `psql` session — including one-off `-c` invocations — starts with:

```sql
SET TRANSACTION READ ONLY;
```

This is the same defense-in-depth the graph's `run_sql` tool applies
(`sql_agent/tools.py`): even if every instruction below is somehow ignored,
Postgres itself refuses to execute a write.

## Hard rules (non-negotiable, not a suggestion to reason about)

- **Read-only. No exceptions.** Never run `INSERT`, `UPDATE`, `DELETE`,
  `DROP`, `ALTER`, `TRUNCATE`, `CREATE`, `GRANT`, or `REVOKE` — the same
  forbidden list `validator_node.py` enforces in the graph version.
- **Every query must start with `SELECT`.** Not "must not contain a write
  keyword" — must literally begin with it. This is what
  `_validate_single_query` actually checks (`validator_node.py:125-127`),
  and it's stricter than a blocklist: a read-only CTE that opens with
  `WITH` still gets rejected there, so match that exactly rather than the
  softer "no destructive keywords" version.
- **One statement per query, no `;`-chaining.** The graph rejects any
  candidate query containing a semicolon before its own trailing one
  (`validator_node.py:141-145`) — this is what stops
  `SELECT 1; DROP TABLE customers` from riding in as a single "query."
  Run one statement per `psql -c`/query, never a chained batch.
- **Never invent a fact you didn't query for.** If you don't know a table
  or column exists, go look — don't guess at a name and hope. This mirrors
  `discovery_node.py`'s "do not invent unsupported facts" instruction and
  `response_node.py`'s "grounded only in the provided SQL results" rule.
- **Every number in your final answer must trace back to a query you
  actually ran and actually saw the output of**, in this same
  conversation. If you're not sure, run one more query — don't round up to
  "probably."

## The loop, in practice

1. **Do you already know the relevant schema?** Check
   `schema_notes.md` at the repo root first, if it exists (see
   *Persisting schema knowledge* below) — that may already answer this.
   If you're still unsure which tables/columns are relevant, inspect
   `information_schema` before guessing:
   ```sql
   SELECT table_name FROM information_schema.tables
   WHERE table_schema = 'public';

   SELECT column_name, data_type FROM information_schema.columns
   WHERE table_name = '<table>';
   ```
2. **Run the query that answers the question.** Simple questions are one
   query. Multi-part questions ("which state has the most customers, and
   who are its 3 most recent signups") are naturally two or more. One
   difference from the graph worth naming, not smoothing over: its
   `executor_node.py` fires an entire batch of independent queries
   concurrently via `asyncio.gather` (line 102) when one reasoning turn
   asks for several at once. You don't have that for free — running
   queries yourself, one at a time, is the honest native-loop version.
   It's still fine, just slower on a multi-query turn, not "the same way."
3. **Look at what actually came back before trusting it.** Be precise
   about what this replaces: `verifier_node.py` only checks *structural*
   validity — the query succeeded, `columns`/`rows`/`row_count` are all
   present, and `row_count == len(rows)` (lines 213–255). Its own
   docstring says it explicitly: "it does not decide whether the results
   semantically satisfy the user's request — that decision belongs to the
   active reasoning loop." So you're not replacing the verifier here, you're
   replacing the *reasoner's own* semantic check — does this row count make
   sense, does an empty result mean "zero" or "wrong query," does this
   actually answer what was asked — which in the graph happens one step
   later anyway, inside `DiscoveryDecision`/`SQLDecision`.
4. **Not enough yet? Run another query.** No cap, no "iteration 3 of 4"
   budget message — just keep going as long as it's genuinely productive.
   If you notice you're repeating the same failed query with no new
   information, that's your own signal to stop and say what you don't
   know, rather than a framework cutting you off.
5. **Answer in plain language**, grounded only in what you queried. State
   the number/fact directly; don't paste raw query output unless the user
   asked for it.

## Persisting schema knowledge (optional, but do it)

The graph version's `schema_registry.json` is the only thing that survives
across requests — everything else in `SQLAgentState` is thrown away per
call. You can get the same benefit without a registry file or a merge
step: after answering, if you learned something about the schema that
wasn't already written down, append it to `schema_notes.md` at the repo
root (create it if it doesn't exist) — table purposes, column meanings,
relationships you had to work out. Keep it short and factual, plain
Markdown, no fabricated detail. Next time this skill runs, step 1 reads
that file first, so the discovery cost is paid once, not every
conversation — same idea as the registry, different storage.


about *which* guarantees,
not all of them equally. That precision *is* the lecture.
