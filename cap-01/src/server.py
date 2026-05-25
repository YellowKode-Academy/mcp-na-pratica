# src/server.py -- versao com 2 tools
# Capitulo 1: Seu Primeiro Servidor MCP em 30 Minutos
from mcp.server.fastmcp import FastMCP

# Criar a instancia do servidor com um nome descritivo
server = FastMCP("market-intelligence")

TENDENCIAS_SIMULADAS = {
    "IA": ["LLM agents", "MCP servers", "RAG avancado", "fine-tuning local"],
    "Python": ["FastAPI", "Pydantic v2", "asyncio", "uv package manager"],
    "KDP": ["romantasy", "dark romance", "cozy mystery", "cli-fi"],
}


@server.tool()
def echo_mercado(mensagem: str) -> str:
    """
    Ecoa uma mensagem de volta. Use para testar se o servidor esta funcionando.

    Args:
        mensagem: O texto a ser ecoado
    """
    return f"Servidor MCP de inteligencia de mercado recebeu: {mensagem}"


@server.tool()
def buscar_tendencias(categoria: str) -> str:
    """
    Busca tendencias de mercado para uma categoria especifica.

    Retorna uma lista de topicos em alta na categoria solicitada.
    Use para identificar oportunidades de mercado e nichos emergentes.

    Args:
        categoria: A categoria de mercado para pesquisar.
                   Valores validos: "IA", "Python", "KDP"
    """
    tendencias = TENDENCIAS_SIMULADAS.get(categoria.upper())

    if tendencias is None:
        categorias_disponiveis = ", ".join(TENDENCIAS_SIMULADAS.keys())
        return f"Categoria '{categoria}' nao encontrada. Disponiveis: {categorias_disponiveis}"

    resultado = f"Tendencias em {categoria}:\n"
    for i, tendencia in enumerate(tendencias, 1):
        resultado += f"{i}. {tendencia}\n"

    return resultado


if __name__ == "__main__":
    server.run()
