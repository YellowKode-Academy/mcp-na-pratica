# tests/test_tools.py
# Capitulo 12: Unit tests das tools em isolamento
import pytest
from unittest.mock import AsyncMock, patch


class TestBuscarTendencias:
    async def test_retorna_tendencias_com_serpapi(self):
        """Quando SerpAPI esta configurada e responde, retorna resultados reais."""
        resultados_mockados = [
            {"titulo": "Romantasy explode nas vendas KDP", "snippet": "BookTok...", "link": "http://ex.com"}
        ]

        with patch("src.tools.tendencias.SERPAPI_KEY", "fake_key"), \
             patch("src.tools.tendencias.buscar_tendencias_serpapi",
                   AsyncMock(return_value=resultados_mockados)):
            from src.server_http import buscar_tendencias
            resultado = await buscar_tendencias("romantasy", 2)

        assert "Romantasy explode nas vendas KDP" in resultado
        assert "fonte: web" in resultado

    async def test_fallback_quando_serpapi_falha(self):
        """Quando SerpAPI falha, retorna dados locais sem propagar o erro."""
        with patch("src.tools.tendencias.SERPAPI_KEY", "fake_key"), \
             patch("src.tools.tendencias.buscar_tendencias_serpapi",
                   AsyncMock(side_effect=Exception("Connection error"))):
            from src.server_http import buscar_tendencias
            resultado = await buscar_tendencias("IA", 3)

        assert "Tendencias em IA" in resultado

    async def test_limite_maximo_10(self):
        """O limite e sempre no maximo 10, mesmo se o usuario pedir mais."""
        with patch("src.tools.tendencias.SERPAPI_KEY", ""):
            from src.server_http import buscar_tendencias
            resultado = await buscar_tendencias("IA", 50)

        linhas_numeradas = [l for l in resultado.split("\n") if l and l[0].isdigit()]
        assert len(linhas_numeradas) <= 10

    async def test_limite_minimo_1(self):
        """O limite e sempre no minimo 1."""
        with patch("src.tools.tendencias.SERPAPI_KEY", ""):
            from src.server_http import buscar_tendencias
            resultado = await buscar_tendencias("IA", 0)

        # Deve retornar ao menos 1 resultado
        assert resultado and len(resultado) > 0

    async def test_area_desconhecida_retorna_mensagem_util(self):
        """Para areas desconhecidas, retorna mensagem clara."""
        with patch("src.tools.tendencias.SERPAPI_KEY", ""):
            from src.server_http import buscar_tendencias
            resultado = await buscar_tendencias("xyzabc123")

        assert "Nao encontrei" in resultado

    async def test_alias_ai_mapeia_para_ia(self):
        """'AI' em ingles deve mapear para o dataset 'IA' em portugues."""
        with patch("src.tools.tendencias.SERPAPI_KEY", ""):
            from src.server_http import buscar_tendencias
            resultado = await buscar_tendencias("AI", 3)

        # Deve retornar dados do dataset IA
        assert "Nao encontrei" not in resultado


class TestAnalisarBsr:
    async def test_categoria_valida_retorna_dados(self):
        """Categorias conhecidas retornam dados de BSR estruturados."""
        from src.server_http import analisar_bsr
        resultado = await analisar_bsr("romantasy")

        assert "Romantasy" in resultado
        assert "BSR medio" in resultado
        assert "Preco medio" in resultado
        assert "Royalty" in resultado

    async def test_categoria_invalida_retorna_lista(self):
        """Categoria invalida retorna mensagem com lista das validas."""
        from src.server_http import analisar_bsr
        resultado = await analisar_bsr("xyz-invalida")

        assert "nao encontrada" in resultado.lower()
        assert "romantasy" in resultado.lower()

    async def test_bsr_zero_e_emergente(self):
        """Categoria com BSR 0 deve ser identificada como emergente."""
        from src.server_http import analisar_bsr
        resultado = await analisar_bsr("cli-fi")

        assert "emergente" in resultado.lower()

    async def test_royalty_calculado(self):
        """O royalty deve ser calculado corretamente (70% do preco medio)."""
        from src.server_http import analisar_bsr
        resultado = await analisar_bsr("romantasy")

        # Preco de romantasy e $4.99, royalty 70% = $3.49
        assert "3.49" in resultado


class TestEchoMercado:
    def test_retorna_mensagem_ecoada(self):
        """echo_mercado deve retornar a mensagem com o prefixo do servidor."""
        from src.server_http import echo_mercado
        resultado = echo_mercado("teste")

        assert "teste" in resultado
        assert "market-intelligence" in resultado.lower() or "inteligencia" in resultado.lower()
