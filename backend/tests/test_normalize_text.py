# backend/tests/test_normalize_text.py
"""
Tests para las funciones de normalización de texto usadas en los servicios RAG
y de búsqueda por categoría.
"""

import pytest

from app.services.search_category_service import SearchCategoryChunks


@pytest.fixture
def service():
    """Instancia SearchCategoryChunks (clientes Azure mockeados por conftest)."""
    return SearchCategoryChunks()


class TestNormalizeText:
    """Tests para SearchCategoryChunks.normalize_text()"""

    def test_lowercase(self, service):
        assert service.normalize_text("HOLA MUNDO") == "hola mundo"

    def test_remove_accents(self, service):
        result = service.normalize_text("Acción jurídica según código")
        assert result == "accion juridica segun codigo"

    def test_preserve_ñ(self, service):
        result = service.normalize_text("Niño español")
        assert "niño" in result
        assert "español" in result

    def test_remove_punctuation(self, service):
        result = service.normalize_text("¿Qué pasó? ¡Nada!")
        assert "?" not in result
        assert "¡" not in result
        assert "!" not in result

    def test_collapse_whitespace(self, service):
        result = service.normalize_text("  muchos   espacios   ")
        assert result == "muchos espacios"

    def test_strip_html(self, service):
        result = service.normalize_text("<p>Texto <b>con</b> HTML</p>")
        assert "<" not in result
        assert ">" not in result
        assert result == "texto con html"

    def test_empty_string(self, service):
        assert service.normalize_text("") == ""

    def test_combined_normalization(self, service):
        """Verifica que todas las normalizaciones se aplican juntas."""
        raw = "  <b>¿Cuáles FUERON los ARGUMENTOS de la Defensa?</b>  "
        result = service.normalize_text(raw)
        assert result == "cuales fueron los argumentos de la defensa"
