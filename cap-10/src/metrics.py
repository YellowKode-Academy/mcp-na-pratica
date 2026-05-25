# src/metrics.py
# Capitulo 10: Metricas Prometheus para o servidor MCP
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
)

# Total de chamadas a tools MCP, por tool e status
TOOL_CALLS = Counter(
    "mcp_tool_calls_total",
    "Total de chamadas a tools MCP",
    ["tool_name", "status"]  # status: sucesso, fallback, erro
)

# Latencia das chamadas a tools MCP (histograma)
TOOL_LATENCY = Histogram(
    "mcp_tool_latency_seconds",
    "Latencia das chamadas a tools MCP em segundos",
    ["tool_name"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Numero de conexoes SSE ativas no momento
SSE_CONNECTIONS = Gauge(
    "mcp_sse_connections_active",
    "Numero de conexoes SSE ativas"
)

# Total de falhas de autenticacao, por motivo
AUTH_FAILURES = Counter(
    "mcp_auth_failures_total",
    "Total de falhas de autenticacao",
    ["motivo"]  # motivo: token_ausente, token_expirado, token_invalido
)

# Total de requests ao servidor, por metodo e status
HTTP_REQUESTS = Counter(
    "mcp_http_requests_total",
    "Total de requests HTTP ao servidor",
    ["method", "path", "status_code"]
)
