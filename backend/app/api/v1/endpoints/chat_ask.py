import os
import uuid
from datetime import datetime

from dotenv import find_dotenv, load_dotenv
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.rag_service_audiencias import RAGPipelineAudiencias
from app.services.rag_service_sentencias import RAGPipelineSentencias
from app.utils.ai_services import AzureServices

load_dotenv(find_dotenv())

router = APIRouter()

connection_string = os.getenv("AZURE_COSMOSDB_ENDPOINT")
db_name = os.getenv("AZURE_COSMOSDB_DATABASE_NAME")
collection = os.getenv("AZURE_COSMOSDB_COLLECTION_NAME")


cosmos = AzureServices.CosmosDB(connection_string=connection_string, db_name=db_name, collection_names=collection)

search_sentencias = RAGPipelineSentencias()
search_audiencias = RAGPipelineAudiencias()


class RequestSentencias(BaseModel):
    query: str
    user_email: str | None
    index: str | None = "index_sentencias"


class RequestAudiencias(BaseModel):
    query: str
    user_email: str | None
    index: str | None = "index_audiencias"


@router.post("/chat_ask_sentencias")
def chat_ask_sentencias(request: RequestSentencias):

    response = search_sentencias.rag_pipeline(
        user_query=request.query, user_email=request.user_email, index_name=request.index
    )

    user_message = {
        "_id": str(uuid.uuid4()),
        "user_id": request.user_email,
        "type": "human",
        "content": request.query,
        "timestamp": datetime.now(),
    }
    cosmos.insert_message(user_message, collection)

    # print("PIPELINE RAW RESPONSE:",response.model_dump())

    bot_message = {
        "_id": str(uuid.uuid4()),
        "user_id": request.user_email,
        "type": "ai",
        "query": request.query,
        "model": response.model,
        "content": response.answer,
        "sources": f"{response.sources}",
        "feed": 0,
        "timestamp": datetime.now(),
    }
    cosmos.insert_message(bot_message, collection)
    return {"message_id": bot_message["_id"], "response": response.model_dump()}


@router.post("/chat_ask_audiencias")
def chat_ask_audiencias(request: RequestAudiencias):

    response = search_audiencias.rag_pipeline(
        user_query=request.query, user_email=request.user_email, index_name=request.index
    )

    user_message = {
        "_id": str(uuid.uuid4()),
        "user_id": request.user_email,
        "type": "human",
        "content": request.query,
        "timestamp": datetime.now(),
    }
    cosmos.insert_message(user_message, collection)

    # print("PIPELINE RAW RESPONSE:",response.model_dump())

    bot_message = {
        "_id": str(uuid.uuid4()),
        "user_id": request.user_email,
        "type": "ai",
        "query": request.query,
        "model": response.model,
        "content": response.answer,
        "sources": f"{response.sources}",
        "feed": 0,
        "timestamp": datetime.now(),
    }
    cosmos.insert_message(bot_message, collection)
    return {"message_id": bot_message["_id"], "response": response.model_dump()}
