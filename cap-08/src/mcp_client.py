# src/mcp_client.py
# Capitulo 8: Context manager para conexao MCP de longa duracao
import asyncio
import os
from contextlib import asynccontextmanager

from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession
from mcp.client.sse import sse_client

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/sse")
MCP_TOKEN = os.getenv("MCP_TOKEN", "")

# Estado global da conexao (singleton simples)
_session = None
_tools = None
_session_lock = asyncio.Lock()


@asynccontextmanager
async def mcp_session():
    """
    Context manager para obter uma sessao MCP com gerenciamento automatico.

    Para agentes de longa duracao, mantem a conexao aberta e reutiliza.
    Em producao, implemente reconexao com backoff para conexoes SSE que caem.
    """
    global _session, _tools

    async with _session_lock:
        if _session is None:
            headers = {"Authorization": f"Bearer {MCP_TOKEN}"}
            read, write = await sse_client(MCP_SERVER_URL, headers=headers).__aenter__()
            _session = await ClientSession(read, write).__aenter__()
            await _session.initialize()
            _tools = await load_mcp_tools(_session)

    yield _session, _tools


class MCPToolAdapter:
    """
    Adapter manual para uma tool MCP especifica.

    Use quando precisar de controle total sobre quais tools incluir
    ou como processar os resultados.
    """

    def __init__(self, name: str, description: str, session: ClientSession):
        self.name = name
        self.description = description
        self.session = session

    async def executar(self, **kwargs) -> str:
        """Executa a tool MCP e retorna o texto do resultado."""
        resultado = await self.session.call_tool(self.name, kwargs)
        textos = [c.text for c in resultado.content if hasattr(c, 'text')]
        return "\n".join(textos)
