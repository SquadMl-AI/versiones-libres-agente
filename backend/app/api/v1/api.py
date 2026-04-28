from fastapi import APIRouter

from app.api.v1.endpoints import (
    advance_search,
    blobs,
    chat_ask,
    feed_messages,
    feedback_synthesis,
    history_session,
    synthesis,
    users_auth,
)

api_router = APIRouter()
api_router.include_router(chat_ask.router, prefix="/chat_ask", tags=["chat"])
api_router.include_router(synthesis.router, prefix="/synthesis_chuks", tags=["chat"])
api_router.include_router(advance_search.router, prefix="/advance_search", tags=["chat"])
api_router.include_router(history_session.router, prefix="/sessions", tags=["gets"])
api_router.include_router(blobs.router_folders, prefix="/folders", tags=["gets"])
api_router.include_router(blobs.router_files, prefix="/files", tags=["gets"])
api_router.include_router(users_auth.router, prefix="/users_auth", tags=["gets"])
api_router.include_router(feedback_synthesis.router_interaction, prefix="", tags=["feeds"])
api_router.include_router(feedback_synthesis.router_graph, prefix="", tags=["feeds"])
api_router.include_router(feedback_synthesis.router_synthe, prefix="", tags=["feeds"])
api_router.include_router(feedback_synthesis.router_stats_synthe, prefix="", tags=["feeds"])
api_router.include_router(feed_messages.router, prefix="", tags=["feeds"])
