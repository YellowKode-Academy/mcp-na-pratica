# Dockerfile
# Capitulo 11: Build multi-stage para o servidor market-intelligence MCP

# Estagio 1: Dependencias
FROM python:3.11-slim AS dependencies

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Estagio 2: Aplicacao
FROM python:3.11-slim AS application

WORKDIR /app

# Copia apenas as dependencias instaladas do primeiro estagio
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copia o codigo da aplicacao
COPY src/ ./src/

# Variaveis de ambiente com valores padrao seguros
ENV PYTHONUNBUFFERED=1
ENV LOG_FORMAT=json
ENV LOG_LEVEL=INFO
ENV PORT=8000

EXPOSE 8000

# Health check integrado ao Docker
# O proprio orquestrador reinicia o container se o servidor parar de responder
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# O ${PORT} permite que plataformas como Railway injetem a porta via variavel de ambiente
CMD ["sh", "-c", "uvicorn src.server_http:app --host 0.0.0.0 --port ${PORT}"]
