#!/usr/bin/env python
# scripts/agent_mcp.py
# Capitulo 8: Agente LangChain usando ferramentas do servidor MCP
# Uso: MCP_TOKEN=<token> ANTHROPIC_API_KEY=<key> python scripts/agent_mcp.py
import asyncio
import os

from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession
from mcp.client.sse import sse_client

SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/sse")
JWT_TOKEN = os.getenv("MCP_TOKEN", "")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")


async def criar_agente_mcp():
    """Cria e executa um agente LangChain usando tools do servidor MCP."""
    if not JWT_TOKEN:
        print("ERRO: configure MCP_TOKEN no ambiente")
        return
    if not ANTHROPIC_KEY:
        print("ERRO: configure ANTHROPIC_API_KEY no ambiente")
        return

    headers = {"Authorization": f"Bearer {JWT_TOKEN}"}

    print(f"Conectando ao servidor MCP: {SERVER_URL}")

    async with sse_client(SERVER_URL, headers=headers) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Carrega e converte todas as tools MCP para BaseTool do LangChain
            tools = await load_mcp_tools(session)
            print(f"Tools carregadas: {[t.name for t in tools]}")

            llm = ChatAnthropic(
                model="claude-opus-4-7-20251101",
                api_key=ANTHROPIC_KEY
            )

            template = """Voce e um especialista em analise de mercado KDP.
Ferramentas disponiveis:
{tools}

Use o formato:
Pensamento: [reflexao sobre o que fazer]
Acao: [nome da ferramenta]
Input da Acao: [input em JSON]
Observacao: [resultado da ferramenta]
... (repita quantas vezes precisar)
Resposta Final: [resposta para o usuario]

Pergunta: {input}
{agent_scratchpad}"""

            prompt = PromptTemplate(
                template=template,
                input_variables=["input", "tools", "tool_names", "agent_scratchpad"]
            )

            agent = create_react_agent(llm, tools, prompt)
            executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                max_iterations=5
            )

            print("\n" + "=" * 60)
            print("Executando analise de mercado...")
            print("=" * 60 + "\n")

            resultado = await executor.ainvoke({
                "input": (
                    "Analise o potencial de mercado para romantasy em 2026. "
                    "Compare com dark romance e recomende qual focar primeiro."
                )
            })

            print("\n" + "=" * 60)
            print("RESPOSTA FINAL:")
            print("=" * 60)
            print(resultado["output"])


if __name__ == "__main__":
    asyncio.run(criar_agente_mcp())
