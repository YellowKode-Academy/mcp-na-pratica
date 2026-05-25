# src/config.py
# Capitulo 4: Configuracao via variaveis de ambiente
import os
from dotenv import load_dotenv

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
MAX_RESULTADOS = int(os.getenv("MAX_RESULTADOS", "10"))

if not SERPAPI_KEY:
    print("[AVISO] SERPAPI_KEY nao configurada. Usando dados simulados.")
