# backend/tests/test_odata_filter.py
"""
Tests para la construcción de filtros OData usados en Azure AI Search.
"""

import pytest

from app.services.search_category_service import SearchCategoryChunks


@pytest.fixture
def service():
    """Instancia SearchCategoryChunks (clientes Azure mockeados por conftest)."""
    return SearchCategoryChunks()


class TestBuildOdataFilter:
    """Tests para SearchCategoryChunks.build_odata_filter()"""

    def test_no_filters_returns_none(self, service):
        assert service.build_odata_filter(None, None) is None

    def test_empty_lists_returns_none(self, service):
        assert service.build_odata_filter([], []) is None

    def test_single_collection(self, service):
        result = service.build_odata_filter(["Bloque Bananero"], None)
        assert "search.in(bloque" in result
        assert "Bloque Bananero" in result

    def test_multiple_collections(self, service):
        result = service.build_odata_filter(["Bloque Bananero", "Bloque Calima"], None)
        assert "Bloque Bananero" in result
        assert "Bloque Calima" in result

    def test_single_document(self, service):
        result = service.build_odata_filter(None, ["Sentencia-2012.pdf"])
        assert "search.in(docnm" in result
        assert "Sentencia-2012.pdf" in result

    def test_collections_and_documents_combined(self, service):
        result = service.build_odata_filter(["Bloque Norte"], ["Doc1.pdf", "Doc2.pdf"])
        assert " and " in result
        assert "bloque" in result
        assert "docnm" in result

    def test_escapes_single_quotes(self, service):
        """Verifica que las comillas simples se escapan para prevenir inyección OData."""
        result = service.build_odata_filter(["Bloque O'Brien"], None)
        assert "O''Brien" in result
