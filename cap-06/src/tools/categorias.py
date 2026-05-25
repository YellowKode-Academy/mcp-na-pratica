# src/tools/categorias.py
# Capitulo 6: Dados de categorias KDP (mesmo codigo do cap-03)

CATEGORIAS_BSR = {
    "romantasy": {
        "nome": "Romantasy",
        "bsr_medio": 5000,
        "preco_medio": 4.99,
        "tendencia": "muito alta",
        "royalty_estimado": round(4.99 * 0.70, 2),
    },
    "dark-romance": {
        "nome": "Dark Romance",
        "bsr_medio": 8000,
        "preco_medio": 3.99,
        "tendencia": "alta",
        "royalty_estimado": round(3.99 * 0.70, 2),
    },
    "cozy-mystery": {
        "nome": "Cozy Mystery",
        "bsr_medio": 15000,
        "preco_medio": 3.99,
        "tendencia": "estavel",
        "royalty_estimado": round(3.99 * 0.70, 2),
    },
    "litrpg": {
        "nome": "LitRPG",
        "bsr_medio": 12000,
        "preco_medio": 4.99,
        "tendencia": "alta",
        "royalty_estimado": round(4.99 * 0.70, 2),
    },
    "cli-fi": {
        "nome": "Cli-Fi (Climate Fiction)",
        "bsr_medio": 0,
        "preco_medio": 5.99,
        "tendencia": "emergente",
        "royalty_estimado": round(5.99 * 0.70, 2),
    },
    "dark-academia": {
        "nome": "Dark Academia",
        "bsr_medio": 20000,
        "preco_medio": 4.49,
        "tendencia": "alta",
        "royalty_estimado": round(4.49 * 0.70, 2),
    },
    "psychological-thriller": {
        "nome": "Psychological Thriller",
        "bsr_medio": 7000,
        "preco_medio": 4.99,
        "tendencia": "muito alta",
        "royalty_estimado": round(4.99 * 0.70, 2),
    },
}


async def buscar_dados_bsr(categoria: str) -> dict | None:
    """Retorna dados de BSR para uma categoria. None se nao encontrada."""
    return CATEGORIAS_BSR.get(categoria)
