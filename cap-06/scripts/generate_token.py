#!/usr/bin/env python
# scripts/generate_token.py
# Capitulo 6: Gera tokens JWT de desenvolvimento
# Uso: python scripts/generate_token.py <cliente_id> [horas_validade]
# Exemplo: python scripts/generate_token.py claude-desktop 720
import json
import os
import sys

# Carrega variaveis de ambiente antes de importar o modulo
from dotenv import load_dotenv
load_dotenv()

# Verifica JWT_SECRET antes de importar (evita erro de import)
if not os.getenv("JWT_SECRET"):
    print("ERRO: JWT_SECRET nao configurado no .env")
    print("Gere uma chave: python -c \"import secrets; print(secrets.token_hex(32))\"")
    sys.exit(1)

from src.auth import criar_token


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/generate_token.py <cliente_id> [horas_validade]")
        print("Exemplo: python scripts/generate_token.py claude-desktop 720")
        sys.exit(1)

    cliente_id = sys.argv[1]
    horas = int(sys.argv[2]) if len(sys.argv) > 2 else 24

    token = criar_token(cliente_id, horas_validade=horas)

    print(f"\nToken gerado para: {cliente_id}")
    print(f"Validade: {horas} horas ({horas // 24} dias)\n")
    print(f"TOKEN:\n{token}\n")
    print("Configuracao para claude_desktop_config.json:")
    config = {
        "mcpServers": {
            "market-intelligence": {
                "url": "http://localhost:8000/sse",
                "headers": {
                    "Authorization": f"Bearer {token}"
                }
            }
        }
    }
    print(json.dumps(config, indent=2))


if __name__ == "__main__":
    main()
