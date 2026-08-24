"""Integration tests for the complete API flow with a mocked LLM."""

import pytest
from fastapi.testclient import TestClient


class _MockLLM:
    configured = True
    cache_hits = 0
    last_inference_ms = 0.0

    @staticmethod
    def generate_sql(user_query: str, prompt: str) -> str:
        return "SELECT nome, cidade FROM clientes WHERE ativo = 1"


@pytest.fixture
def client(monkeypatch):
    import app.main as main_module

    monkeypatch.setattr(main_module, "_llm", _MockLLM())
    return TestClient(main_module.app)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["llm_configured"] is True


def test_schema(client):
    response = client.get("/schema")
    assert response.status_code == 200
    tables = [table["name"] for table in response.json()["tables"]]
    assert "clientes" in tables
    assert "produtos" in tables
    assert "pedidos" in tables


def test_query_success(client):
    response = client.post("/query", json={"query": "Liste os clientes ativos"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["sql"].startswith("SELECT")
    assert isinstance(payload["result"], list)
    assert payload["row_count"] == len(payload["result"])
    assert payload["cached"] is False
    assert "llm_inference_ms" in payload
    assert "sql_execution_ms" in payload
    assert "total_ms" in payload


def test_query_rejects_short(client):
    assert client.post("/query", json={"query": "ab"}).status_code == 422


def test_query_rejects_offtopic(client):
    response = client.post("/query", json={"query": "Qual a capital do Brasil?"})
    assert response.status_code == 400
