import logging
import re
import time
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from ..database.connection import engine
from ..validators.sql_validator import is_safe_sql

logger = logging.getLogger(__name__)

_STRING_LITERAL_RE = re.compile(r"'(?:''|[^'])*'")


class SQLExecutor:
    def __init__(self, schema_metadata: dict[str, Any]) -> None:
        self._schema = schema_metadata
        self._last_execution_ms: float = 0.0

    @property
    def last_execution_ms(self) -> float:
        return self._last_execution_ms

    def execute(self, sql: str) -> list[dict[str, Any]]:
        if not is_safe_sql(sql, self._schema):
            raise ValueError(
                "SQL inválido ou não permitido. Apenas SELECT simples são aceitos."
            )

        stmt, params = self._parametrize(sql)
        start = time.perf_counter()
        try:
            with engine.connect() as conn:
                rows = [dict(r._mapping) for r in conn.execute(stmt, params)]
                self._last_execution_ms = (time.perf_counter() - start) * 1000
                logger.info("%d linha(s) retornada(s) em %.1fms.", len(rows), self._last_execution_ms)
                return rows
        except SQLAlchemyError:
            logger.exception("Falha ao executar SQL: %s", sql)
            raise ValueError("Falha ao executar o SQL. Verifique a sintaxe e tente novamente.")

    def _parametrize(self, sql: str) -> tuple[Any, dict[str, Any]]:
        """Replace string literals with named bind parameters."""
        params: dict[str, Any] = {}

        def replace(match: re.Match) -> str:
            key = f"p{len(params)}"
            params[key] = match.group(0)[1:-1].replace("''", "'")
            return f":{key}"

        return text(_STRING_LITERAL_RE.sub(replace, sql)), params
