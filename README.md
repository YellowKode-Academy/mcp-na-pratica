# MCP na Pratica com Python -- Codigo Companion

Repositorio de codigo do livro "MCP na Pratica com Python" (YellowKode Academy).

Cada diretorio `cap-XX/` contem o estado completo do projeto ao final do capitulo correspondente.

## Estrutura

```
mcp-na-pratica/
cap-01/      -- Servidor minimo: 2 tools via stdio
cap-02/      -- Protocolo JSON-RPC: 3 tools com listar_categorias
cap-03/      -- Tools async com SerpAPI + fallback + modulos src/tools/
cap-04/      -- Tres primitivas completas: Tools + Resources + Prompts
cap-05/      -- Transport HTTP/SSE com FastAPI + endpoints /health e /ready
cap-06/      -- Autenticacao JWT com middleware e scripts/generate_token.py
cap-07/      -- Workflows do Claude Desktop (referencia -- usa cap-06)
cap-08/      -- Cliente LangChain + agente MCP scripts/agent_mcp.py
cap-09/      -- Observabilidade: structlog + Prometheus + rate limiting
cap-10/      -- Testes: unit + integration + E2E + GitHub Actions
cap-11/      -- Docker: Dockerfile multi-stage + docker-compose.yml
cap-12/      -- Deploy em producao: Railway + CI/CD completo
```

## Como usar

Cada capitulo e autocontido. Navegue ate o diretorio do capitulo e siga as instrucoes:

```bash
cd cap-03
pip install -r requirements.txt
cp .env.example .env
# preencha .env com suas chaves
python src/server.py
```

## Servidor market-intelligence MCP

O projeto central e um servidor MCP chamado "market-intelligence" que evolui capitulo a capitulo.

### Ferramentas (Tools)

| Tool | Descricao | Capitulo |
|---|---|---|
| `echo_mercado` | Ecoa mensagem de volta (teste de conexao) | 1 |
| `buscar_tendencias` | Busca tendencias em uma area de mercado | 1 |
| `listar_categorias` | Lista categorias KDP com BSR e tendencia | 2 |
| `analisar_bsr` | Analisa BSR e preco medio de uma categoria | 3 |

### Resources

| URI | Descricao | Capitulo |
|---|---|---|
| `mercado://categorias` | Catalogo completo de categorias | 4 |
| `mercado://bsr/{categoria}` | Dados de BSR por categoria | 4 |

### Prompts

| Prompt | Descricao | Capitulo |
|---|---|---|
| `analisar_oportunidade` | Analise sistematica de um nicho KDP | 4 |
| `planejar_serie` | Planejamento de serie de livros | 4 |

## Variaveis de Ambiente

| Variavel | Obrigatoria | Descricao |
|---|---|---|
| `SERPAPI_KEY` | Nao | Chave SerpAPI para buscar dados reais |
| `JWT_SECRET` | Sim (cap 6+) | Chave para assinar tokens JWT |
| `JWT_ALGORITHM` | Nao | Algoritmo JWT (padrao: HS256) |
| `JWT_EXPIRY_HOURS` | Nao | Validade do token em horas (padrao: 24) |
| `LOG_FORMAT` | Nao | "json" (producao) ou "console" (dev) |
| `LOG_LEVEL` | Nao | Nivel de log (padrao: INFO) |
| `PORT` | Nao | Porta HTTP (padrao: 8000) |

## Comandos Uteis

```bash
# Testar servidor via MCP Inspector (cap 1-4)
mcp dev src/server.py

# Iniciar servidor HTTP (cap 5+)
uvicorn src.server_http:app --host 0.0.0.0 --port 8000 --reload

# Gerar token JWT (cap 6+)
python scripts/generate_token.py claude-desktop 720

# Testar protocolo via cliente Python (cap 8)
MCP_TOKEN=<token> python scripts/client_test.py

# Rodar agente LangChain (cap 8)
MCP_TOKEN=<token> ANTHROPIC_API_KEY=<key> python scripts/agent_mcp.py

# Executar testes (cap 10+)
pytest tests/test_tools.py tests/test_server.py -v

# Docker (cap 11+)
docker build -t market-intelligence-mcp:latest .
docker run --rm -p 8000:8000 -e JWT_SECRET=<secret> market-intelligence-mcp:latest
docker compose up
```

## Livro

"MCP na Pratica com Python" -- YellowKode Academy (2026)
Pen name: Kelvin Biffi
