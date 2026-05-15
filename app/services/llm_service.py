import logging
import time
from functools import lru_cache

from groq import Groq

from ..config import settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self) -> None:
        if not settings.groq_api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. "
                "Create a free key at https://console.groq.com and add it to .env"
            )
        self._client = Groq(api_key=settings.groq_api_key)
        self._last_inference_ms: float = 0.0
        logger.info("LLM ready — model: %s", settings.groq_model)

    @property
    def last_inference_ms(self) -> float:
        return self._last_inference_ms

    @lru_cache(maxsize=256)
    def generate_sql(self, user_query: str, prompt: str) -> str:
        """Cached by (user_query, prompt). Calls Groq API."""
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

    def _clean(self, text: str) -> str:
        """Remove markdown fences, SQL: prefix and extra whitespace."""
        text = text.strip()
        # Remove ```sql ... ``` or ``` ... ```
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(
                line for line in lines
                if not line.strip().startswith("```")
            )
        if text.lower().startswith("sql:"):
            text = text[4:]
        return " ".join(text.split())
