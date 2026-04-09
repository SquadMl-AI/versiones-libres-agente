import locale
from datetime import datetime
from typing import Annotated, Literal

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from services.tools_graph import retrieval_tool
from utils.ai_services import AzureServices

openai = AzureServices.AzureOpenAI()

# Inicializa el cliente de Azure OpenAI
llm4o = openai.load_model("gpt-41")

# Se definen las tools
tools = [retrieval_tool]

# Se le bindean las tools al modelo
llm4o_with_tools = llm4o.bind_tools(tools)

# Darle al modelo el contexto de qué día es hoy
# locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')
locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")
today = datetime.today().strftime("%A, %d de %B de %Y")

# Aquí se define el prompt con las instrucciones que ayudarán al modelo
# a interactuar con el usuario y le darán contexto de las tools que puede usar
SYSTEM_PROMPT = f"""
Eres un asistente virtual especializado en ayudar a las personas en sus consultas sobre los
documentos de sentencias de la fiscalía de Colombia.

Usa `retrieval_tool` para poder dar respuesta a los usuarios cuando pregunten cosas que no
tengas en tu conocimiento base.

**SOLO** cuando recibas la respuesta de la herramienta, responde exactamente con el JSON
recibido, sin modificar nada. En otros casos responde en texto.

La fecha de hoy es: {today}

Este es el contexto de la conversación:
{{conversation}}
"""

# Definimos el template para enviarlo al modelo
template_with_tools = ChatPromptTemplate(
    [
        ("system", SYSTEM_PROMPT),
        ("placeholder", "{conversation}"),
    ]
)


async def _handle_standard_conversation(state, messages):
    """
    Maneja la conversación estándar, generando una respuesta del modelo
    y procesando tool calls.
    """
    formatted_prompt = template_with_tools.format_messages(conversation=messages)
    response_msg = await llm4o_with_tools.ainvoke(formatted_prompt)

    ai_message = AIMessage(
        content=response_msg.content,
        tool_calls=getattr(response_msg, "tool_calls", None),
    )

    return {
        **state,
        "messages": messages + [ai_message],
        "response": response_msg.content,
    }


class State(TypedDict):
    """
    Define el estado del grafo.
    """

    user_id: str
    messages: Annotated[list, add_messages]  # Acumula los mensajes correctamente.
    response: str


async def chat_agent(state: State) -> State:
    """
    Nodo principal del grafo, donde se maneja la interacción Bot-usuario.

    Aquí se genera el mensaje inicial de la conversación, el modelo decide si usa
    las tools y mantiene la conversación.
    """
    try:
        messages = state.get("messages", [])
    except KeyError as e:
        raise ValueError(f"Falta la clave en el estado: {e}") from e

    # Si no hay mensajes previos, generar el mensaje inicial directamente
    if not messages:
        initial_message = AIMessage(
            content=(
                "Hola, estoy aquí para ayudarte con las consultas que necesites. "
                "Por favor dime en qué puedo ayudarte hoy."
            )
        )
        return {
            **state,
            "messages": [initial_message],
            "response": initial_message.content,
        }

    # Extraer los últimos mensajes para la conversación
    last_messages = messages[-35:] if len(messages) > 35 else messages

    return await _handle_standard_conversation(
        state=state,
        messages=last_messages,
    )


def route_after_agent(state: State) -> Literal["chat_agent", "tool_node", "__end__"]:
    messages = state.get("messages", [])

    # Si solo hay un mensaje (el del bot inicial), termina la conversación
    # hasta que llegue uno nuevo
    if len(messages) == 1 and isinstance(messages[0], AIMessage):
        return "__end__"

    if not messages:
        return "__end__"

    last_message = messages[-1]

    if not isinstance(last_message, AIMessage):
        return "chat_agent"

    if getattr(last_message, "tool_calls", None):
        return "tool_node"

    return "__end__"


# Creando nodos
graph_builder = StateGraph(State)
graph_builder.add_node("chat_agent", chat_agent)
graph_builder.add_node("tool_node", ToolNode(tools))

# Creando el grafo
graph_builder.add_edge(START, "chat_agent")
graph_builder.add_conditional_edges("chat_agent", route_after_agent)
graph_builder.add_edge("tool_node", "chat_agent")

# Compilar el grafo
graph = graph_builder.compile()
