# Architecture Notes

This document explains the project in a way that is easy to present to recruiters, technical interviewers and non-specialists.

## The plain-language version

The project lets a person ask questions about ERP data without writing SQL.

Instead of giving the language model full control over the database, the system separates responsibilities:

- the **LLM** interprets the question and proposes SQL;
- the **application** validates whether the SQL is safe;
- the **database executor** only runs approved read-only statements.

The core design principle is:

> Treat LLM output as untrusted input.

## Cascading architecture

```mermaid
flowchart TD
    A[1. User question<br/>Natural language in Portuguese]
    B[2. API contract<br/>FastAPI + Pydantic validation]
    C[3. Domain gate<br/>Rejects questions outside the ERP schema]
    D[4. Prompt assembly<br/>Schema metadata + examples]
    E[5. LLM proposal<br/>Groq model returns one SQL candidate]
    F[6. Safety policy<br/>Deterministic SQL validator]
    G[7. Execution<br/>SQLAlchemy with bind parameters]
    H[8. Response<br/>Rows + SQL + latency metrics]

    A --> B --> C --> D --> E --> F --> G --> H
```

## Failure cascade

```mermaid
flowchart TD
    A[Generated SQL] --> B{Safe?}
    B -->|Yes| C[Execute]
    B -->|No, first failure| D[Fallback prompt]
    D --> E[Second SQL proposal]
    E --> F{Safe now?}
    F -->|Yes| C
    F -->|No| G[Reject request]
```

The retry loop is limited to one attempt. This keeps the workflow predictable and prevents uncontrolled agent loops.

## Runtime boundaries

```mermaid
flowchart LR
    subgraph API[API boundary]
        A1[FastAPI endpoint]
        A2[Request and response models]
    end

    subgraph AI[AI boundary]
        B1[PromptBuilder]
        B2[LLMService]
    end

    subgraph Safety[Safety boundary]
        C1[Schema relevance gate]
        C2[SQLValidator]
    end

    subgraph Data[Data boundary]
        D1[SQLExecutor]
        D2[(SQLite ERP database)]
    end

    API --> Safety --> AI --> Safety --> Data
```

## Why not let the LLM execute directly?

Because prompts are not enforcement mechanisms.

A model may ignore instructions, hallucinate a column, generate unsafe SQL or produce syntax that does not match the current schema. The project therefore keeps the database tool behind a deterministic validation layer.

## What is intentionally out of scope?

| Limitation | Why it is deferred | Production path |
|---|---|---|
| No JOINs | keeps validator simple and explainable | add relationship metadata and AST-level policy |
| SQLite | zero setup for demo | PostgreSQL read replica and read-only role |
| Lexical domain gate | easy to understand | classifier or embedding-based schema/table retrieval |
| Single LLM provider | demo simplicity | provider abstraction, fallback and cost routing |
| No authentication | not needed for local demo | JWT/API key middleware, RBAC and tenant isolation |

## Interview explanation

A strong explanation is:

> This is a bounded agentic workflow. The model proposes a database action, but deterministic application code validates the action before execution. If the action is invalid, the agent can retry once. If it still fails, the system refuses instead of forcing an unsafe answer.
