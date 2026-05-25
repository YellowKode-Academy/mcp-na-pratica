# src/tools/tendencias.py
# Capitulo 3: Chamada assincrona a SerpAPI com fallback local
import asyncio

import httpx

from src.config import SERPAPI_KEY

SERPAPI_BASE = "https://serpapi.com/search.json"

# Dados de fallback para quando a SerpAPI nao esta configurada
TENDENCIAS_FALLBACK = {
    "IA": [
        "LLM agents autonomos",
        "MCP servers e integracao",
        "RAG avancado com multimodal",
        "fine-tuning local com LoRA",
        "agentes multi-tarefa",
        "modelos de raciocinio",
        "computer use e automacao",
        "embeddings semanticos",
    ],
    "Python": [
        "FastAPI e Pydantic v2",
        "asyncio e concorrencia",
        "uv package manager",
        "Ruff para linting",
        "Polars vs Pandas",
        "Typer para CLIs",
        "httpx para HTTP async",
        "structlog para logs",
    ],
    "KDP": [
        "romantasy (romance + fantasia)",
        "dark romance subgeneros",
        "cozy mystery com animais",
        "LitRPG series longas",
        "cli-fi (climate fiction)",
        "dark academia",
        "hockey romance",
        "reverse harem",
    ],
}


async def buscar_tendencias_serpapi(query: str, limite: int = 5) -> list[dict]:
    """Busca tendencias via SerpAPI. Retorna lista de resultados."""
    if not SERPAPI_KEY:
        raise ValueError("SERPAPI_KEY nao configurada")

    params = {
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": limite,
        "hl": "pt",
        "gl": "br"
    }

    # O timeout=10.0 e critico -- sem ele uma API lenta pode bloquear indefinidamente
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(SERPAPI_BASE, params=params)
        response.raise_for_status()
        data = response.json()

    return [
        {
            "titulo": item.get("title", ""),
            "snippet": item.get("snippet", ""),
            "link": item.get("link", "")
        }
        for item in data.get("organic_results", [])[:limite]
    ]


async def buscar_com_retry(query: str, limite: int, max_tentativas: int = 3) -> list[dict]:
    """Busca com retry automatico em caso de falha."""
    ultimo_erro = None

    for tentativa in range(max_tentativas):
        try:
            return await buscar_tendencias_serpapi(query, limite)
        except httpx.TimeoutException:
            ultimo_erro = f"Timeout na tentativa {tentativa + 1}"
            if tentativa < max_tentativas - 1:
                await asyncio.sleep(2 ** tentativa)  # 1s, 2s, 4s
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (429, 503):
                ultimo_erro = f"HTTP {e.response.status_code} na tentativa {tentativa + 1}"
                if tentativa < max_tentativas - 1:
                    await asyncio.sleep(2 ** tentativa)
            else:
                raise  # Erros 4xx (exceto 429) nao melhoram com retry

    raise Exception(f"Falha apos {max_tentativas} tentativas: {ultimo_erro}")
