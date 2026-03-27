# backend/app/api/v1/endpoints/synthesize.py
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.services.search_service import synthesize_final
from app.schemas.search import SynthesisRequest, SynthesisResponse

router = APIRouter()


@router.post("/", response_model=SynthesisResponse)
def synthesis_endpoint(payload: SynthesisRequest):
    """
    Genera una síntesis automática de los resultados seleccionados usando LLM.
    Args:
      payload (SynthesisRequest): Incluye query, modelo, resultados y categorías de relevancia.
    Returns:
      SynthesisResponse: Texto de síntesis generado.
    """
    return synthesize_final(payload)


@router.post("/stream", response_class=StreamingResponse, include_in_schema=True)
def synthesis_stream_endpoint(payload: SynthesisRequest, request: Request):
    """
    Genera una síntesis automática en modo streaming (útil para respuestas largas).
    Args:
      payload (SynthesisRequest): Incluye query, modelo, resultados y categorías de relevancia.
    Returns:
      StreamingResponse: Texto de síntesis generado en partes.
    """
    from app.services.search_service import synthesize_final

    def stream_generator():
        result = synthesize_final(payload, stream=True)
        if hasattr(result, '__iter__') and not isinstance(result, str):
            for chunk in result:
                # print("[STREAM CHUNK]", chunk)
                if hasattr(chunk, 'choices') and chunk.choices and hasattr(chunk.choices[0], 'delta'):
                    content = getattr(chunk.choices[0].delta, 'content', None)
                    if content:
                        yield content
                elif isinstance(chunk, str):
                    yield chunk
        else:
            yield str(result)
    return StreamingResponse(stream_generator(), media_type="text/plain")