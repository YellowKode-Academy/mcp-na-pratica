# src/server.py -- tres tools com logica real
# Capitulo 2: O Protocolo MCP por Dentro
from mcp.server.fastmcp import FastMCP

server = FastMCP("market-intelligence")

TENDENCIAS_SIMULADAS = {
    "IA": ["LLM agents", "MCP servers", "RAG avancado", "fine-tuning local"],
    "Python": ["FastAPI", "Pydantic v2", "asyncio", "uv package manager"],
    "KDP": ["romantasy", "dark romance", "cozy mystery", "cli-fi"],
}

# Dados de categorias KDP com BSR medio e preco medio
CATEGORIAS_KDP = {
    "romantasy": {
        "nome": "Romantasy",
        "bsr_medio": 5000,
        "preco_medio": 4.99,
        "tendencia": "muito alta",
    },
    "dark-romance": {
        "nome": "Dark Romance",
        "bsr_medio": 8000,
        "preco_medio": 3.99,
        "tendencia": "alta",
    },
    "cozy-mystery": {
        "nome": "Cozy Mystery",
        "bsr_medio": 15000,
        "preco_medio": 3.99,
        "tendencia": "estavel",
    },
    "litrpg": {
        "nome": "LitRPG",
        "bsr_medio": 12000,
        "preco_medio": 4.99,
        "tendencia": "alta",
    },
    "cli-fi": {
        "nome": "Cli-Fi (Climate Fiction)",
        "bsr_medio": 0,
        "preco_medio": 5.99,
        "tendencia": "emergente",
    },
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


@server.tool()
def listar_categorias(filtrar_por_tendencia: str = "") -> str:
    """
    Lista as categorias de mercado disponiveis com dados de BSR e tendencia.

    Use para dar ao usuario uma visao geral do mercado antes de uma analise
    mais profunda. Pode filtrar por tendencia para mostrar apenas as categorias
    em alta ou estaveis.

    Args:
        filtrar_por_tendencia: Filtra categorias por tendencia.
                                Valores validos: "alta", "muito alta", "estavel", "emergente".
                                Deixe vazio para listar todas.
    """
    categorias = list(CATEGORIAS_KDP.values())

    if filtrar_por_tendencia:
        categorias = [
            cat for cat in categorias
            if cat["tendencia"].lower() == filtrar_por_tendencia.lower()
        ]
        if not categorias:
            tendencias_disponiveis = list(set(c["tendencia"] for c in CATEGORIAS_KDP.values()))
            return f"Nenhuma categoria com tendencia '{filtrar_por_tendencia}'. Disponiveis: {', '.join(tendencias_disponiveis)}"

    resultado = "Categorias de mercado disponiveis:\n\n"
    for cat in categorias:
        bsr_info = f"BSR medio: {cat['bsr_medio']:,}" if cat['bsr_medio'] > 0 else "BSR: sem dados ainda"
        resultado += f"**{cat['nome']}**\n"
        resultado += f"  Tendencia: {cat['tendencia']}\n"
        resultado += f"  {bsr_info} | Preco medio: ${cat['preco_medio']:.2f}\n\n"

    return resultado


if __name__ == "__main__":
    server.run()
