from fastapi import HTTPException, APIRouter
from app.utils.ai_services import AzureServices
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

router = APIRouter()

connection_string = os.getenv("AZURE_COSMOSDB_ENDPOINT")
db_name = os.getenv("AZURE_COSMOSDB_DATABASE_NAME")
collection = os.getenv("AZURE_COSMOSDB_COLLECTION_NAME")


cosmos = AzureServices.CosmosDB(connection_string=connection_string, db_name=db_name, collection_names=collection)


@router.get("/history/{user_email}")
def get_history(user_email: str):
    try:
        messages = cosmos.get_messages_by_user(user_email, "Graphs_Users")
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
