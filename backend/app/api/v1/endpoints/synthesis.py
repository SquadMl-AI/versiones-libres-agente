from fastapi import APIRouter
from pydantic import BaseModel
from app.services.synthesis_service import SynthesisCategoryChunks
from typing import List, Any

router = APIRouter()

synthesis = SynthesisCategoryChunks()


class Request(BaseModel):

    query: str
    chunks: List[dict[str, Any]]


##############
# End-points #
##############


@router.post("/synthesis_chunks")
async def advance_search(request: Request):

    response = synthesis.synthesis_pipeline_endpoint(query=request.query, chunks=request.chunks)

    return response