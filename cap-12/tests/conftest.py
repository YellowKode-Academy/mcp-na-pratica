# tests/conftest.py
# Capitulo 12: Fixtures compartilhadas entre os testes
import os

import pytest

# Configura variaveis de ambiente ANTES de importar qualquer modulo do servidor
# Critico: JWT_SECRET deve estar configurado antes do import de src.config
os.environ.setdefault("JWT_SECRET", "chave_de_teste_somente_nao_use_em_producao_abc123")
os.environ.setdefault("LOG_FORMAT", "console")
os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("SERPAPI_KEY", "")
