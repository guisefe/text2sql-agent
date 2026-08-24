# Design Decisions

## 1. Hosted inference over a local model

This demo uses Groq-hosted inference with `llama-3.1-8b-instant`. The goal is to keep the local runtime lightweight while still exercising a real external LLM boundary. The provider is intentionally isolated in `LLMService` so the rest of the pipeline does not depend on Groq-specific code.

## 2. ERP schema as the bounded domain

The schema (`clientes`, `produtos`, `pedidos`) represents a small commercial ERP domain. Keeping the domain bounded makes it possible to demonstrate generation, validation, execution, failure handling and observability without hiding the core behavior behind a large dataset.

## 3. Deterministic guardrails around probabilistic generation

The LLM may propose SQL, but it never decides what is safe to execute. Safety is enforced by deterministic application code: one SELECT statement, one approved table, approved columns/functions, no comments, no subqueries, no UNIONs, no JOINs and no write/DDL operations.

## 4. String literal parametrization in the executor

After SQL validation, string literals are replaced with SQLAlchemy bind parameters before execution. This keeps user/model-generated values separate from the SQL statement and adds another defensive layer beyond token validation.

## 5. Cheap schema-relevance gate before inference

Before spending an LLM request, the application checks whether the question mentions a known table or column. This is intentionally a deterministic lexical gate, not an embedding-based semantic classifier. It is cheap, explainable and appropriate for this small demo domain.

## 6. One controlled retry

If the first generated SQL fails validation or execution, the agent gets one fallback attempt containing the rejected SQL plus the schema. The retry is bounded to avoid uncontrolled loops, excess latency and unnecessary model usage.

## 7. Cache by query and full prompt

The LLM result is cached by `(user_query, prompt)`. Including the full prompt prevents a result generated against an older schema/examples prompt from being reused after the prompt changes.

## 8. Sync endpoint with a sync provider client

The Groq client used here is synchronous. FastAPI dispatches a normal `def` endpoint to its thread pool, which avoids blocking the event loop with a synchronous external API call.

## 9. No JOINs in the demo contract

JOINs are deliberately outside the current execution contract. Multi-table generation requires relationship-aware validation and broader evaluation. For a live demo, a smaller verified SQL surface is preferable to a broader but weakly controlled one.

## 10. SQLite for zero-setup demonstration

SQLite keeps the demo self-contained. SQLAlchemy isolates most database access, but production portability is not claimed to be configuration-only: a real migration to PostgreSQL/MySQL would also require the correct driver, dialect-aware validation, operational configuration and production testing.

## 11. This is a single-purpose agentic workflow

The project is intentionally not a general autonomous agent. It is a bounded Text-to-SQL agent: it receives a goal, uses an LLM for one probabilistic step, validates the proposed action, executes an allowed tool (SQL), observes failure, and can self-correct once. That constrained design is part of the safety model.
