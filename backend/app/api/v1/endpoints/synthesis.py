from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.synthesis_service import SynthesisCategoryChunks

router = APIRouter()

synthesis= SynthesisCategoryChunks()

class Request(BaseModel):

    query: str
    chunks: list[dict[str, Any]]



##############
# End-points #
##############

@router.post("/synthesis_chunks")
async def advance_search(request: Request):

    response= synthesis.synthesis_pipeline_endpoint(query=request.query, chunks=request.chunks)

    return response
