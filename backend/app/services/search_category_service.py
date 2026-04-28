import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import openai
from bs4 import BeautifulSoup
from pydantic import BaseModel

# Ajustar path para importaciones del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.ai_services import AzureServices


# --- Modelos Pydantic ---
class QueryRequest(BaseModel):
    question: str
    index_name: str
    collections: list[str] | None = None
    documents: list[str] | None = None


class ClassificationResponse(BaseModel):
    model: str
    high_score_categorized_chunks: list[dict[str, Any]]
    low_score_reranked_chunks: list[dict[str, Any]]
    remaining_chunks: list[dict[str, Any]]


class SearchCategoryChunks:
    """
    Pipeline de filtrado y clasificación. Toma una gran cantidad de resultados de búsqueda,
    refina progresivamente y, finalmente, usa un LLM para categorizar los más prometedores,
    todo esto manteniendo la integridad de los metadatos originales.
    """

    def __init__(self):
        self.aoai_client = AzureServices.AzureOpenAI()
        self.search_client = AzureServices.AzureIASearch()

    def get_embedding(self, text: str, client: openai.AzureOpenAI) -> list[float]:
        """Genera un embedding para un texto dado."""
        embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
        return client.embeddings.create(input=[text], model=embedding_deployment).data[0].embedding

    def normalize_text(self, query: str) -> str:
        """
        Normaliza la query para mejorar la búsqueda y la generación de respuestas:
        - Pasa a minúsculas
        - Elimina tildes (pero mantiene la ñ)
        - Elimina signos de puntuación y html
        """
        soup = BeautifulSoup(query, "html.parser")
        texto = soup.get_text(separator=" ").lower()
        # Reemplaza solo las vocales acentuadas, sin tocar la ñ
        reemplazos = {
            "á": "a",
            "é": "e",
            "í": "i",
            "ó": "o",
            "ú": "u",
            "ä": "a",
            "ë": "e",
            "ï": "i",
            "ö": "o",
            "ü": "u",
            "à": "a",
            "è": "e",
            "ì": "i",
            "ò": "o",
            "ù": "u",
        }
        for acentuada, simple in reemplazos.items():
            texto = texto.replace(acentuada, simple)
        # Elimina signos de puntuación
        texto = re.sub(r"[^\w\s]", "", texto)
        texto = re.sub(r"\s+", " ", texto).strip()
        return texto

    def build_odata_filter(self, collections: list[str] | None, documents: list[str] | None) -> str | None:
        """
        Construye una cadena de filtro OData a partir de las listas de colecciones y documentos.
        """
        filter_parts = []
        if collections:
            escaped_collections = [c.replace("'", "''") for c in collections]
            filter_parts.append(f"search.in(bloque, '{','.join(escaped_collections)}', ',')")

        if documents:
            escaped_documents = [d.replace("'", "''") for d in documents]
            filter_parts.append(f"search.in(docnm, '{','.join(escaped_documents)}', ',')")

        if not filter_parts:
            return None

        filter_string = " and ".join(filter_parts)
        print(f"🔎 Filtro OData construido: {filter_string}")
        return filter_string

    # ======================================================================================
    #  BÚSQUEDA Y CLASIFICACIÓN
    # ======================================================================================
    def hybrid_search_for_classification(
        self, query: str, index_name: str, collections: list[str] | None = None, documents: list[str] | None = None
    ) -> list[dict]:
        """
        Realiza una búsqueda híbrida para obtener 300 resultados, con rerankeo semántico aplicado.
        """
        print(f"🔍 Realizando búsqueda híbrida para obtener 300 chunks para la consulta: '{query}'")

        normalized_query = self.normalize_text(query)
        odata_filter = self.build_odata_filter(collections, documents)

        retrieved_chunks = self.search_client.hybrid_search(normalized_query, index_name, 300, odata_filter)

        processed_results = []
        for result in retrieved_chunks:
            chunk_data = {
                "chunk id": result["doc_id"],
                "content": result["content"],
                "page_numbers": result.get("page_number", []),
                "folder": result.get("bloque", "N/A"),
                "document_name": result.get("docnm", "N/A"),
                "hybrid_score": result["@search.score"],
                "reranker_score": result.get("@search.reranker_score"),
                "highlights": result.get("@search.highlights", {}),
            }
            processed_results.append(chunk_data)

        print(f"✅ Búsqueda completada. Se obtuvieron {len(processed_results)} chunks.")
        return processed_results

    # ---------- Funciones auxiliares para create_highlights ----------
    @staticmethod
    def _remove_stopword_highlights(text: str, stopwords: set) -> str:
        """Quita <em> de las stopwords resaltadas, deja el resto igual."""

        def _replace(match):
            palabra = match.group(1)
            if palabra.lower() in stopwords:
                return palabra  # Sin <em>
            else:
                return match.group(0)  # Deja el <em>

        return re.sub(r"<em>(.*?)</em>", _replace, text)

    @staticmethod
    def _extract_highlighted_phrases(highlight_list: list) -> set:
        """Extrae todas las palabras/frases resaltadas que quedan."""
        found = set()
        for frase in highlight_list:
            matches = re.findall(r"<em>(.*?)</em>", frase)
            for m in matches:
                found.add(m)
        # Ordena por longitud descendente para evitar resaltados parciales
        return found

    @staticmethod
    def _highlight_phrases_in_content(content: str, phrases: set) -> str:
        """Resalta todas las frases encontradas en el texto completo."""
        if not phrases:
            return content
        # Ordenar por longitud descendente
        sorted_phrases = sorted(phrases, key=len, reverse=True)
        pattern = r"(" + "|".join(re.escape(p) for p in sorted_phrases if p) + r")"
        return re.sub(pattern, r"<em>\1</em>", content, flags=re.IGNORECASE)

    def create_highlights(self, all_chunks):
        """
        1. Limpia las etiquetas <em> SOLO de las stopwords en los highlights
        2. Extrae todas las palabras/frases resaltadas que quedan
        3. Resalta esas palabras/frases en el campo content (en todo el texto)
        """
        stopwords = {
            "el",
            "la",
            "los",
            "las",
            "un",
            "una",
            "unos",
            "unas",
            "de",
            "del",
            "al",
            "a",
            "en",
            "por",
            "para",
            "con",
            "sin",
            "y",
            "o",
            "u",
            "que",
            "como",
            "es",
            "su",
            "sus",
            "se",
            "lo",
            "le",
            "les",
            "mi",
            "mis",
            "tu",
            "tus",
            "nuestro",
            "nuestra",
            "nuestros",
            "nuestras",
        }

        for chunk in all_chunks:
            highlights = chunk.get("highlights")
            highlights_content = None
            if highlights and isinstance(highlights, dict):
                highlights_content = highlights.get("content")

            if highlights_content and isinstance(highlights_content, list) and any(highlights_content):
                cleaned_highlights = [
                    self._remove_stopword_highlights(frase, stopwords) for frase in highlights_content
                ]
                chunk["highlights"]["content"] = cleaned_highlights
                palabras_resaltadas = self._extract_highlighted_phrases(cleaned_highlights)
                chunk["content_highlighted"] = self._highlight_phrases_in_content(chunk["content"], palabras_resaltadas)
            else:
                chunk["content_highlighted"] = chunk["content"]

        return all_chunks

    # ---------- Categorización ----------
    def categorize_chunk_content(self, content: str, user_query: str) -> tuple[dict, str]:
        """
        Usa un LLM para clasificar el contenido de un chunk sin recibir sus metadatos.
        """
        system_prompt = (
            f"Eres un riguroso agente experto investigador judicial que analiza y escribe su "
            f"respuesta basándose exclusivamente en fragmentos de texto (chunks) cuya fuente son "
            f"numerosas sentencias de la ley 975 de 2005 de colombia, tu tarea es determinar el "
            f"tipo de relevancia de cada chunk de manera rigurosa respecto a la consulta inicial "
            f"del usuario: '{user_query}'. "
            "Clasifica el fragmento o chunck según los siguientes criterios:\n"
            "- **Relevante:** Si el contenido aborda literal y explicitamente todos los temas de la "
            "consulta, -especialmente- cuando se menciona la relaciòn entre personas, las víctimas "
            "y los victimarios (a quienes tambien se les llama postulados en el texto), lugares "
            "específicos relacionados con los hechos, modus operandi, armas o bienes muebles e "
            "inmuebles involucrados. Solo se pueden aceptar variaciones ortográficas o de digitaciòn "
            "muy leves (como errores de digitación y tildes). cuando se esté consultando por el "
            "nombre de alguién, debes citar la información que esté explícita y exacta, sin tomar "
            "referencias externas ni acercamientos a nombres parecidos. tiene que estar el nombre "
            "completo de quien se consulta (con nombre y apellido). Nombres parecidos o partes del "
            "nombre no se deben citar en el resultado de la consulta. lo único con lo que serás "
            "tolerante a la hora de traer referencias de nombres, es cuando les falten las tildes o "
            "con variaciones ortográficas leves. no hagas relaciones de parentezco entre las personas "
            "por sus nombres o apellidos similares, a menos que el texto diga explícitamente que "
            "existe una relación familiar entre el nombre consultado y otros. \n"
            "- **Relevancia Indeterminada:** Si el contenido toca temas que están relacionados "
            "estríctamente con la consulta pero no están explícitamente en el texto. Debe ser "
            "específico en los aspectos relacionados en la consulta aunque la conexión no sea "
            "explícita o clara (por ambigüedad o relación indirecta). debe tenenr en cuenta el "
            "contexto de las situaciones en las que se dieron los hechos y las relaciones de personas "
            "con estos contextos generales, aunque no se nombre explícitamente. no hacer conjeturas "
            "sobre similitudes superfluas, por ejemplo: nombrar casos por el hecho de pertenecer al "
            "conjuno de casos analizados. \n"
            "- **No Relevante:** Si el contenido no tiene ninguna relación con la consulta.\n"
            "Basa tu decisión únicamente en el análisis del contenido.\n"
            "Proporciona un resumen breve pero detallado y muy acorde al analisis del contenido, "
            "que describa la relación del contenido con la consulta del usuario, y justifique la "
            "clasificación.\n"
            "Devuelve la respuesta en este formato JSON exacto:\n\n"
            '{ "clasificacion": "[Relevante|Relevancia Indeterminada|No Relevante]", '
            '"resumen_llm": "[Resumen breve y justificativo]" }'
        )

        user_prompt = f"Contenido del chunk:\n{content}"

        try:
            response_format = {"type": "json_object"}
            llm_answer, model = self.aoai_client.model_response(
                user_prompt, system_prompt, response_format, model="gpt-4.1mini"
            )
            result = json.loads(llm_answer)
            return {
                "categoria": result.get("clasificacion", "Error de Formato"),
                "resumen_llm": result.get("resumen_llm", "El LLM no generó un resumen válido."),
            }, model
        except Exception as e:
            print(f"❌ Error al categorizar con el LLM: {e}")
            return {"categoria": "Error de Procesamiento", "resumen_llm": str(e)}, "unknown_model"

    # ======================================================================================
    #  4. EJECUCIÓN PRINCIPAL DEL PIPELINE
    # ======================================================================================
    def classification_pipeline_endpoint(
        self,
        query: str,
        index_name: str = "index_sentencias",
        collections: list[str] | None = None,
        documents: list[str] | None = None,
    ):
        """
        Endpoint que ejecuta el pipeline completo de búsqueda, filtrado y clasificación.
        """
        # --- Paso 1: Búsqueda Híbrida Amplia ---
        all_chunks = self.hybrid_search_for_classification(query, index_name, collections, documents)

        all_chunks = self.create_highlights(all_chunks)

        # --- Paso 2: Dividir y Filtrar los Resultados ---
        high_score_chunks = []
        low_score_reranked_chunks = []
        remaining_chunks = []

        for chunk in all_chunks:
            reranker_score = chunk.get("reranker_score")
            if reranker_score is not None:
                if reranker_score > 2.0:
                    high_score_chunks.append(chunk)
                else:
                    chunk["categoria"] = "No analizado"
                    chunk["resumen_llm"] = "No analizado por el LLM (Fuera del Top Seleccionable)"
                    low_score_reranked_chunks.append(chunk)
            else:
                chunk["categoria"] = "No analizado"
                chunk["resumen_llm"] = "No analizado por el LLM (Fuera del Top Seleccionable)"
                remaining_chunks.append(chunk)

        print(
            f"📊 División completada: {len(high_score_chunks)} de alto score, "
            f"{len(low_score_reranked_chunks)} de bajo score, "
            f"{len(remaining_chunks)} restantes."
        )

        # --- Paso 3: Categorización por LLM (solo para los de alto score, paralelo, ordenado) ---
        final_categorized_chunks = []
        model = "unknown_model"

        if high_score_chunks:
            print(f"🤖 Iniciando categorización por LLM para {len(high_score_chunks)} chunks...")

            start_time = time.time()
            indexed_chunks = [(idx, chunk) for idx, chunk in enumerate(high_score_chunks)]

            def categorize_single_chunk(index_chunk_tuple):
                idx, chunk = index_chunk_tuple
                chunk_copy = chunk.copy()
                llm_result, mod = self.categorize_chunk_content(chunk_copy["content"], query)
                chunk_copy["categoria"] = llm_result["categoria"]
                chunk_copy["resumen_llm"] = llm_result["resumen_llm"]
                return idx, chunk_copy, mod

            results_map = {}
            with ThreadPoolExecutor(max_workers=12) as executor:
                futures = {executor.submit(categorize_single_chunk, item): item[0] for item in indexed_chunks}
                for i, future in enumerate(as_completed(futures), 1):
                    idx = futures[future]
                    try:
                        index, chunk_result, mod = future.result()
                        results_map[index] = chunk_result
                        model = mod  # último modelo usado
                        print(f"    - Procesado chunk {i}/{len(high_score_chunks)}")
                    except Exception as e:
                        print(f"❌ Error procesando chunk {idx}: {e}")
                        results_map[idx] = None

            final_categorized_chunks = [
                results_map[idx] for idx in range(len(high_score_chunks)) if results_map.get(idx) is not None
            ]
            end_time = time.time()
            print(f"✅ Categorización completada. Tiempo total: {end_time - start_time:.2f} segundos.")

        # --- Paso 4: Devolver la Respuesta Estructurada ---
        return ClassificationResponse(
            model=model,
            high_score_categorized_chunks=final_categorized_chunks,
            low_score_reranked_chunks=low_score_reranked_chunks,
            remaining_chunks=remaining_chunks,
        )


if __name__ == "__main__":
    pregunta_usuario = "Qué argumentos presentó la defensa de Jorge Barney Veloza García en la apelación?"

    pipeline = SearchCategoryChunks()
    final_response = pipeline.classification_pipeline_endpoint(
        pregunta_usuario, index_name="index_sentencias", collections=[], documents=[]
    )
    print(final_response)
