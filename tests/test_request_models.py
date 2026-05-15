"""Testes de validação do request model."""

import pytest
from pydantic import ValidationError
from app.models.request_models import QueryRequest


def test_valid():
    assert QueryRequest(query="Liste os clientes ativos").query

def test_reject_empty():
    with pytest.raises(ValidationError):
        QueryRequest(query="")

def test_reject_too_short():
    with pytest.raises(ValidationError):
        QueryRequest(query="ok")

def test_reject_too_long():
    with pytest.raises(ValidationError):
        QueryRequest(query="x" * 501)

def test_accepts_min():
    assert QueryRequest(query="x" * 5).query

def test_accepts_max():
    assert QueryRequest(query="x" * 500).query
