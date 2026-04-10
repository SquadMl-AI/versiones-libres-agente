# backend/tests/test_smoke.py
"""
Smoke tests: verifican que los módulos principales del backend se pueden
importar sin errores de dependencia o de configuración.

Estos tests requieren que las dependencias completas del proyecto estén
instaladas (requirements.txt). En CI se ejecutan en el job 'test'.
"""

from unittest.mock import MagicMock

import pytest

# Verificar si las dependencias están instaladas realmente (no mockeadas)
try:
    import azure.search.documents

    HAS_FULL_DEPS = not isinstance(azure.search.documents, MagicMock)
except ImportError:
    HAS_FULL_DEPS = False

requires_full_deps = pytest.mark.skipif(
    not HAS_FULL_DEPS,
    reason="Requiere dependencias completas (requirements.txt) — no mockeadas",
)


@requires_full_deps
class TestAppImports:
    """Verifica que la aplicación FastAPI se puede construir correctamente."""

    def test_app_creates(self):
        """La app de FastAPI se importa y crea sin explotar."""
        from app.main import app

        assert app is not None
        assert app.title == "Memorias de Justicia y Paz API"

    def test_api_router_has_routes(self):
        """El router principal tiene rutas registradas."""
        from app.api.v1.api import api_router

        assert len(api_router.routes) > 0

    def test_expected_prefixes_registered(self):
        """Verifica que los prefijos de los endpoints activos están registrados."""
        from app.main import app

        route_paths = [r.path for r in app.routes]
        expected_fragments = [
            "/chat_ask",
            "/synthesis",
            "/advance_search",
            "/sessions",
            "/folders",
            "/files",
            "/users_auth",
            "/feedbacks",
            "/feed_message",
        ]
        for fragment in expected_fragments:
            assert any(fragment in path for path in route_paths), (
                f"No se encontró ruta con '{fragment}' en las rutas: {route_paths}"
            )
