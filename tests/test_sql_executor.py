"""Tests for SQLExecutor."""

import pytest

from app.database.connection import get_schema_metadata, initialize_database
from app.services.sql_executor import SQLExecutor

initialize_database()
SCHEMA = get_schema_metadata()


def test_execute_returns_rows():
    rows = SQLExecutor(SCHEMA).execute("SELECT nome FROM clientes WHERE ativo = 1")
    assert isinstance(rows, list)
    assert len(rows) > 0


def test_execute_with_string_literal():
    rows = SQLExecutor(SCHEMA).execute("SELECT * FROM pedidos WHERE status = 'aprovado'")
    assert all(row["status"] == "aprovado" for row in rows)


def test_execute_count():
    rows = SQLExecutor(SCHEMA).execute("SELECT COUNT(*) FROM clientes")
    assert list(rows[0].values())[0] >= 5


def test_execute_rejects_drop():
    with pytest.raises(ValueError, match="inválido"):
        SQLExecutor(SCHEMA).execute("DROP TABLE clientes")


def test_execute_rejects_unknown_table():
    with pytest.raises(ValueError):
        SQLExecutor(SCHEMA).execute("SELECT * FROM usuarios")


def test_parametrize_string():
    _, params = SQLExecutor(SCHEMA)._parametrize(
        "SELECT * FROM pedidos WHERE status = 'aprovado'"
    )
    assert "p0" in params and params["p0"] == "aprovado"


def test_parametrize_no_literals():
    _, params = SQLExecutor(SCHEMA)._parametrize(
        "SELECT COUNT(*) FROM clientes WHERE ativo = 1"
    )
    assert params == {}
