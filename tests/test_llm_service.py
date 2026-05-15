"""Testes do LLMService — sem chamar a API real."""

import pytest
from app.services.llm_service import LLMService


def _mock(output: str) -> LLMService:
    svc = LLMService.__new__(LLMService)
    svc._last_inference_ms = 0.0

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

    svc._client = FakeClient()
    return svc


def test_clean_sql_prefix():
    svc = _mock("SQL: SELECT * FROM clientes")
    assert svc.generate_sql("query", "prompt") == "SELECT * FROM clientes"

def test_clean_markdown_fence():
    svc = _mock("```sql\nSELECT * FROM clientes\n```")
    assert svc.generate_sql("query", "prompt") == "SELECT * FROM clientes"

def test_clean_whitespace():
    svc = _mock("  SELECT *  FROM  clientes  ")
    assert svc.generate_sql("query", "prompt") == "SELECT * FROM clientes"

def test_raises_on_empty():
    svc = _mock("")
    with pytest.raises(RuntimeError, match="válido"):
        svc.generate_sql("query", "prompt")
