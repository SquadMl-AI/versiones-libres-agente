# Generar un path para el archivo
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importaciones
from typing import Annotated, Literal
from typing_extensions import TypedDict
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from datetime import datetime
import locale

from services.tools_graph import retrieval_tool
from utils.ai_services import AzureServices


openai = AzureServices.AzureOpenAI()

# Inicializa el cliente de Azure OpenAI
llm4o = openai.load_model("gpt-41")
# Se definen las tools
tools = [retrieval_tool]
# Se le bindean las las tools a el modelo
llm4o_with_tools = llm4o.bind_tools(tools)
# Darle al modelo el contexto de que dia es hoy
# locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')
locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
today = datetime.today().strftime("%A, %d de %B de %Y")


# Aqui se define el prompt con las instrucciones que ayudaran al modelo a interactura con el usuario
# y le daran contexto de las tools que puede usar
SYSTEM_PROMPT = (
    """
    Eres un asistente virtual especializado en ayudar a las personas en sus cosultas sobre los
    docuemntos de sentencias de la fiscalia de Colombia.

    Usa ´retrieval_tool´ para poder dar respuesta los usuarios cuando pregunten cosas que no
    tengas en tu conocimiento base.
    **SOLO** Cuando recibas la respuesta de la herramienta, responde exactamente con el JSON
    recibido, sin modificar nada. en otros casos responde en texto.

    este es el contexto de la conversación:
    {conversation}
    """
)


# Definimos el template para enviarlo al modelo
template_with_tools = ChatPromptTemplate([
        ("system", SYSTEM_PROMPT),
        ("placeholder", "{conversation}")
    ])

# ###########################
# ## Funciones auxiliares  ##
# ###########################
# def find_last_user_message(last_messages: List[Any], n: int = 3) -> Optional[Any]:
#     """
#     Busca el último mensaje enviado por el usuario en la conversación.
#     """
#     user_messages= [m for m in reversed(last_messages) if isinstance(m, HumanMessage)]
#     user_messages = list(reversed(user_messages[:n]))
#     msgs_text= "\n".join(m.content for m in user_messages)
#     return msgs_text


async def _handle_standard_conversation(state, messages, last_messages):
    """"Maneja la conversación estándar, generando una respuesta del modelo y procesando tool calls."""
    formatted_prompt = template_with_tools.format_messages(conversation=messages)
    response_msg = await llm4o_with_tools.ainvoke(formatted_prompt)
    ai_message = AIMessage(
        content=response_msg.content,
        tool_calls=getattr(response_msg, "tool_calls", None)
    )

    return {
        **state,
        "messages": messages + [ai_message],
        "response": response_msg.content
    }


class State(TypedDict):
    """
    Define el estado del grafo.
    """
    user_id: str
    messages: Annotated[list, add_messages]  # Asegura que los mensajes se acumulen correctamente.
    response: str


async def chat_agent(state: State) -> State:
    """
    Este es el nodo principal del grafo, donde se maneja la interacción del Bot-usuario.

    Aqui se genera el mensaje inicial de la conversación, el modelo decide si usa las tools
    y mantiene la conversación.
    Detecta la disposición del usuario, ofrece opciones de negociación y redirige tras tres rechazos.
    """
    # Toma las variables del estado.
    try:
        messages = state.get("messages", [])
    except KeyError as e:
        raise ValueError(f"Falta la clave en el estado: {e}")

    last_message = messages[-1] if messages else messages
    # Si no hay mensajes previos, generar el mensaje inicial directamente
    if not messages:  # or isinstance(last_message, AIMessage):
        return (
            " Hola estoy aqui para ayudarte con las consultas que necesites, "
            "por favor dime en que puedo ayudarte hoy."
        )

    # Extraer los últimos mensajes del usuario para la conversación
    last_messages = messages[-35:] if len(messages) > 35 else messages
    last_user_message = last_messages[-1] if last_messages else None

    return await _handle_standard_conversation(
            state=state, messages=last_messages, last_messages=last_user_message)


def route_after_agent(state: State) -> Literal["chat_agent", "tool_node", "__end__"]:
    messages = state.get("messages", [])

    # Si solo hay un mensaje (el del bot inicial), termina la conversación hasta que llegue uno nuevo
    if len(messages) == 1 and isinstance(messages[0], AIMessage):
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

# compilar el grafo
graph = graph_builder.compile()