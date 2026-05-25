# src/logging_config.py
# Capitulo 10: Configuracao de logs estruturados com structlog
import logging
import os

import structlog


def configurar_logging(nivel: str = "INFO", formato: str = "json") -> None:
    """
    Configura o structlog para o servidor MCP.

    Args:
        nivel: Nivel de log (DEBUG, INFO, WARNING, ERROR)
        formato: "json" para producao, "console" para desenvolvimento local
    """
    nivel_numerico = getattr(logging, nivel.upper(), logging.INFO)

    # Processadores compartilhados
    processadores_compartilhados = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if formato == "console":
        # Saida colorida para desenvolvimento local
        processadores_compartilhados.append(structlog.dev.ConsoleRenderer())
    else:
        # JSON para producao
        processadores_compartilhados.append(structlog.processors.JSONRenderer())

    # Configura o logging padrao do Python antes do structlog
    logging.basicConfig(
        format="%(message)s",
        level=nivel_numerico,
    )

    structlog.configure(
        processors=processadores_compartilhados,
        wrapper_class=structlog.make_filtering_bound_logger(nivel_numerico),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


# Configura automaticamente ao importar
# Use LOG_FORMAT=console para desenvolvimento, LOG_FORMAT=json para producao
LOG_FORMAT = os.getenv("LOG_FORMAT", "json")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
configurar_logging(nivel=LOG_LEVEL, formato=LOG_FORMAT)
