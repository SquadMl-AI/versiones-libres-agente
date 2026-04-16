from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
import os
import uvicorn
from app.services.search_category_service import SearchCategoryChunks
from langchain_core.messages import HumanMessage
from typing import Optional, List
from app.utils.ai_services import AzureServices

import json
from fastapi.responses import JSONResponse

router = APIRouter()

search= SearchCategoryChunks()

class Request(BaseModel):
    query: Optional[str] = None
    bloque: Optional[List[str]] = []  
    file: Optional[List[str]] = []    
    user_id: Optional[str] = None


##############
# End-points #
##############

@router.post("/advance_search")
async def advance_search(request: Request):

    response= search.classification_pipeline_endpoint(query=request.query,collections=request.bloque, documents=request.file)

    return response