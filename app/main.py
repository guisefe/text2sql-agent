import logging
import time

from fastapi import FastAPI, HTTPException, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .config import settings
from .database.connection import get_schema_metadata, initialize_database
from .logging_config import configure_logging
from .models.request_models import QueryRequest
from .models.response_models import QueryResponse
from .services.llm_service import LLMService
from .services.prompt_builder import PromptBuilder
from .services.sql_executor import SQLExecutor
from .validators.sql_validator import query_mentions_schema

configure_logging()
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Text2SQL Agent — ERP",
    description=(
        "Guardrailed Text-to-SQL agent for ERP data. It translates natural-language "
        "questions into validated read-only SQL before execution."
    ),
    version="1.1.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

initialize_database()
_schema = get_schema_metadata()
_prompt_builder = PromptBuilder(_schema)
_llm = LLMService()
_executor = SQLExecutor(_schema)


@app.post("/query", response_model=QueryResponse, tags=["agent"])
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
def process_query(request: Request, payload: QueryRequest) -> QueryResponse:
    """Translate a natural-language ERP question into validated read-only SQL."""
    logger.info("Query recebida: %r", payload.query)
    t_start = time.perf_counter()

    if not query_mentions_schema(payload.query, _schema):
        raise HTTPException(
            status_code=400,
            detail=(
                "A pergunta não menciona nenhuma tabela ou coluna do schema atual. "
                "Tente uma pergunta sobre clientes, produtos ou pedidos."
            ),
        )

    if not getattr(_llm, "configured", True):
        raise HTTPException(
            status_code=503,
            detail="LLM não configurado. Defina GROQ_API_KEY antes de usar /query.",
        )

    prompt = _prompt_builder.build_prompt(payload.query)
    hits_before = getattr(_llm, "cache_hits", 0)

    try:
        sql = _llm.generate_sql(payload.query, prompt)
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    cached = getattr(_llm, "cache_hits", 0) > hits_before

    try:
        rows = _executor.execute(sql)
    except ValueError:
        logger.warning("SQL inválido na primeira tentativa (%r) — tentando fallback.", sql)
        fallback = _prompt_builder.build_fallback_prompt(payload.query, sql)
        try:
            sql = _llm.generate_sql(payload.query, fallback)
            rows = _executor.execute(sql)
            cached = False
        except (ValueError, RuntimeError) as exc:
            logger.error("Fallback também falhou: %s", exc)
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Erro inesperado ao executar SQL.")
        raise HTTPException(status_code=500, detail="Erro interno ao processar a query.") from exc

    total_ms = (time.perf_counter() - t_start) * 1000

    return QueryResponse(
        sql=sql,
        result=rows,
        row_count=len(rows),
        cached=cached,
        llm_inference_ms=round(_llm.last_inference_ms, 2),
        sql_execution_ms=round(_executor.last_execution_ms, 2),
        total_ms=round(total_ms, 2),
    )


@app.get("/schema", tags=["metadata"])
def get_schema() -> dict:
    """Return the schema metadata supplied to the agent."""
    return _schema


@app.get("/health", tags=["operations"])
def health() -> dict:
    return {
        "status": "ok",
        "version": app.version,
        "model": settings.groq_model,
        "llm_configured": getattr(_llm, "configured", True),
    }
