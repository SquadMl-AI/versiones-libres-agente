from pydantic import BaseModel
from typing import List, Optional
from app.model_handlers import initialize_client, invoke_model
from app.services.logging_service import log_interaction


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    user_email: Optional[str] = None


def chat_backend(payload: ChatRequest):
    """
    Handles the chat logic, sends messages to the LLM, and logs the interaction.
    """
    model_provider = "Azure OpenAI (o3-mini)"
    client, model, base_url = initialize_client(model_provider)

    if not client:
        return {"role": "assistant", "content": f"Error: No se pudo inicializar el modelo {model_provider}."}

    # Basic system prompt
    system_prompt = "Eres un asistente de IA útil. Responde las preguntas del usuario de forma concisa."

    # The user's prompt is the last message in the list
    user_prompt = payload.messages[-1].content if payload.messages else ""

    # For more advanced scenarios, you might pass the whole message history
    # For this implementation, we'll keep it simple

    full_response = invoke_model(
        client,
        model,
        base_url,
        system_prompt,
        user_prompt,
        model_provider,
        max_tokens=1500,
        stream=False
    )

    assistant_response = {"role": "assistant", "content": full_response}

    if payload.user_email:
        # Log the interaction
        log_interaction(
            user_email=payload.user_email,
            query=user_prompt,
            synthesis=assistant_response.get("content")
        )

    return assistant_response