"""Tests for LLMService without calling the real API."""

import pytest

from app.services.llm_service import LLMService


def _mock(output: str) -> LLMService:
    service = LLMService.__new__(LLMService)
    service._last_inference_ms = 0.0

    class FakeChoice:
        message = type("M", (), {"content": output})()

    class FakeResponse:
        choices = [FakeChoice()]

    class FakeClient:
        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    return FakeResponse()

    service._client = FakeClient()
    return service


def test_clean_sql_prefix():
    service = _mock("SQL: SELECT * FROM clientes")
    assert service.generate_sql("query", "prompt") == "SELECT * FROM clientes"


def test_clean_markdown_fence():
    service = _mock("```sql\nSELECT * FROM clientes\n```")
    assert service.generate_sql("query", "prompt") == "SELECT * FROM clientes"


def test_clean_whitespace():
    service = _mock("  SELECT *  FROM  clientes  ")
    assert service.generate_sql("query", "prompt") == "SELECT * FROM clientes"


def test_raises_on_empty():
    service = _mock("")
    with pytest.raises(RuntimeError, match="válido"):
        service.generate_sql("query", "prompt")
