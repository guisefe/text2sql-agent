# Technical Documentation

## Architecture overview

```text
POST /query
    │
    ▼
QueryRequest             Pydantic input contract (5–500 chars)
    │
    ▼
query_mentions_schema    deterministic schema-relevance gate
    │
    ▼
PromptBuilder            schema metadata + few-shot examples
    │
    ▼
LLMService               Groq / llama-3.1-8b-instant
    │                     cached by (user_query, prompt)
    ▼
SQLExecutor
    ├── is_safe_sql       allowlisted read-only SQL contract
    ├── _parametrize      bind string literals
    └── SQLAlchemy        execute against SQLite demo database
    │
    ├── failure → one bounded fallback generation → validate again
    ▼
QueryResponse            SQL, rows, cache flag and timing metrics
```

The LLM proposes an action; deterministic code decides whether that action is allowed to execute.

## Schema design

The demo contains three ERP-style tables:

- **clientes** — customer registry, market segment and location;
- **produtos** — product/service catalog, pricing and stock;
- **pedidos** — sales orders linking a customer and product.

`schema.json` carries column-level descriptions that are injected into the model prompt. `schema.sql` is the executable demo schema and seed dataset. The two files are deliberately separate so model-facing metadata is explicit rather than inferred at runtime.

## Guardrails

| Layer | Implementation | Purpose |
|---|---|---|
| Request contract | Pydantic | rejects malformed/oversized questions |
| Domain gate | `query_mentions_schema()` | avoids off-domain inference calls |
| Output cleaning | `LLMService._clean()` | strips fences/prefix noise |
| SQL validation | `is_safe_sql()` | permits only the bounded SELECT surface |
| Literal binding | `SQLExecutor._parametrize()` | separates literal values from SQL text |
| Bounded retry | `/query` orchestration | allows one controlled self-correction |
| Rate limit | SlowAPI | limits requests per client |

The current validator rejects writes/DDL, comments, multiple statements, unknown schema identifiers, subqueries, UNIONs and JOINs.

## LLM boundary

`LLMService` owns provider-specific code. The API can boot without `GROQ_API_KEY`; `/health` remains available and `/query` returns a clear service-unavailable response until the provider is configured.

The current model is configurable through:

```text
GROQ_MODEL=llama-3.1-8b-instant
```

A future provider abstraction should be introduced when a second real provider is implemented, rather than adding an unused interface prematurely.

## Failure behavior

1. Off-domain question → reject before calling the LLM.
2. Missing provider configuration → HTTP 503.
3. Empty/invalid generation → controlled client error.
4. Unsafe or non-executable SQL → one fallback generation.
5. Second failure → stop; do not create an unbounded agent loop.

## Observability

Successful responses include:

- generated SQL;
- returned rows and row count;
- whether the generation came from cache;
- LLM inference latency;
- SQL execution latency;
- total request latency.

Production evolution should add request IDs, structured event logging, centralized metrics and model/token-cost telemetry.

## Tests and CI

The suite covers request validation, prompt construction, LLM-output cleaning, SQL safety rules, SQL execution and API integration with a mocked LLM. CI runs linting and tests on Python 3.11 and 3.12 and enforces an 85% coverage floor.

## Known gaps

| Gap | Production direction |
|---|---|
| No authentication | API key/JWT + authorization policy |
| In-memory rate limiting | shared Redis-backed limiter |
| No JOIN contract | relationship-aware generation + validator + evaluation set |
| SQLite demo database | production RDBMS, migrations and connection-pool tuning |
| No request-level tracing | request IDs + structured telemetry |
| Single provider | add a provider interface when a second implementation exists |
| Lexical domain gate | evaluate classifier/embedding routing only if domain scale requires it |
