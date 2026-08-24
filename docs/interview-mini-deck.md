# Interview Mini Deck — Text2SQL Agent

Use this as a 5-minute verbal deck during the interview.

---

## Slide 1 — Problem

**Title:** From natural language to safe database answers

**Say:**

> Business users often need answers from operational systems, but they do not know SQL. The risk is giving an LLM direct access to a database and executing whatever it returns.

**Message:**

The project is not just about generating SQL. It is about generating SQL safely.

---

## Slide 2 — Product idea

**Title:** A bounded Text-to-SQL agent for ERP data

**Say:**

> The user asks in Portuguese. The system understands the question, proposes SQL, validates it and only then executes a read-only query.

**Message:**

The LLM proposes. The application enforces.

---

## Slide 3 — Cascading architecture

**Title:** Clear responsibility per layer

```text
User question
  ↓
FastAPI endpoint
  ↓
Schema relevance gate
  ↓
PromptBuilder
  ↓
Groq LLM
  ↓
SQLValidator
  ↓
SQLExecutor
  ↓
SQLite ERP database
  ↓
Rows + SQL + metrics
```

**Say:**

> I separated the probabilistic part from the deterministic part. The model handles language. The validator handles permission. The executor handles the database.

---

## Slide 4 — Guardrails

**Title:** Prompting is guidance. Validation is enforcement.

**Say:**

> The model output is treated as untrusted input. The validator only allows known tables, known columns, allowlisted functions and one SELECT statement.

**Mention:**

- blocks writes and DDL;
- blocks unknown schema elements;
- blocks multiple statements;
- parameterizes string literals;
- rejects off-domain questions before the LLM call.

---

## Slide 5 — Live demo

**Title:** Three requests show the full behavior

1. `Liste os clientes ativos`
2. `Qual o valor total dos pedidos aprovados?`
3. `Qual a capital do Brasil?`

**Say:**

> The first shows a happy path. The second shows aggregation. The third shows safe refusal before wasting an LLM call.

---

## Slide 6 — Production evolution

**Title:** What I would improve next

**Say:**

> I intentionally kept the demo small. For production, I would add authentication, database read-only roles, row limits, timeouts, stronger AST validation, evaluation datasets, tracing and cost monitoring.

**Close with:**

> The main point is that I can build with LLMs while keeping software engineering boundaries around them.
