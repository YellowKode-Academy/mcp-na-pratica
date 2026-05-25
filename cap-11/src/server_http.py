# src/server_http.py
# Capitulo 11: Servidor HTTP com Docker e deploy local
# Adiciona: logs estruturados, correlation IDs, metricas Prometheus, rate limiting
import json
import time
import uuid
from collections import defaultdict

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse, Response
from mcp.server.fastmcp import FastMCP
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from src.auth import validar_token
from src.config import JWT_SECRET, SERPAPI_KEY
from src.logging_config import LOG_FORMAT, LOG_LEVEL  # Configura logging ao importar
from src.metrics import AUTH_FAILURES, TOOL_CALLS, TOOL_LATENCY
from src.tools.categorias import CATEGORIAS_BSR, buscar_dados_bsr
from src.tools.tendencias import TENDENCIAS_FALLBACK, buscar_tendencias_serpapi

logger = structlog.get_logger(__name__)
START_TIME = time.time()
MAX_CHAMADAS_POR_MINUTO = 60

# Rate limiting em memoria (para producao com multiplas instancias, use Redis)
_chamadas_por_cliente: dict[str, list[float]] = defaultdict(list)

server = FastMCP("market-intelligence")


# ============================================================
# TOOLS com logs estruturados e metricas
# ============================================================

@server.tool()
def echo_mercado(mensagem: str) -> str:
    """
    Ecoa uma mensagem de volta. Use para testar se o servidor esta funcionando.

    Args:
        mensagem: O texto a ser ecoado
    """
    logger.info("tool_call", tool="echo_mercado", mensagem=mensagem)
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
    inicio = time.monotonic()
    log = logger.bind(tool="buscar_tendencias", area=area, limite=limite)
    log.info("tool_call_started")

    limite = max(1, min(limite, 10))

    try:
        if SERPAPI_KEY:
            query = f"tendencias {area} 2026 mercado"
            resultados = await buscar_tendencias_serpapi(query, limite)
            if resultados:
                latencia_ms = round((time.monotonic() - inicio) * 1000)
                log.info("tool_call_succeeded", fonte="serpapi",
                         num_resultados=len(resultados), latencia_ms=latencia_ms)
                TOOL_CALLS.labels(tool_name="buscar_tendencias", status="sucesso").inc()
                TOOL_LATENCY.labels(tool_name="buscar_tendencias").observe(time.monotonic() - inicio)

                texto = f"Tendencias para '{area}' (fonte: web):\n\n"
                for i, r in enumerate(resultados, 1):
                    texto += f"{i}. {r['titulo']}\n"
                    if r['snippet']:
                        texto += f"   {r['snippet'][:200]}\n"
                    texto += "\n"
                return texto
    except Exception as e:
        latencia_ms = round((time.monotonic() - inicio) * 1000)
        log.warning("tool_call_fallback", erro=str(e),
                    erro_tipo=type(e).__name__, latencia_ms=latencia_ms)

    # Fallback para dados locais
    area_upper = area.upper()
    mapeamento = {"IA": "IA", "AI": "IA", "PYTHON": "Python", "KDP": "KDP", "EBOOKS": "KDP"}
    area_mapeada = next((v for k, v in mapeamento.items() if k in area_upper), None)

    if area_mapeada and area_mapeada in TENDENCIAS_FALLBACK:
        tendencias = TENDENCIAS_FALLBACK[area_mapeada][:limite]
        latencia_ms = round((time.monotonic() - inicio) * 1000)
        log.info("tool_call_succeeded", fonte="fallback_local",
                 num_resultados=len(tendencias), latencia_ms=latencia_ms)
        TOOL_CALLS.labels(tool_name="buscar_tendencias", status="fallback").inc()
        TOOL_LATENCY.labels(tool_name="buscar_tendencias").observe(time.monotonic() - inicio)
        return f"Tendencias em {area_mapeada}:\n\n" + "\n".join(
            f"{i}. {t}" for i, t in enumerate(tendencias, 1)
        )

    log.warning("tool_call_no_results", latencia_ms=round((time.monotonic() - inicio) * 1000))
    TOOL_CALLS.labels(tool_name="buscar_tendencias", status="sem_resultados").inc()
    return f"Nao encontrei tendencias para '{area}'."


@server.tool()
async def analisar_bsr(categoria: str) -> str:
    """
    Analisa os dados de BSR (Best Seller Rank) de uma categoria KDP.

    Args:
        categoria: Slug da categoria KDP. Exemplos: "romantasy", "dark-romance"
    """
    inicio = time.monotonic()
    log = logger.bind(tool="analisar_bsr", categoria=categoria)
    log.info("tool_call_started")

    dados = await buscar_dados_bsr(categoria)

    if not dados:
        log.warning("tool_call_not_found", latencia_ms=round((time.monotonic() - inicio) * 1000))
        TOOL_CALLS.labels(tool_name="analisar_bsr", status="nao_encontrado").inc()
        return f"Categoria '{categoria}' nao encontrada. Disponiveis: {', '.join(CATEGORIAS_BSR.keys())}"

    bsr = dados["bsr_medio"]
    nivel = (
        "emergente" if bsr == 0
        else "alto volume" if bsr < 10000
        else "volume moderado" if bsr < 50000
        else "volume baixo"
    )

    latencia_ms = round((time.monotonic() - inicio) * 1000)
    log.info("tool_call_succeeded", latencia_ms=latencia_ms)
    TOOL_CALLS.labels(tool_name="analisar_bsr", status="sucesso").inc()
    TOOL_LATENCY.labels(tool_name="analisar_bsr").observe(time.monotonic() - inicio)

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
        return json.dumps({"erro": f"'{categoria}' nao encontrada"})

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
3. Score de oportunidade 1-10 com justificativa
4. Decisao: ENTRAR / AGUARDAR / NAO ENTRAR"""


@server.prompt()
def planejar_serie(genero: str, num_livros: int = 3) -> str:
    """Template para planejar uma serie de livros para o KDP."""
    return f"""Planeje uma serie de {num_livros} livros no genero: **{genero}**

1. Use analisar_bsr para verificar o potencial
2. Estrategia de preco e Kindle Unlimited"""


# ============================================================
# FASTAPI APP + MIDDLEWARES
# ============================================================

from fastapi import FastAPI as _FastAPI
_mcp_app = server.sse_app()
app = _FastAPI(title="Market Intelligence MCP Server")

ROTAS_PUBLICAS = {"/health", "/ready", "/docs", "/openapi.json", "/redoc", "/metrics"}


@app.middleware("http")
async def middleware_rate_limit(request: Request, call_next):
    """Rate limiting por cliente (deve ser o primeiro middleware)."""
    if request.url.path in ROTAS_PUBLICAS:
        return await call_next(request)

    cliente_id = getattr(request.state, 'cliente_id', request.client.host if request.client else "unknown")
    agora = time.time()

    # Mantém apenas chamadas dos ultimos 60 segundos
    _chamadas_por_cliente[cliente_id] = [
        t for t in _chamadas_por_cliente[cliente_id] if t > agora - 60
    ]

    if len(_chamadas_por_cliente[cliente_id]) >= MAX_CHAMADAS_POR_MINUTO:
        logger.warning("rate_limit_excedido", cliente_id=cliente_id,
                       chamadas_no_minuto=len(_chamadas_por_cliente[cliente_id]))
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit excedido", "limite": f"{MAX_CHAMADAS_POR_MINUTO}/minuto"}
        )

    _chamadas_por_cliente[cliente_id].append(agora)
    return await call_next(request)


@app.middleware("http")
async def middleware_autenticacao(request: Request, call_next):
    """Valida JWT e adiciona correlation ID."""
    request.state.request_id = str(uuid.uuid4())[:8]

    if request.url.path in ROTAS_PUBLICAS:
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        AUTH_FAILURES.labels(motivo="token_ausente").inc()
        logger.warning("auth_falhou", motivo="token_ausente",
                       path=request.url.path, request_id=request.state.request_id)
        return JSONResponse(
            status_code=401,
            content={"detail": "Token de autenticacao ausente"}
        )

    try:
        payload = validar_token(auth_header[7:])
        request.state.cliente_id = payload.get("sub", "desconhecido")
        request.state.token_payload = payload
        logger.info("request_autenticado",
                    cliente_id=request.state.cliente_id,
                    path=request.url.path,
                    request_id=request.state.request_id)
    except Exception as e:
        AUTH_FAILURES.labels(motivo="token_invalido").inc()
        return JSONResponse(status_code=401, content={"detail": str(e)})

    return await call_next(request)


@app.get("/health")
async def health_check():
    """Health check para monitoramento (liveness probe)."""
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


@app.get("/metrics")
async def metrics():
    """Endpoint Prometheus para scraping de metricas."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.mount("/", _mcp_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
