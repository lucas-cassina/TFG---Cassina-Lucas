from datetime import datetime, timezone, timedelta

import pytest
from app.core.sse_tokens import issue_sse_token, consume_sse_token
from app.core import sse_tokens as _st


def test_issue_and_consume():
    """Token emitido se consume exitosamente y devuelve el conductor_id."""
    token = issue_sse_token(42)
    assert consume_sse_token(token) == 42


def test_single_use():
    """Token SSE es de un solo uso: el segundo consume devuelve None."""
    token = issue_sse_token(99)
    assert consume_sse_token(token) == 99
    assert consume_sse_token(token) is None


def test_token_invalido():
    """Token inexistente devuelve None sin excepciones."""
    assert consume_sse_token("token-que-no-existe-jamas") is None


def test_token_expirado():
    """Token con expires_at en el pasado devuelve None."""
    token = issue_sse_token(77)
    _st._sse_tokens[token]["expires_at"] = datetime.now(timezone.utc) - timedelta(seconds=1)
    assert consume_sse_token(token) is None


def test_cleanup_expirados():
    """_cleanup_expired elimina tokens vencidos del store."""
    token = issue_sse_token(55)
    _st._sse_tokens[token]["expires_at"] = datetime.now(timezone.utc) - timedelta(seconds=1)
    _st._cleanup_expired()
    assert token not in _st._sse_tokens


def test_tokens_distintos_por_conductor():
    """Dos emisiones para el mismo conductor generan tokens distintos."""
    t1 = issue_sse_token(10)
    t2 = issue_sse_token(10)
    assert t1 != t2
    assert consume_sse_token(t1) == 10
    assert consume_sse_token(t2) == 10
