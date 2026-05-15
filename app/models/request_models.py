from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=5,
        max_length=500,
        examples=["Quais clientes estão com pedidos pendentes?"],
        description="Pergunta em linguagem natural sobre os dados do ERP.",
    )
