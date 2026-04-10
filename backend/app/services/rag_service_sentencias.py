import ast
import json
import os
import re
import sys
import unicodedata

from bs4 import BeautifulSoup
from pydantic import BaseModel

# Ajustar path para importaciones del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.ai_services import AzureServices

# =================================================================================================
#                                                           PIPELINE DEL SERVICIO RAG PARA SENTENCIAS
# =================================================================================================

db = os.getenv("AZURE_COSMOSDB_DATABASE_NAME")
collection = os.getenv("AZURE_COSMOSDB_COLLECTION_NAME")
connection_string = os.getenv("AZURE_COSMOSDB_ENDPOINT")
cosmos = AzureServices.CosmosDB(
    connection_string=connection_string,
    db_name=db,
    collection_names=collection,  # collection_names="Graphs_Users"
)


# Modelos Pydantic para la validación de datos del request y response
class QueryRequest(BaseModel):
    question: str
    index_name: str


class Source(BaseModel):
    id: str  # "[fuente 1]"
    document_name: str
    content: str
    page_number: list[int]  # Lista de números de página donde se encuentra el contenido
    bloque: str | None = None  # Bloque de información, si aplica
    highlights: dict | None = None  # Lista de fragmentos destacados, si aplica


class RAGResponse(BaseModel):
    model: str
    answer: str
    sources: list[Source]


class RAGPipelineSentencias:
    """
    Clase que implementa un pipeline de Recuperación de Información y Generación de Respuestas (RAG)
    utilizando Azure AI Search y Azure OpenAI.
    """

    def __init__(self):
        self.aoai_client = AzureServices.AzureOpenAI()
        self.search_client = AzureServices.AzureIASearch()
        self.cosmos = AzureServices.CosmosDB(
            connection_string=connection_string, db_name=db, collection_names=collection
        )

    def normalize_text(self, query: str) -> str:
        """
        Normaliza la query del usuario para mejorar la búsqueda y la generación de respuestas.
        (lowercase, sin tildes, sin signos, sin html).
        """
        soup = BeautifulSoup(query, "html.parser")
        texto = soup.get_text(separator=" ").lower()
        texto = unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("utf-8")
        texto = re.sub(r"[^\w\s]", "", texto)
        texto = re.sub(r"\s+", " ", texto).strip()
        return texto

    # ======================================================================================
    #  4. GENERACIÓN DE RESPUESTA CON CITAS (LÓGICA PRINCIPAL)
    # ======================================================================================

    def generate_cited_answer(self, query: str, history: list, retrieved_chunks: list[dict]) -> RAGResponse:
        """
        Genera una respuesta con citas incrustadas y una lista de fuentes estructuradas.
        """
        if not retrieved_chunks:
            return RAGResponse(
                answer=(
                    "Lo siento, no pude encontrar información relevante en los documentos para responder a tu pregunta."
                ),
                sources=[],
            )

        thresholds = [2, 1.5, 1]
        top_retrieved_chunks = []

        for threshold in thresholds:
            top_retrieved_chunks = [
                content for content in retrieved_chunks if content.get("@search.reranker_score", 0) >= threshold
            ]
            if top_retrieved_chunks:
                print(f"✅ Se encontraron {len(top_retrieved_chunks)} resultados con score >= {threshold}")
                break
            else:
                print(f"🔎 No se encontraron resultados con umbral semantic score >= {threshold}... (Bajandolo...)")

        if not top_retrieved_chunks:
            print("⚠️ No se encontraron resultados relevantes con ningún umbral.")
            top_retrieved_chunks = []

        print(f"chunks completo -> {len(retrieved_chunks)}")
        print(f"chunks filtrados -> {len(top_retrieved_chunks)}")

        # 1. Crear el contexto y el mapa de fuentes para el prompt
        context_for_prompt = ""
        sources_map = {}
        for i, chunk in enumerate(top_retrieved_chunks, 1):
            source_id = f"[fuente {i}]"
            context_for_prompt += f"{source_id}\n"
            context_for_prompt += f"Contenido: {chunk['content']}\n\n---\n\n"

            # Guardar la información completa de la fuente
            sources_map[source_id] = Source(
                id=source_id,
                document_name=chunk.get("docnm", ""),
                content=chunk.get("content", ""),
                page_number=chunk.get("page_number", []),
                bloque=chunk.get("bloque"),
                highlights=chunk.get("@search.highlights", {}),
            )

        # 2. Diseñar el prompt de sistema para forzar las citas
        system_prompt = f"""
        Eres un asistente inteligente. Genera un texto extenso del contenido de la base de
        conocimientos para responder a la pregunta. Si hay suficiente información relevante en la
        base de conocimientos, proporcione una respuesta extensa y completa. Enumere explícitamente
        los datos relevantes de la base de conocimientos que respaldan su respuesta. Si todo el
        contenido de la base de conocimientos es irrelevante para la pregunta, responde solo con:
        «Lo siento, no pude responder a tu pregunta. Por favor, intenta formularla de nuevo».
        Las respuestas deben tener en cuenta el contexto proporcionado por el historial del chat.

        ### REGLAS DE CITACIÓN ESTRICTAS:

        1. **Citas:** Al final de cada oración o párrafo que construyas usando información de una
           fuente, DEBES citar la fuente usando su identificador, por ejemplo: `[fuente 1]`.
        2. **Citas Múltiples:** Si combinas información de múltiples fuentes en una misma oración,
           cita todas las fuentes relevantes, por ejemplo: `[fuente 1][fuente 3]`.
        3. **Formato Obligatorio:** El único formato de cita permitido es `[fuente N]`, donde N es
           el número de la fuente. Debe ser en minúsculas y con un solo espacio entre "fuente" y
           el número.
        4. **Ejemplos INCORRECTOS y Prohibidos:** No uses mayúsculas (`[Fuente 1]`), plurales
           (`[fuentes 2]`), ni agrupes citas (`[fuente 1 y 3]`). Cita cada fuente de forma
           individual.

        ### REGLAS DE CONTENIDO Y PRECISIÓN:

        1. **Advertencia sobre Cifras:** Si la pregunta del usuario solicita cifras exactas,
           conteos, porcentajes o listados completos (por ejemplo: "¿Cuántos casos hay?",
           "Dame todos los nombres", "¿Cuál es el total de...?", etc.), DEBES advertir al usuario
           que la respuesta se basa exclusivamente en los fragmentos recuperados y no representa
           necesariamente la totalidad de la información existente. Ejemplo de advertencia:
           "La información presentada corresponde únicamente a los fragmentos recuperados, por lo
           que no debe tomarse como una cifra absoluta ni exhaustiva."
        2. **No Inventar:** NUNCA inventes información. Si no encuentras información suficiente
           para responder la pregunta, responde únicamente: «Lo siento, no pude responder a tu
           pregunta. Por favor, intenta formularla de nuevo o realiza una consulta diferente.»

        ---
        AQUÍ ESTÁN LAS FUENTES DE CONOCIMIENTO DISPONIBLES:
        ---
        {context_for_prompt}
        ---
        """

        print(system_prompt)

        # 3. Llamar al modelo de lenguaje
        print("🤖 Generando respuesta con citas...")
        llm_answer, model = self.aoai_client.model_response_with_history(
            query=query, system_prompt=system_prompt, history_msg=history
        )

        # 4. Identificar las fuentes que SÍ fueron usadas en la respuesta
        super_flexible_regex = r"\[\s*(?:fuente|fuentes|cita|ref)\.?\s+(\d+)\s*\]"
        cited_numbers = re.findall(super_flexible_regex, llm_answer, re.IGNORECASE)

        unique_numbers = sorted(list(set(cited_numbers)), key=int)
        unique_cited_ids = [f"[fuente {num}]" for num in unique_numbers]

        print(f"✅ IDs de fuentes extraídos y normalizados: {unique_cited_ids}")

        final_sources = [sources_map[source_id] for source_id in unique_cited_ids if source_id in sources_map]

        return RAGResponse(model=model, answer=llm_answer, sources=final_sources)

    # ======================================================================================
    #  PIPELINE PRINCIPAL
    # ======================================================================================

    def rag_pipeline(self, user_query: str, user_email: str, index_name: str = "index_sentencias", top_k: int = 50):
        """
        Pipeline completo de RAG que toma una consulta y devuelve una respuesta contextualizada.

        Args:
            user_query (str): La pregunta del usuario.
            user_email (str): Correo del usuario para obtener historial.
            index_name (str): Nombre del índice de búsqueda.
            top_k (int): Número de fragmentos a recuperar.
        """
        print(
            "\n############################## RECUPERACIÓN DE FRAGMENTOS RELEVANTES "
            "DESDE LA BASE DE CONOCIMIENTOS DE SENTENCIAS ################################\n"
        )

        # Paso 1: Normalizar la consulta del usuario
        normalized_query = self.normalize_text(user_query)

        # Paso 2: Realizar la búsqueda híbrida para obtener contexto
        retrieved_chunks = self.search_client.hybrid_search(normalized_query, index_name, top_k)

        context = self.cosmos.get_messages_by_user_and_time(user_email, collection)
        history = context[-15:] if context else []

        answers = []
        for m in history:
            if m.get("type") == "ai":
                content = m.get("content")
                if isinstance(content, str):
                    try:
                        content = json.loads(content)
                    except Exception:
                        try:
                            content = ast.literal_eval(content)
                        except Exception:
                            content = {}
                answer = content.get("answer") if isinstance(content, dict) else None
                if answer:
                    answers.append({"role": "assistant", "content": answer})
            elif m.get("type") == "human":
                answers.append({"role": "user", "content": m["content"]})

        final_response = self.generate_cited_answer(
            query=user_query, history=answers, retrieved_chunks=retrieved_chunks
        )
        return final_response


if __name__ == "__main__":
    # pregunta_usuario = "Qué argumentos presentó la defensa de Jorge Barney Veloza García en la apelación?"
    pregunta_usuario = "Que se comentó en el caso de mancuso"
    # pregunta_usuario = "¿Qué se determinó sobre la participación de la guerrilla
    # del M-19 en los eventos de la masacre de El Salado?"

    ragpipeline = RAGPipelineSentencias()
    final_response = ragpipeline.rag_pipeline(
        pregunta_usuario, index_name="index_sentencias", top_k=5, user_email="Default"
    )
