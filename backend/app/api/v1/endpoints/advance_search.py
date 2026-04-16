from fastapi import APIRouter
from pydantic import BaseModel

from app.services.search_category_service import SearchCategoryChunks

router = APIRouter()

search = SearchCategoryChunks()


class Request(BaseModel):
    query: str | None = None
    bloque: list[str] | None = []
    file: list[str] | None = []
    user_id: str | None = None


##############
# End-points #
##############


@router.post("/advance_search")
async def advance_search(request: Request):

    response = search.classification_pipeline_endpoint(
        query=request.query, collections=request.bloque, documents=request.file
    )

    return response
