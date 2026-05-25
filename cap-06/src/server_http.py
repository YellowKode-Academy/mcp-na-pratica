# src/server_http.py
# Capitulo 6: Servidor HTTP com autenticacao JWT
import json
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mcp.server.fastmcp import FastMCP

from src.auth import validar_token
from src.config import JWT_SECRET, SERPAPI_KEY
from src.tools.categorias import CATEGORIAS_BSR, buscar_dados_bsr
from src.tools.tendencias import TENDENCIAS_FALLBACK, buscar_tendencias_serpapi

START_TIME = time.time()

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
            pass

    area_upper = area.upper()
    mapeamento = {"IA": "IA", "AI": "IA", "PYTHON": "Python", "KDP": "KDP", "EBOOKS": "KDP"}
    area_mapeada = next((v for k, v in mapeamento.items() if k in area_upper), None)

    if area_mapeada and area_mapeada in TENDENCIAS_FALLBACK:
        tendencias = TENDENCIAS_FALLBACK[area_mapeada][:limite]
        return f"Tendencias em {area_mapeada} (dados internos):\n\n" + "\n".join(
            f"{i}. {t}" for i, t in enumerate(tendencias, 1)
        )

    return f"Nao encontrei tendencias para '{area}'."


@server.tool()
async def analisar_bsr(categoria: str) -> str:
    """
    Analisa os dados de BSR (Best Seller Rank) de uma categoria KDP.

    Args:
        categoria: Slug da categoria KDP. Exemplos: "romantasy", "dark-romance"
    """
    dados = await buscar_dados_bsr(categoria)

    if not dados:
        return f"Categoria '{categoria}' nao encontrada. Disponiveis: {', '.join(CATEGORIAS_BSR.keys())}"

    bsr = dados["bsr_medio"]
    nivel = (
        "emergente (sem dados)" if bsr == 0
        else "alto volume" if bsr < 10000
        else "volume moderado" if bsr < 50000
        else "volume baixo"
    )

    return (
        f"Analise de BSR: {dados['nome']}\n\n"
        f"BSR medio: {bsr:,} ({nivel})\n"
        f"Preco medio: ${dados['preco_medio']:.2f}\n"
        f"Royalty estimado (70%): ${dados['royalty_estimado']:.2f} por venda\n"
        f"Tendencia atual: {dados['tendencia']}\n"
    )


# ============================================================
# RESOURCES
# ============================================================

@server.resource("mercado://categorias")
def listar_categorias_resource() -> str:
    """Lista todas as categorias de mercado disponiveis."""
    categorias = [
        {"slug": slug, "nome": d["nome"], "tendencia": d["tendencia"], "preco_medio": d["preco_medio"]}
        for slug, d in CATEGORIAS_BSR.items()
    ]
    return json.dumps(categorias, ensure_ascii=False, indent=2)


@server.resource("mercado://bsr/{categoria}")
def bsr_por_categoria(categoria: str) -> str:
    """Retorna dados de BSR para uma categoria especifica."""
    dados = CATEGORIAS_BSR.get(categoria)
    if not dados:
        return json.dumps({"erro": f"'{categoria}' nao encontrada", "disponiveis": list(CATEGORIAS_BSR.keys())})

    bsr = dados["bsr_medio"]
    nivel = "emergente" if bsr == 0 else "alto volume" if bsr < 10000 else "volume moderado" if bsr < 50000 else "volume baixo"

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
    """Template de analise de oportunidade de mercado para um nicho KDP."""
    return f"""Voce e um especialista em analise de mercado KDP.

Analise a oportunidade para: **{nicho}** | Publico: {publico_alvo}

1. Use buscar_tendencias para identificar tendencias atuais
2. Use analisar_bsr para verificar benchmarks de volume de vendas
3. Liste 3-5 concorrentes com BSR, preco e rating
4. Score de oportunidade 1-10 com justificativa
5. Decisao: ENTRAR / AGUARDAR / NAO ENTRAR"""


@server.prompt()
def planejar_serie(genero: str, num_livros: int = 3) -> str:
    """Template para planejar uma serie de livros para o KDP."""
    return f"""Planeje uma serie de {num_livros} livros no genero: **{genero}**

1. Use analisar_bsr para verificar o potencial do genero
2. Defina o gancho do livro 1
3. Estrategia de preco e Kindle Unlimited"""


# ============================================================
# FASTAPI APP
# ============================================================

from fastapi import FastAPI as _FastAPI
_mcp_app = server.sse_app()
app = _FastAPI(title="Market Intelligence MCP Server")

# Rotas que nao precisam de autenticacao
ROTAS_PUBLICAS = {"/health", "/ready", "/docs", "/openapi.json", "/redoc"}


@app.middleware("http")
async def autenticar_requests(request: Request, call_next):
    """Valida JWT em todos os requests, exceto rotas publicas."""
    if request.url.path in ROTAS_PUBLICAS:
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={
                "detail": "Token de autenticacao ausente",
                "hint": "Inclua: Authorization: Bearer <token>"
            }
        )

    try:
        payload = validar_token(auth_header[7:])
        request.state.cliente_id = payload.get("sub", "desconhecido")
        request.state.token_payload = payload
    except Exception as e:
        return JSONResponse(status_code=401, content={"detail": str(e)})

    return await call_next(request)


@app.get("/health")
async def health_check():
    """Health check endpoint para monitoramento."""
    return JSONResponse({
        "status": "healthy",
        "uptime_seconds": round(time.time() - START_TIME),
        "server": "market-intelligence-mcp",
        "version": "1.0.0"
    })


@app.get("/ready")
async def readiness_check():
    """Readiness check -- verifica se o servidor esta pronto para trafego."""
    checks = {
        "mcp_server": True,
        "jwt_configured": bool(JWT_SECRET),
        "serpapi_configured": bool(SERPAPI_KEY)
    }
    all_ready = checks["mcp_server"] and checks["jwt_configured"]
    return JSONResponse(
        content={"ready": all_ready, "checks": checks},
        status_code=200 if all_ready else 503
    )


app.mount("/", _mcp_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
