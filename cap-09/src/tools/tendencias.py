# src/tools/tendencias.py
# Capitulo 9: Ferramentas de tendencias (mesmo codigo do cap-03)
import asyncio

import httpx

from src.config import SERPAPI_KEY

SERPAPI_BASE = "https://serpapi.com/search.json"

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
