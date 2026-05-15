# Technical Documentation

## Architecture overview

```
POST /query
    │
    ▼
QueryRequest           pydantic validation (min 5, max 500 chars)
    │
    ▼
query_mentions_schema  semantic gate — rejects off-topic questions
    │
    ▼
PromptBuilder          schema metadata + few-shot examples → prompt string
    │
    ▼
LLMService             Groq API (llama3-8b), cached by (user_query, prompt)
    │                  _clean() strips markdown, prefixes, whitespace
    │
    ▼
is_safe_sql            whitelist: keywords, functions, tables, columns
    │                  rejects: subqueries, JOINs, UNIONs, comments, DDL
    │  (invalid → fallback prompt → retry once)
    ▼
SQLExecutor            _parametrize() → bind params → SQLAlchemy execute()
    │
    ▼
QueryResponse          sql, result, row_count, cached, timing metrics
```

## Schema design

The three-table schema represents a commercial ERP module:

- **clientes** — customer registry with market segment and location
- **produtos** — product/service catalog with pricing and stock
- **pedidos** — sales orders linking customers to products

The schema.json file provides column-level descriptions that are injected into the LLM prompt, enabling the model to understand business context (e.g., "status: aprovado, pendente ou cancelado").

## Validation layers

| Layer | Where | What it checks |
|-------|-------|----------------|
| Input length | Pydantic | min 5, max 500 chars |
| Semantic gate | `query_mentions_schema()` | schema term presence |
| LLM output cleaning | `_clean()` | removes fences, prefixes |
| SQL safety | `is_safe_sql()` | whitelist of all tokens |
| String parametrization | `_parametrize()` | bind params for literals |
| Rate limiting | slowapi middleware | per-IP, configurable |

## Extending the schema

To add a new table:

1. Add DDL and seed data to `schema.sql`
2. Add table metadata to `schema.json`
3. Add relevant few-shot examples to `prompt_builder.py`
4. The validator automatically allows the new table and columns

## Swapping the LLM

Replace `LLMService` with any class implementing:

```python
def generate_sql(self, user_query: str, prompt: str) -> str: ...

@property
def last_inference_ms(self) -> float: ...

def cache_info(self): ...  # must return object with .hits attribute
```

The rest of the pipeline is LLM-agnostic.

## Connecting to a production database

Change `DATABASE_URL` in `.env`. SQLAlchemy supports PostgreSQL, MySQL, MSSQL and others with the appropriate driver (e.g. `psycopg2` for Postgres).

## Known gaps (intentional for demo scope)

| Gap | Production fix |
|-----|----------------|
| No authentication | JWT / API key middleware |
| In-memory rate limiting | Redis-backed slowapi storage |
| No JOINs | Prompt engineering with relationship descriptions |
| No audit logging | Structured log sink (Datadog, CloudWatch) |
| SQLite | PostgreSQL + connection pooling |
