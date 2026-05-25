# Capitulo 7: Claude Desktop como Cliente MCP

Este capitulo nao adiciona novos arquivos de codigo ao servidor.
O foco e nos workflows de uso real do Claude Desktop como cliente MCP.

## Configuracao do Claude Desktop

Edite `claude_desktop_config.json` para apontar para o servidor HTTP com autenticacao:

```json
{
  "mcpServers": {
    "market-intelligence": {
      "url": "http://localhost:8000/sse",
      "headers": {
        "Authorization": "Bearer SEU_TOKEN_AQUI"
      }
    }
  }
}
```

## Como iniciar o servidor para uso com Claude Desktop

```bash
uvicorn src.server_http:app --host 0.0.0.0 --port 8000
```

## Workflows demonstrados no capitulo

### 1. Analise de nicho de mercado
Pergunte ao Claude: "Quero publicar no KDP em romantasy. Faz sentido?"
O Claude chamara buscar_tendencias e analisar_bsr automaticamente.

### 2. Usando o prompt de analise
Selecione o prompt `analisar_oportunidade` na interface do Claude Desktop,
preencha `nicho` e `publico_alvo`, e o Claude executara a analise sistematica.

### 3. Analise comparativa
Pergunte: "Compare romantasy e dark romance. Qual tem melhor retorno para um estreante?"
O Claude chamara analisar_bsr para os dois e comparara.

### 4. Combinando tool e resource
Pergunte: "Lista as categorias e me diz qual tem a melhor oportunidade para iniciantes."
O Claude pode acessar o resource mercado://categorias e chamar analisar_bsr.

## Logs do servidor em tempo real

Adicione este trecho no inicio de cada tool para ver as chamadas em tempo real:

```python
import logging
logger = logging.getLogger(__name__)

@server.tool()
async def buscar_tendencias(area: str, limite: int = 5) -> str:
    logger.info("buscar_tendencias chamada", extra={"area": area, "limite": limite})
    # ... resto da funcao
```

## Estrutura de arquivos usada

Este capitulo usa o mesmo servidor do cap-06.
Os arquivos de referencia estao em `../cap-06/`.
