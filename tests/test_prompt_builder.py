"""Testes do PromptBuilder."""

from app.services.prompt_builder import PromptBuilder

SCHEMA = {
    "tables": [{
        "name": "clientes",
        "description": "Cadastro de clientes.",
        "columns": [
            {"name": "id",   "type": "INTEGER", "description": "PK"},
            {"name": "nome", "type": "TEXT",    "description": "Nome"},
        ],
    }]
}


def test_prompt_has_table():
    assert "clientes" in PromptBuilder(SCHEMA).build_prompt("Liste clientes")

def test_prompt_has_columns():
    prompt = PromptBuilder(SCHEMA).build_prompt("Liste clientes")
    assert "id" in prompt and "nome" in prompt

def test_prompt_has_user_query():
    assert "Liste clientes" in PromptBuilder(SCHEMA).build_prompt("Liste clientes")

def test_prompt_ends_with_sql():
    assert PromptBuilder(SCHEMA).build_prompt("x").strip().endswith("SQL:")

def test_prompt_has_examples():
    prompt = PromptBuilder(SCHEMA).build_prompt("x")
    assert "Exemplos:" in prompt and "SELECT" in prompt

def test_fallback_has_invalid_sql():
    prompt = PromptBuilder(SCHEMA).build_fallback_prompt("x", "SELECT senha FROM clientes")
    assert "SELECT senha FROM clientes" in prompt
    assert "inválido" in prompt.lower()
