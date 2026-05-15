from typing import Any

FEW_SHOT_EXAMPLES = [
    {
        "pergunta": "Liste todos os clientes ativos",
        "sql": "SELECT id, nome, cidade, estado, segmento FROM clientes WHERE ativo = 1",
    },
    {
        "pergunta": "Qual o valor total dos pedidos aprovados?",
        "sql": "SELECT SUM(valor_total) FROM pedidos WHERE status = 'aprovado'",
    },
    {
        "pergunta": "Quais produtos são da categoria Software?",
        "sql": "SELECT descricao, preco_unitario FROM produtos WHERE categoria = 'Software'",
    },
    {
        "pergunta": "Quantos pedidos estão pendentes?",
        "sql": "SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'",
    },
    {
        "pergunta": "Qual o produto mais caro?",
        "sql": "SELECT descricao, preco_unitario FROM produtos ORDER BY preco_unitario DESC LIMIT 1",
    },
]

_SYSTEM = (
    "Você é um assistente Text2SQL para um sistema ERP. "
    "Retorne APENAS uma instrução SQL SELECT que responda à pergunta do usuário. "
    "Use somente as tabelas e colunas descritas no schema abaixo. "
    "Não adicione comentários, ponto-e-vírgula, explicações ou formatação markdown."
)


class PromptBuilder:
    def __init__(self, schema_metadata: dict[str, Any]) -> None:
        self._schema_desc = self._build_schema(schema_metadata)
        self._examples = self._build_examples()

    def _build_schema(self, schema: dict[str, Any]) -> str:
        lines = []
        for table in schema.get("tables", []):
            cols = ", ".join(
                f"{c['name']} ({c['type']}) — {c['description']}"
                for c in table.get("columns", [])
            )
            lines.append(
                f"Tabela: {table['name']} — {table.get('description', '')}\n"
                f"Colunas: {cols}"
            )
        return "\n\n".join(lines)

    def _build_examples(self) -> str:
        return "\n".join(
            f"Pergunta: {ex['pergunta']}\nSQL: {ex['sql']}"
            for ex in FEW_SHOT_EXAMPLES
        )

    def build_prompt(self, user_query: str) -> str:
        return (
            f"{_SYSTEM}\n\n"
            f"Schema:\n{self._schema_desc}\n\n"
            f"Exemplos:\n{self._examples}\n\n"
            f"Pergunta: {user_query}\n"
            "SQL:"
        )

    def build_fallback_prompt(self, user_query: str, invalid_sql: str) -> str:
        return (
            f"{_SYSTEM}\n\n"
            "A tentativa anterior gerou um SQL inválido. Tente novamente com atenção ao schema.\n"
            f"SQL inválido anterior: {invalid_sql}\n\n"
            f"Schema:\n{self._schema_desc}\n\n"
            f"Exemplos:\n{self._examples}\n\n"
            f"Pergunta: {user_query}\n"
            "SQL:"
        )
