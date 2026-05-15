"""Testes do validador SQL — segurança, schema e edge cases."""

import pytest
from app.database.connection import get_schema_metadata
from app.validators.sql_validator import is_safe_sql, query_mentions_schema

SCHEMA = get_schema_metadata()


# --- Queries válidas ---

def test_select_all_clientes():
    assert is_safe_sql("SELECT * FROM clientes", SCHEMA)

def test_select_with_where():
    assert is_safe_sql("SELECT nome FROM clientes WHERE ativo = 1", SCHEMA)

def test_select_with_string_literal():
    assert is_safe_sql("SELECT * FROM pedidos WHERE status = 'aprovado'", SCHEMA)

def test_select_count():
    assert is_safe_sql("SELECT COUNT(*) FROM pedidos", SCHEMA)

def test_select_sum():
    assert is_safe_sql("SELECT SUM(valor_total) FROM pedidos", SCHEMA)

def test_select_avg():
    assert is_safe_sql("SELECT AVG(preco_unitario) FROM produtos", SCHEMA)

def test_select_group_by():
    assert is_safe_sql("SELECT status, COUNT(*) FROM pedidos GROUP BY status", SCHEMA)

def test_select_order_limit():
    assert is_safe_sql(
        "SELECT descricao, preco_unitario FROM produtos ORDER BY preco_unitario DESC LIMIT 5",
        SCHEMA,
    )

def test_select_distinct():
    assert is_safe_sql("SELECT DISTINCT segmento FROM clientes", SCHEMA)


# --- Queries rejeitadas: operações perigosas ---

def test_reject_drop():
    assert not is_safe_sql("DROP TABLE clientes", SCHEMA)

def test_reject_insert():
    assert not is_safe_sql("INSERT INTO clientes VALUES (6, 'X', 'Y', 'Z', 'W', 1)", SCHEMA)

def test_reject_update():
    assert not is_safe_sql("UPDATE clientes SET ativo = 0", SCHEMA)

def test_reject_delete():
    assert not is_safe_sql("DELETE FROM clientes", SCHEMA)

def test_reject_load_extension():
    assert not is_safe_sql("SELECT load_extension('evil.so') FROM clientes", SCHEMA)


# --- Injeção ---

def test_reject_semicolon():
    assert not is_safe_sql("SELECT * FROM clientes; DROP TABLE clientes", SCHEMA)

def test_reject_comment():
    assert not is_safe_sql("SELECT * FROM clientes -- comentário", SCHEMA)

def test_reject_union():
    assert not is_safe_sql("SELECT * FROM clientes UNION SELECT * FROM clientes", SCHEMA)

def test_reject_subquery():
    assert not is_safe_sql(
        "SELECT * FROM pedidos WHERE valor_total > (SELECT AVG(valor_total) FROM pedidos)",
        SCHEMA,
    )


# --- Violações de schema ---

def test_reject_unknown_table():
    assert not is_safe_sql("SELECT * FROM usuarios", SCHEMA)

def test_reject_unknown_column():
    assert not is_safe_sql("SELECT senha FROM clientes", SCHEMA)


# --- Edge cases ---

def test_reject_empty():
    assert not is_safe_sql("", SCHEMA)

def test_reject_semicolon_only():
    assert not is_safe_sql(";", SCHEMA)


# --- Semantic gate ---

def test_gate_mentions_table():
    assert query_mentions_schema("Liste os clientes ativos", SCHEMA)

def test_gate_mentions_column():
    assert query_mentions_schema("Qual o valor total dos pedidos?", SCHEMA)

def test_gate_rejects_offtopic():
    assert not query_mentions_schema("Qual a capital do Brasil?", SCHEMA)

def test_gate_rejects_empty():
    assert not query_mentions_schema("", SCHEMA)
