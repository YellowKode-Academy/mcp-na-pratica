#!/usr/bin/env python
# scripts/client_test.py
# Capitulo 8: Teste direto do protocolo MCP via ClientSession
# Uso: MCP_TOKEN=<token> python scripts/client_test.py
import asyncio
import os

from mcp import ClientSession
from mcp.client.sse import sse_client

SERVER_URL = "http://localhost:8000/sse"
JWT_TOKEN = os.getenv("MCP_TOKEN", "")


async def main():
    if not JWT_TOKEN:
        print("ERRO: configure MCP_TOKEN no ambiente")
        print("Gere um token: python scripts/generate_token.py meu-agente 24")
        return

    headers = {"Authorization": f"Bearer {JWT_TOKEN}"}

    print(f"Conectando a {SERVER_URL}...")

    async with sse_client(SERVER_URL, headers=headers) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Conexao estabelecida!\n")

            # Lista ferramentas disponiveis
            tools = await session.list_tools()
            print(f"Ferramentas disponiveis ({len(tools.tools)}):")
            for tool in tools.tools:
                desc = tool.description[:60] if tool.description else "(sem descricao)"
                print(f"  - {tool.name}: {desc}...")

            print()

            # Chama buscar_tendencias
            print("Chamando buscar_tendencias(area='romantasy', limite=3)...")
            resultado = await session.call_tool(
                "buscar_tendencias",
                {"area": "romantasy", "limite": 3}
            )
            print("Resultado:")
            for content in resultado.content:
                print(content.text)

            print()

            # Le o resource de categorias
            print("Lendo resource mercado://categorias...")
            categorias = await session.read_resource("mercado://categorias")
            print("Categorias (primeiros 200 chars):")
            for content in categorias.contents:
                print(content.text[:200])

            print()

            # Chama echo_mercado
            print("Chamando echo_mercado...")
            eco = await session.call_tool("echo_mercado", {"mensagem": "teste-protocolo-2026"})
            for content in eco.content:
                print(f"Echo: {content.text}")


if __name__ == "__main__":
    asyncio.run(main())
