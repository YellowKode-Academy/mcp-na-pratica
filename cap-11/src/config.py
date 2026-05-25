# src/config.py
# Capitulo 11: Configuracao com variaveis JWT
import os

from dotenv import load_dotenv

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
MAX_RESULTADOS = int(os.getenv("MAX_RESULTADOS", "10"))

# Configuracoes JWT -- obrigatorias para o servidor HTTP
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))

if not SERPAPI_KEY:
    print("[AVISO] SERPAPI_KEY nao configurada. Usando dados simulados.")

# JWT_SECRET e obrigatorio -- falha rapida e clara
if not JWT_SECRET:
    raise ValueError(
        "JWT_SECRET nao configurado. "
        "Gere uma chave com: python -c \"import secrets; print(secrets.token_hex(32))\""
    )
