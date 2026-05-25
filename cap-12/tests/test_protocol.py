# tests/test_protocol.py
# Capitulo 10: E2E tests do protocolo MCP com ClientSession real
# REQUISITO: servidor rodando em localhost:8000
# Pule esses testes se TEST_MCP_TOKEN nao estiver configurado
import json
import os

import pytest
from mcp import ClientSession
from mcp.client.sse import sse_client

SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/sse")
TEST_TOKEN = os.getenv("TEST_MCP_TOKEN", "")


@pytest.fixture(scope="session")
async def mcp_session():
    """Sessao MCP compartilhada para os testes E2E."""
    if not TEST_TOKEN:
        pytest.skip("TEST_MCP_TOKEN nao configurado -- pulando testes E2E")

    headers = {"Authorization": f"Bearer {TEST_TOKEN}"}

    async with sse_client(SERVER_URL, headers=headers) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


class TestProtocoloMCP:
    async def test_tools_list_retorna_ferramentas(self, mcp_session):
        """O servidor retorna pelo menos 3 tools."""
        tools = await mcp_session.list_tools()

        assert len(tools.tools) >= 3
        nomes = [t.name for t in tools.tools]
        assert "echo_mercado" in nomes
        assert "buscar_tendencias" in nomes
        assert "analisar_bsr" in nomes

    async def test_tool_echo_retorna_mensagem(self, mcp_session):
        """echo_mercado retorna a mensagem enviada."""
        resultado = await mcp_session.call_tool("echo_mercado", {"mensagem": "teste-protocolo-2026"})

        assert not resultado.isError
        assert "teste-protocolo-2026" in resultado.content[0].text

    async def test_tool_buscar_tendencias_retorna_dados(self, mcp_session):
        """buscar_tendencias retorna dados para 'IA'."""
        resultado = await mcp_session.call_tool("buscar_tendencias", {"area": "IA", "limite": 3})

        assert not resultado.isError
        texto = resultado.content[0].text
        assert "Tendencias" in texto or "tendencias" in texto.lower()

    async def test_tool_analisar_bsr_categoria_valida(self, mcp_session):
        """analisar_bsr retorna dados para 'romantasy'."""
        resultado = await mcp_session.call_tool("analisar_bsr", {"categoria": "romantasy"})

        assert not resultado.isError
        texto = resultado.content[0].text
        assert "Romantasy" in texto

    async def test_ler_resource_categorias(self, mcp_session):
        """O resource mercado://categorias retorna JSON valido."""
        resultado = await mcp_session.read_resource("mercado://categorias")
        dados = json.loads(resultado.contents[0].text)

        assert isinstance(dados, list)
        assert len(dados) > 0
        assert "slug" in dados[0]
        assert "nome" in dados[0]

    async def test_ler_resource_bsr_especifico(self, mcp_session):
        """O resource mercado://bsr/romantasy retorna dados corretos."""
        resultado = await mcp_session.read_resource("mercado://bsr/romantasy")
        dados = json.loads(resultado.contents[0].text)

        assert "categoria" in dados
        assert "bsr" in dados
        assert "preco_medio" in dados

    async def test_prompts_list_retorna_templates(self, mcp_session):
        """O servidor expoe pelo menos 2 prompts."""
        prompts = await mcp_session.list_prompts()

        assert len(prompts.prompts) >= 2
        nomes = [p.name for p in prompts.prompts]
        assert "analisar_oportunidade" in nomes
        assert "planejar_serie" in nomes
