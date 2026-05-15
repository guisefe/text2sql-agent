# Design Decisions

## 1. Groq API over local models

Local models (flan-t5, bloomz) run on CPU and generate incorrect SQL ~40% of the time for non-trivial queries. Groq's free tier provides llama3-8b with ~90% accuracy on simple SQL, 14,400 requests/day at no cost, and millisecond latency. For a demo, quality matters more than offline capability.

## 2. ERP schema — commercial module

The schema (clientes, produtos, pedidos) mirrors the core of a commercial ERP module — the kind found in systems like Londrisoft Gestor. This makes the demo contextually relevant for data engineering roles in the ERP/SaaS space.

## 3. Whitelist validator over blacklist

Blacklists miss edge cases. The validator allows only explicitly approved tokens: SQL keywords, aggregate functions, table names, column names from schema.json, and safe literals. Everything else is rejected by default.

## 4. String literal parametrization in executor

Even after whitelist validation, string literals are extracted and replaced with SQLAlchemy bind parameters. This adds a second layer of injection protection independent of the validator.

## 5. Semantic gate

Before calling the LLM, the query is checked against schema terms (table names, column names, singular forms). Queries with no match are rejected immediately — no wasted API call.

## 6. Retry with fallback prompt

When the LLM generates invalid SQL on first attempt, the agent retries once with a prompt that includes the invalid SQL as context. This improves success rate on ambiguous questions without adding dependencies.

## 7. Cache by (user_query, prompt)

Caching by user_query alone would return stale results if the prompt changes. Caching by prompt alone wastes memory on long strings. The tuple key balances correctness and efficiency.

## 8. Sync endpoints (not async)

Groq API calls are I/O-bound but use the synchronous groq client. FastAPI dispatches sync endpoints to a thread pool automatically. Using `async def` with a sync client would block the event loop.

## 9. No JOINs

JOINs are blocked by the validator intentionally. A correct JOIN requires the LLM to know foreign key relationships — this would need additional prompt engineering (relationship descriptions, more examples) beyond the scope of this demo. Documented as a known limitation.

## 10. SQLite for demo, SQLAlchemy for portability

SQLite requires zero setup. SQLAlchemy abstracts the engine — swapping to PostgreSQL or MySQL only requires changing DATABASE_URL.
