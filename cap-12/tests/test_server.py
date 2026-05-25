# tests/test_server.py
# Capitulo 12: Integration tests dos endpoints HTTP e middleware de autenticacao
import os

import pytest

# Configura variaveis de ambiente ANTES de importar o app
os.environ["JWT_SECRET"] = "test_secret_key_para_testes_unitarios_apenas"
os.environ["LOG_FORMAT"] = "console"
os.environ["LOG_LEVEL"] = "WARNING"

from fastapi.testclient import TestClient

from src.auth import criar_token
from src.server_http import app

# Token valido para os testes -- validade de 1 hora
TEST_TOKEN = criar_token("test-client", horas_validade=1)
AUTH_HEADERS = {"Authorization": f"Bearer {TEST_TOKEN}"}


class TestHealthEndpoints:
    def test_health_sem_autenticacao(self):
        """Health check nao requer autenticacao."""
        with TestClient(app) as client:
            resp = client.get("/health")

        assert resp.status_code == 200
        dados = resp.json()
        assert dados["status"] == "healthy"
        assert "uptime_seconds" in dados
        assert "server" in dados

    def test_ready_retorna_checks(self):
        """Ready check retorna status dos componentes."""
        with TestClient(app) as client:
            resp = client.get("/ready")

        assert resp.status_code in (200, 503)
        dados = resp.json()
        assert "ready" in dados
        assert "checks" in dados
        assert "mcp_server" in dados["checks"]
        assert "jwt_configured" in dados["checks"]

    def test_docs_sem_autenticacao(self):
        """Documentacao Swagger nao requer autenticacao."""
        with TestClient(app) as client:
            resp = client.get("/docs")
        assert resp.status_code == 200


class TestAutenticacao:
    def test_sem_token_retorna_401(self):
        """Requests sem token retornam 401."""
        with TestClient(app) as client:
            resp = client.get("/sse")
        assert resp.status_code == 401

    def test_header_malformado_retorna_401(self):
        """Header sem 'Bearer ' retorna 401."""
        with TestClient(app) as client:
            resp = client.get("/sse", headers={"Authorization": "token-sem-bearer"})
        assert resp.status_code == 401

    def test_token_invalido_retorna_401(self):
        """Token invalido retorna 401."""
        with TestClient(app) as client:
            resp = client.get("/sse", headers={"Authorization": "Bearer token-invalido-aqui"})
        assert resp.status_code == 401

    def test_token_valido_nao_retorna_401(self):
        """Token valido nao retorna 401 ou 403."""
        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.get("/sse", headers=AUTH_HEADERS)
        assert resp.status_code not in (401, 403)

    def test_metrics_sem_autenticacao(self):
        """Endpoint de metricas nao requer autenticacao."""
        with TestClient(app) as client:
            resp = client.get("/metrics")
        assert resp.status_code == 200


class TestRateLimiting:
    def test_health_nao_tem_rate_limit(self):
        """Health check deve responder independente de rate limit."""
        with TestClient(app) as client:
            for _ in range(5):
                resp = client.get("/health")
                assert resp.status_code == 200
