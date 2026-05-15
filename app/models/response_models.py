from typing import Any
from pydantic import BaseModel, Field


class QueryResponse(BaseModel):
    sql: str = Field(..., description="SQL gerado pelo agente.")
    result: list[dict[str, Any]] = Field(..., description="Linhas retornadas pela query.")
    row_count: int = Field(0, description="Número de linhas no resultado.")
    cached: bool = Field(False, description="True se o SQL veio do cache.")
    llm_inference_ms: float = Field(0.0, description="Tempo de inferência do LLM em ms.")
    sql_execution_ms: float = Field(0.0, description="Tempo de execução do SQL em ms.")
    total_ms: float = Field(0.0, description="Tempo total da requisição em ms.")
