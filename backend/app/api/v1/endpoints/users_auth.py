import os

from dotenv import find_dotenv, load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.utils.ai_services import AzureServices

load_dotenv(find_dotenv())

router = APIRouter()

connection_string = os.getenv("AZURE_COSMOSDB_ENDPOINT")
db_name = os.getenv("AZURE_COSMOSDB_DATABASE_NAME")
collection = "Users_Auth"
docs = ["audiencias_usuarios", "sentencias_usuarios"]


cosmos = AzureServices.CosmosDB(connection_string=connection_string, db_name=db_name, collection_names=collection)


class UserAuth(BaseModel):
    e_mail: str


@router.post("/users_auth")
def get_user_auth(query: UserAuth):
    try:
        users = cosmos.get_users_lists(collection_name=collection, doc_ids=docs)
        access = set()
        correo_encontrado = None
        for user in users:
            if user["CORREO"].lower() == query.e_mail.lower():
                access.add(user["MODULO"])
                correo_encontrado = user["CORREO"]
        if access:
            return {"correo": correo_encontrado, "access": list(access)}
        else:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
