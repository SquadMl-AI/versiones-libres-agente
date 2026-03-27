from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.services.dashboard_service import get_dashboard_metrics

router = APIRouter()

@router.get("/metrics", tags=["dashboard"])
def dashboard_metrics():
    """
    Devuelve métricas agregadas para el dashboard de uso.
    """
    try:
        metrics = get_dashboard_metrics()
        # Forzar siempre 200 y evitar ETag/caché
        return JSONResponse(content=metrics, headers={"Cache-Control": "no-store"})
    except Exception as e:
        return JSONResponse(
            content={"error": f'{type(e).__name__}: {str(e)}'},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            headers={"Cache-Control": "no-store"}
        )
