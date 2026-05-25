# src/auth.py
# Capitulo 10: Autenticacao JWT para o servidor MCP
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt

from src.config import JWT_ALGORITHM, JWT_EXPIRY_HOURS, JWT_SECRET

security = HTTPBearer()


def criar_token(
    cliente_id: str,
    horas_validade: Optional[int] = None,
    dados_extras: Optional[dict] = None
) -> str:
    """Cria um JWT assinado para um cliente."""
    validade = horas_validade or JWT_EXPIRY_HOURS
    agora = datetime.now(timezone.utc)

    payload = {
        "sub": cliente_id,
        "iat": agora,
        "exp": agora + timedelta(hours=validade),
        "client": cliente_id
    }
    if dados_extras:
        payload.update(dados_extras)

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def validar_token(token: str) -> dict:
    """Valida um JWT e retorna o payload. Lanca HTTPException se invalido."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def verificar_autenticacao(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """Dependencia FastAPI para validar autenticacao em endpoints protegidos."""
    return validar_token(credentials.credentials)
