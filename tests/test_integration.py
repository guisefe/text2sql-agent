"""Testes de integração — ciclo completo com LLM mockado."""

import pytest
from fastapi.testclient import TestClient


class _MockLLM:
    _last_inference_ms = 0.0

    class _Info:
        hits = 0

    @staticmethod
    def generate_sql(user_query: str, prompt: str) -> str:
        return "SELECT nome, cidade FROM clientes WHERE ativo = 1"

    @staticmethod
    def cache_info():
        return _MockLLM._Info()

    @property
    def last_inference_ms(self):
        return 0.0


@pytest.fixture
def client(monkeypatch):
    import app.main as m
    monkeypatch.setattr(m, "_llm", _MockLLM())
    from app.main import app
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_schema(client):
    r = client.get("/schema")
    assert r.status_code == 200
    tables = [t["name"] for t in r.json()["tables"]]
    assert "clientes" in tables
    assert "produtos" in tables
    assert "pedidos" in tables


def test_query_success(client):
    r = client.post("/query", json={"query": "Liste os clientes ativos"})
    assert r.status_code == 200
    p = r.json()
    assert p["sql"].startswith("SELECT")
    assert isinstance(p["result"], list)
    assert p["row_count"] == len(p["result"])
    assert "cached" in p
    assert "llm_inference_ms" in p
    assert "sql_execution_ms" in p
    assert "total_ms" in p


def test_query_rejects_short(client):
    assert client.post("/query", json={"query": "ab"}).status_code == 422


def test_query_rejects_offtopic(client):
    r = client.post("/query", json={"query": "Qual a capital do Brasil?"})
    assert r.status_code == 400
