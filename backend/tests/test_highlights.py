# backend/tests/test_highlights.py
"""
Tests para las funciones estáticas de highlights del servicio de búsqueda.
"""

from app.services.search_category_service import SearchCategoryChunks


class TestRemoveStopwordHighlights:
    """Tests para SearchCategoryChunks._remove_stopword_highlights()"""

    def test_removes_em_from_stopwords(self):
        stopwords = {"el", "la", "de"}
        text = "<em>el</em> caso <em>de</em> <em>Veloza</em>"
        result = SearchCategoryChunks._remove_stopword_highlights(text, stopwords)
        assert result == "el caso de <em>Veloza</em>"

    def test_preserves_em_on_non_stopwords(self):
        stopwords = {"el", "la"}
        text = "<em>García</em> fue <em>condenado</em>"
        result = SearchCategoryChunks._remove_stopword_highlights(text, stopwords)
        assert "<em>García</em>" in result
        assert "<em>condenado</em>" in result

    def test_empty_text(self):
        result = SearchCategoryChunks._remove_stopword_highlights("", {"el"})
        assert result == ""


class TestExtractHighlightedPhrases:
    """Tests para SearchCategoryChunks._extract_highlighted_phrases()"""

    def test_extracts_phrases(self):
        highlights = [
            "El <em>caso</em> de <em>Veloza</em> García",
            "La <em>sentencia</em> del tribunal",
        ]
        result = SearchCategoryChunks._extract_highlighted_phrases(highlights)
        assert "caso" in result
        assert "Veloza" in result
        assert "sentencia" in result

    def test_empty_list(self):
        result = SearchCategoryChunks._extract_highlighted_phrases([])
        assert result == set()

    def test_no_highlighted_words(self):
        result = SearchCategoryChunks._extract_highlighted_phrases(["Sin resaltados"])
        assert result == set()


class TestHighlightPhrasesInContent:
    """Tests para SearchCategoryChunks._highlight_phrases_in_content()"""

    def test_highlights_matching_phrases(self):
        content = "El caso de Veloza fue revisado"
        phrases = {"Veloza"}
        result = SearchCategoryChunks._highlight_phrases_in_content(content, phrases)
        assert "<em>Veloza</em>" in result

    def test_case_insensitive(self):
        content = "veloza VELOZA Veloza"
        phrases = {"Veloza"}
        result = SearchCategoryChunks._highlight_phrases_in_content(content, phrases)
        assert result.count("<em>") == 3

    def test_empty_phrases_returns_original(self):
        content = "Texto sin cambios"
        result = SearchCategoryChunks._highlight_phrases_in_content(content, set())
        assert result == content

    def test_multiple_phrases(self):
        content = "García y Veloza fueron condenados"
        phrases = {"García", "Veloza"}
        result = SearchCategoryChunks._highlight_phrases_in_content(content, phrases)
        assert "<em>García</em>" in result
        assert "<em>Veloza</em>" in result
