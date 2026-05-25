# src/server.py
# Capitulo 4: Servidor com as tres primitivas MCP (Tools + Resources + Prompts)
import json

from mcp.server.fastmcp import FastMCP

from src.config import SERPAPI_KEY
from src.tools.tendencias import buscar_tendencias_serpapi, TENDENCIAS_FALLBACK
from src.tools.categorias import buscar_dados_bsr, CATEGORIAS_BSR

server = FastMCP("market-intelligence")


# ============================================================
# TOOLS
# ============================================================

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


# ============================================================
# RESOURCES
# ============================================================

@server.resource("mercado://categorias")
def listar_categorias_resource() -> str:
    """
    Lista todas as categorias de mercado com seus identificadores e metadados.

    Use este resource para obter o catalogo completo de categorias disponiveis
    no servidor de inteligencia de mercado.
    """
    categorias = [
        {
            "slug": slug,
            "nome": dados["nome"],
            "tendencia": dados["tendencia"],
            "preco_medio": dados["preco_medio"]
        }
        for slug, dados in CATEGORIAS_BSR.items()
    ]

    return json.dumps(categorias, ensure_ascii=False, indent=2)


@server.resource("mercado://bsr/{categoria}")
def bsr_por_categoria(categoria: str) -> str:
    """
    Retorna dados de BSR e analise de mercado para uma categoria especifica.
    URI: mercado://bsr/{categoria}
    Exemplo: mercado://bsr/romantasy
    """
    dados = CATEGORIAS_BSR.get(categoria)

    if not dados:
        return json.dumps({
            "erro": f"Categoria '{categoria}' nao encontrada",
            "disponiveis": list(CATEGORIAS_BSR.keys())
        }, ensure_ascii=False, indent=2)

    bsr = dados["bsr_medio"]
    nivel = (
        "emergente" if bsr == 0
        else "alto volume" if bsr < 10000
        else "volume moderado" if bsr < 50000
        else "volume baixo"
    )

    return json.dumps({
        "categoria": dados["nome"],
        "slug": categoria,
        "bsr": {"valor": bsr, "nivel": nivel},
        "preco_medio": dados["preco_medio"],
        "tendencia": dados["tendencia"],
        "royalty_estimado_70pct": round(dados["preco_medio"] * 0.70, 2)
    }, ensure_ascii=False, indent=2)


# ============================================================
# PROMPTS
# ============================================================

@server.prompt()
def analisar_oportunidade(nicho: str, publico_alvo: str = "geral") -> str:
    """
    Template de analise de oportunidade de mercado para um nicho KDP.

    Guia o Claude na analise sistematica: demanda, competicao, viabilidade e gaps.

    Args:
        nicho: O nicho ou subgenero a analisar
        publico_alvo: Publico-alvo do livro (padrao: geral)
    """
    return f"""Voce e um especialista em analise de mercado KDP.

Analise a oportunidade para: **{nicho}** | Publico: {publico_alvo}

1. Use buscar_tendencias para identificar tendencias atuais
2. Use analisar_bsr para verificar benchmarks de volume de vendas
3. Liste 3-5 concorrentes com BSR, preco e rating
4. Identifique gaps: o que os concorrentes nao cobrem?
5. Score de oportunidade 1-10 com justificativa
6. Decisao: ENTRAR / AGUARDAR / NAO ENTRAR

Baseie tudo em dados. Seja direto."""


@server.prompt()
def planejar_serie(genero: str, num_livros: int = 3) -> str:
    """
    Template para planejar uma serie de livros para o KDP.

    Gera um plano de serie considerando as regras do mercado KDP:
    livro 1 como isca, progressao de preco, e estrategia de KU.

    Args:
        genero: O genero da serie (ex: "romantasy", "LitRPG", "cozy mystery")
        num_livros: Numero de livros planejados para a serie (padrao: 3)
    """
    return f"""Voce e um especialista em publicacao KDP e estrategia de series.

Planeje uma serie de {num_livros} livros no genero: **{genero}**

1. Use analisar_bsr para verificar o potencial do genero
2. Defina o gancho do livro 1 (deve ser o mais forte da serie)
3. Mapeie os arcos narrativos por livro
4. Estrategia de preco: livro 1 como isca ($0.99 ou KU), progressao nos seguintes
5. Recomendacao de Kindle Unlimited vs venda direta para este genero
6. Frequencia de lancamento ideal baseada no BSR do genero

Foque em dados de mercado e estrategia de publicacao, nao em sinopse."""


if __name__ == "__main__":
    server.run()
