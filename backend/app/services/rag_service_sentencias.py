from services.rag_service_base import BaseRAGPipeline, QueryRequest, RAGResponse, Source


class RAGPipelineSentencias(BaseRAGPipeline):
    domain_name = "SENTENCIAS"
    default_index_name = "index_sentencias"


if __name__ == "__main__":
    pregunta_usuario = "Que se comentó en el caso de mancuso"

    ragpipeline = RAGPipelineSentencias()
    final_response = ragpipeline.rag_pipeline(
        pregunta_usuario,
        index_name="index_sentencias",
        top_k=5,
        user_email="Default",
    )