import logging
import time
from functools import lru_cache

from groq import Groq

from ..config import settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self) -> None:
        self._client = Groq(api_key=settings.groq_api_key) if settings.groq_api_key else None
        self._last_inference_ms: float = 0.0

        if self._client is None:
            logger.warning("LLM not configured — set GROQ_API_KEY before using /query.")
        else:
            logger.info("LLM ready — model: %s", settings.groq_model)

    @property
    def configured(self) -> bool:
        return self._client is not None

    @property
    def last_inference_ms(self) -> float:
        return self._last_inference_ms

    @property
    def cache_hits(self) -> int:
        return self.generate_sql.cache_info().hits

    @lru_cache(maxsize=256)
    def generate_sql(self, user_query: str, prompt: str) -> str:
        """Generate one SQL statement and cache it by query and complete prompt."""
        if self._client is None:
            raise RuntimeError(
                "GROQ_API_KEY is not configured. Add it to .env before running an AI query."
            )

        start = time.perf_counter()
        response = self._client.chat.completions.create(
            model=settings.groq_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=256,
        )
        self._last_inference_ms = (time.perf_counter() - start) * 1000

        raw = response.choices[0].message.content or ""
        sql = self._clean(raw)

        if not sql:
            logger.warning("LLM returned empty output for: %r", user_query)
            raise RuntimeError("O modelo não conseguiu gerar um SQL válido para essa pergunta.")

        logger.info("SQL gerado (%.0fms): %s", self._last_inference_ms, sql)
        return sql

    @staticmethod
    def _clean(text: str) -> str:
        """Remove markdown fences, SQL prefixes and extra whitespace."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(
                line for line in lines if not line.strip().startswith("```")
            )
        if text.lower().startswith("sql:"):
            text = text[4:]
        return " ".join(text.split())
