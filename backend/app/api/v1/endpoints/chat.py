# backend/app/api/v1/endpoints/chat.py
from fastapi import APIRouter
from app.services.chat_service import chat_backend, ChatRequest

router = APIRouter()


@router.post("/")
def chat_endpoint(payload: ChatRequest):
    """
    Endpoint de chat para interacción con LLM.

    Args:
      payload (ChatRequest): Incluye la lista de mensajes y opcionalmente el email del usuario para logging.

    Returns:
      dict con respuesta del modelo.
    """
    return chat_backend(payload)