# backend/tests/test_synthesis_helpers.py
"""
Tests para las funciones auxiliares del servicio de síntesis.
"""

import pytest

from app.services.synthesis_service import SynthesisCategoryChunks


@pytest.fixture
def service():
    """Instancia SynthesisCategoryChunks (clientes Azure mockeados por conftest)."""
    return SynthesisCategoryChunks()


class TestExtractYearFromDocname:
    """Tests para SynthesisCategoryChunks.extract_year_from_docname()"""

    def test_extracts_year_from_standard_name(self, service):
        result = service.extract_year_from_docname("Sentencia-Veloza-García-2012.pdf")
        assert result == 2012

    def test_extracts_most_recent_year(self, service):
        """Si hay múltiples años, debe devolver el más reciente."""
        result = service.extract_year_from_docname("Sentencia-1999-apelacion-2012.pdf")
        assert result == 2012

    def test_no_year_returns_sf(self, service):
        result = service.extract_year_from_docname("documento-sin-año.pdf")
        assert result == "s.f."

    def test_empty_string_returns_none(self, service):
        result = service.extract_year_from_docname("")
        assert result is None

    def test_none_returns_none(self, service):
        result = service.extract_year_from_docname(None)
        assert result is None

    def test_recent_year(self, service):
        result = service.extract_year_from_docname("Informe-2025.pdf")
        assert result == 2025


class TestPrepareChunksForSynthesis:
    """Tests para SynthesisCategoryChunks.prepare_chunks_for_synthesis()"""

    def test_generates_apa_citation_tag(self, service):
        chunks = [
            {
                "document_name": "Sentencia-2012.pdf",
                "folder": "Bloque Bananero",
                "content": "Contenido de prueba",
                "page_numbers": [10],
            }
        ]
        result = service.prepare_chunks_for_synthesis(chunks)
        assert len(result) == 1
        assert "(Bloque Bananero, 2012)" in result[0]["apa_citation_tag"]

    def test_adds_letters_for_same_author_year(self, service):
        """Si hay dos chunks del mismo autor y año, deben tener letras a, b."""
        chunks = [
            {
                "document_name": "Sentencia-2012-A.pdf",
                "folder": "Bloque Bananero",
                "content": "Primer contenido",
                "page_numbers": [1],
            },
            {
                "document_name": "Sentencia-2012-B.pdf",
                "folder": "Bloque Bananero",
                "content": "Segundo contenido",
                "page_numbers": [5],
            },
        ]
        result = service.prepare_chunks_for_synthesis(chunks)
        tags = [r["apa_citation_tag"] for r in result]
        assert "(Bloque Bananero, 2012a)" in tags
        assert "(Bloque Bananero, 2012b)" in tags

    def test_generates_full_reference_string(self, service):
        chunks = [
            {
                "document_name": "Sentencia-Veloza-2012.pdf",
                "folder": "Bloque Calima",
                "content": "Contenido",
                "page_numbers": [42],
            }
        ]
        result = service.prepare_chunks_for_synthesis(chunks)
        ref = result[0]["full_reference_string"]
        assert "Bloque Calima" in ref
        assert "2012" in ref
        assert "Página: 42" in ref

    def test_empty_chunks_returns_empty(self, service):
        result = service.prepare_chunks_for_synthesis([])
        assert result == []
