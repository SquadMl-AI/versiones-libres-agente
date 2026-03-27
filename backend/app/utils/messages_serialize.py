from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage


# Definimos las funciones para manejar los mensajes
def serialize_message(msg, user_id):
    return {
        "user_id": user_id,
        "type": msg.type,
        "content": msg.content,
        "tool_calls": getattr(msg, "tool_calls", []),
        "tool_call_id": getattr(msg, "tool_call_id", None),
        "timestamp": datetime.now().isoformat()
    }


def message_signature(m):
    serialized = serialize_message(m, user_id=None)
    return (
        serialized.get("content"),
        serialized.get("tool_call_id"),
        tuple(
            (tc.get("id"), tc.get("name"))
            for tc in serialized.get("tool_calls", [])
        )  # Solo presente en mensajes tipo 'ai' con tool_calls
    )


def deserialize_message(doc):
    if doc["type"] == "human":
        return HumanMessage(content=doc["content"])
    elif doc["type"] == "ai":
        tool_calls = doc.get("tool_calls") or []
        return AIMessage(content=doc["content"], tool_calls=tool_calls)
    elif doc["type"] == "system":
        return SystemMessage(content=doc["content"])
    elif doc["type"] == "tool":
        return ToolMessage(content=doc["content"], tool_call_id=doc.get("tool_call_id"))
    else:
        raise ValueError(f"Tipo de mensaje no soportado: {doc['type']}")