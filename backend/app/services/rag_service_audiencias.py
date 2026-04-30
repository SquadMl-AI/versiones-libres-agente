from services.rag_service_base import BaseRAGPipeline


class RAGPipelineAudiencias(BaseRAGPipeline):
    domain_name = "AUDIENCIAS"
    default_index_name = "index_audiencias"


if __name__ == "__main__":
    pregunta_usuario = "Que se comentó en el caso de mancuso"

    ragpipeline = RAGPipelineAudiencias()
    final_response = ragpipeline.rag_pipeline(
        pregunta_usuario,
        index_name="index_audiencias",
        top_k=5,
        user_email="Default",
    )
