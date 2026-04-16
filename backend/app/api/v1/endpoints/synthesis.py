from fastapi import APIRouter
from pydantic import BaseModel
import os
import uvicorn
from app.services.synthesis_service import  SynthesisCategoryChunks
from typing import Optional, List, Any
from app.utils.ai_services import AzureServices

import json
from fastapi.responses import JSONResponse

router = APIRouter()

synthesis= SynthesisCategoryChunks()

class Request(BaseModel):

    query: str
    chunks: List[dict[str, Any]]



##############
# End-points #
##############

@router.post("/synthesis_chunks")
async def advance_search(request: Request):

    response= synthesis.synthesis_pipeline_endpoint(query=request.query, chunks=request.chunks)

    return response