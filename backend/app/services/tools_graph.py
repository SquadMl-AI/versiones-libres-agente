from langchain.tools import tool
from app.services.rag_service import RAGPipeline
from tenacity import retry, stop_after_attempt, wait_fixed


search = RAGPipeline()


@tool
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def retrieval_tool(query: str, user_email: str):
    """
    Tool que sirve para buscar informacion sobre preguntas que haga el usario referente que
    documentos indexados de las sentencias de la fiscalia.

    Usala para devolver la informacion completa que te de el RAG recibirás del indice un
    diccionario con la siguente estructura:
    '''json
        {
        answer: Que es la respuesta del modelo generada a partir de las fuentes,
        sources: que es una links de los chunks que uso el modelo para construir answer
        cites esa fuentes cuando vayas a dar la respuesta
        }

    Args:
    query: Lo que el Usuario pregunta
    """
    response = search.rag_pipeline(user_query=query, user_email=user_email)
    return response.model_dump()