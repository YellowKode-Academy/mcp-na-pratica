# src/server.py
# Capitulo 3: Servidor com async, fallback e modulos separados
from mcp.server.fastmcp import FastMCP

from src.config import SERPAPI_KEY
from src.tools.tendencias import buscar_tendencias_serpapi, TENDENCIAS_FALLBACK
from src.tools.categorias import buscar_dados_bsr, CATEGORIAS_BSR

server = FastMCP("market-intelligence")


@server.tool()
def echo_mercado(mensagem: str) -> str:
    """
    Ecoa uma mensagem de volta. Use para testar se o servidor esta funcionando.

    Args:
        mensagem: O texto a ser ecoado
    """
    return f"Servidor MCP de inteligencia de mercado recebeu: {mensagem}"


@server.tool()
async def buscar_tendencias(area: str, limite: int = 5) -> str:
    """
    Busca tendencias atuais em uma area de mercado ou tecnologia.

    Quando a SerpAPI esta configurada, busca dados reais da web.
    Sem configuracao, retorna dados curados do dataset interno.

    Use para identificar o que esta em alta, quais subgeneros crescem,
    ou quais tecnologias tem maior demanda no momento.

    Args:
        area: Area para pesquisar. Exemplos: "romantasy", "MCP Python", "dark romance KDP"
        limite: Numero de resultados (1 a 10, padrao 5)
    """
    limite = max(1, min(limite, 10))

    if SERPAPI_KEY:
        try:
            query = f"tendencias {area} 2026 mercado"
            resultados = await buscar_tendencias_serpapi(query, limite)
            if resultados:
                texto = f"Tendencias para '{area}' (fonte: web, {len(resultados)} resultados):\n\n"
                for i, r in enumerate(resultados, 1):
                    texto += f"{i}. {r['titulo']}\n"
                    if r['snippet']:
                        texto += f"   {r['snippet'][:200]}\n"
                    texto += "\n"
                return texto
        except Exception:
            pass  # Falha silenciosa -- cai para fallback

    area_upper = area.upper()
    mapeamento = {"IA": "IA", "AI": "IA", "PYTHON": "Python", "KDP": "KDP", "EBOOKS": "KDP"}
    area_mapeada = next((v for k, v in mapeamento.items() if k in area_upper), None)

    if area_mapeada and area_mapeada in TENDENCIAS_FALLBACK:
        tendencias = TENDENCIAS_FALLBACK[area_mapeada][:limite]
        return f"Tendencias em {area_mapeada} (dados internos):\n\n" + "\n".join(
            f"{i}. {t}" for i, t in enumerate(tendencias, 1)
        )

    return f"Nao encontrei tendencias para '{area}'. Tente: 'IA', 'Python', 'KDP', ou um subgenero especifico como 'romantasy'."


@server.tool()
async def analisar_bsr(categoria: str) -> str:
    """
    Analisa os dados de BSR (Best Seller Rank) de uma categoria KDP.

    Retorna BSR medio, preco medio, royalty estimado e nivel de competicao.
    Use para avaliar o potencial de uma categoria antes de publicar.

    Args:
        categoria: Slug da categoria KDP. Exemplos: "romantasy", "dark-romance",
                   "cozy-mystery", "litrpg", "cli-fi"
    """
    dados = await buscar_dados_bsr(categoria)

    if not dados:
        categorias_disponiveis = ", ".join(CATEGORIAS_BSR.keys())
        return f"Categoria '{categoria}' nao encontrada. Disponiveis: {categorias_disponiveis}"

    bsr = dados["bsr_medio"]
    if bsr == 0:
        nivel = "emergente (sem dados de BSR ainda)"
    elif bsr < 10000:
        nivel = "alto volume de vendas"
    elif bsr < 50000:
        nivel = "volume moderado"
    else:
        nivel = "volume baixo"

    resultado = f"Analise de BSR: {dados['nome']}\n\n"
    resultado += f"BSR medio: {bsr:,} ({nivel})\n"
    resultado += f"Preco medio: ${dados['preco_medio']:.2f}\n"
    resultado += f"Royalty estimado (70%): ${dados['royalty_estimado']:.2f} por venda\n"
    resultado += f"Tendencia atual: {dados['tendencia']}\n"

    return resultado


if __name__ == "__main__":
    server.run()
