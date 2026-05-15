# Text2SQL Agent — ERP

[![CI](https://github.com/guisefe/text2sql-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/guisefe/text2sql-agent/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-demo-orange.svg)

A metadata-driven Text2SQL agent that converts natural language questions into SQL queries against ERP data. Powered by **Groq API (llama-3.1-8b-instant)** and built with FastAPI.

The schema mirrors a commercial ERP module — customers, products, and sales orders — the kind of data found in systems like Londrisoft Gestor.

> **⚠️ Demo project.** Intentional limitations documented below.

---

## How it works

\`\`\`
Natural language question
        │
        ▼
Semantic gate ──── rejects questions unrelated to schema
        │
        ▼
PromptBuilder ──── injects schema metadata + few-shot examples
        │
        ▼
Groq API ────────── llama-3.1-8b-instant generates one SQL SELECT
        │
        ▼
SQLValidator ────── whitelist: tables, columns, keywords, functions
        │           (on failure → retry with fallback prompt)
        ▼
SQLExecutor ─────── parametrized execution via SQLAlchemy
        │
        ▼
JSON response ───── sql, result, row_count, timing metrics
\`\`\`

---

## Quick start

### Option 1: Docker

\`\`\`bash
git clone https://github.com/guisefe/text2sql-agent.git
cd text2sql-agent
cp .env.example .env
docker compose up --build
\`\`\`

### Option 2: Local Python

\`\`\`bash
git clone https://github.com/guisefe/text2sql-agent.git
cd text2sql-agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
\`\`\`

Get a free Groq API key at [console.groq.com](https://console.groq.com).

---

## Usage

\`\`\`bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Liste os clientes ativos"}'
\`\`\`

\`\`\`json
{
  "sql": "SELECT id, nome, cidade, estado, segmento FROM clientes WHERE ativo = 1",
  "result": [
    {"id": 1, "nome": "Mercado Central Ltda", "cidade": "São Paulo", "estado": "SP", "segmento": "Varejo"},
    {"id": 2, "nome": "Distribuidora Norte SA", "cidade": "Manaus", "estado": "AM", "segmento": "Atacado"}
  ],
  "row_count": 4,
  "cached": false,
  "llm_inference_ms": 198.1,
  "sql_execution_ms": 1.0,
  "total_ms": 207.8
}
\`\`\`

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| \`POST\` | \`/query\` | Convert question to SQL and execute |
| \`GET\` | \`/schema\` | Return current schema metadata |
| \`GET\` | \`/health\` | Liveness check |

Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Schema

| Table | Description |
|-------|-------------|
| \`clientes\` | Customer registry — name, city, state, segment, active status |
| \`produtos\` | Product catalog — description, category, unit price, stock |
| \`pedidos\` | Sales orders — customer, product, quantity, total, status, date |

---

## Example questions

| Question | Generated SQL |
|---|---|
| Liste os clientes ativos | \`SELECT id, nome FROM clientes WHERE ativo = 1\` |
| Qual o valor total dos pedidos aprovados? | \`SELECT SUM(valor_total) FROM pedidos WHERE status = 'aprovado'\` |
| Quantos pedidos estão pendentes? | \`SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'\` |
| Qual o produto mais caro? | \`SELECT descricao, preco_unitario FROM produtos ORDER BY preco_unitario DESC LIMIT 1\` |

---

## Safety layers

1. **Input validation** — Pydantic enforces query length (5–500 chars)
2. **Semantic gate** — query must mention a table or column from the schema
3. **LLM output cleaning** — strips markdown fences, prefixes, whitespace
4. **Whitelist SQL validator** — only approved keywords, functions, tables, columns
5. **String literal parametrization** — bind parameters before execution
6. **Retry with fallback prompt** — on validation failure, retries once
7. **Rate limiting** — configurable per-IP limit (default 30/min)

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| \`GROQ_API_KEY\` | — | **Required.** Free at console.groq.com |
| \`GROQ_MODEL\` | \`llama-3.1-8b-instant\` | Groq model to use |
| \`DATABASE_URL\` | \`sqlite:///./erp.db\` | SQLAlchemy connection string |
| \`RATE_LIMIT_PER_MINUTE\` | \`30\` | Max requests per IP per minute |
| \`LOG_LEVEL\` | \`INFO\` | Logging verbosity |

---

## Project structure

\`\`\`
app/
├── main.py              FastAPI app, endpoints, orchestration
├── config.py            pydantic-settings, .env support
├── logging_config.py    Structured logging
├── database/
│   ├── connection.py    Engine, DB init, schema loader
│   ├── schema.json      Table/column metadata for the LLM
│   └── schema.sql       DDL and seed data
├── models/
│   ├── request_models.py   Input validation
│   └── response_models.py  Response with timing metrics
├── services/
│   ├── llm_service.py      Groq API wrapper with caching
│   ├── prompt_builder.py   Prompt + fallback construction
│   └── sql_executor.py     Validated + parametrized execution
└── validators/
    └── sql_validator.py    Whitelist validator + semantic gate
tests/                   40+ tests across all layers
\`\`\`

---

## Running tests

\`\`\`bash
pytest -v
pytest --cov=app
\`\`\`

---

## Known limitations

- **Single table per query** — JOINs blocked by design
- **Model sensitivity** — specific questions yield better SQL
- **No authentication** — add auth before exposing publicly
- **In-memory rate limiting** — use Redis for multi-instance deployments

See [TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md) and [DECISIONS.md](DECISIONS.md).

---

## License

MIT © Guilherme Senis Fernandes
