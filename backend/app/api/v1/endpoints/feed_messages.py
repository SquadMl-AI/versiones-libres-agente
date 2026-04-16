"""
Este modulo se encarga de gestionar los endpoints relacionados con la retroalimentación de los mensajes.
"""

# Importaciones necesarias
import os

from dotenv import find_dotenv, load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.utils.ai_services import AzureServices

load_dotenv(find_dotenv())

# Instanciamos un router
router = APIRouter()
# Usamos la configuración de Azure Cosmos DB
connection_string = os.getenv("AZURE_COSMOSDB_ENDPOINT")
db_name = os.getenv("AZURE_COSMOSDB_DATABASE_NAME")
collection = "Users"

# Instanciamos el cliente de Cosmos DB
cosmos = AzureServices.CosmosDB(connection_string=connection_string, db_name=db_name, collection_names=collection)


# Definimos el modelo para la retroalimentación de mensajes
class MessagesFeedback(BaseModel):
    message_id: str  # ID del mensaje
    feed: int  # Valor de retroalimentación


@router.put("/feed_message")
def feed_message(request: MessagesFeedback):
    """
    Endpoint para actualizar la retroalimentación de un mensaje.
    """
    filter_field = {"_id": request.message_id}
    update_field = {"feed": request.feed}

    try:
        # Actualizamos el mensaje en la base de datos
        cosmos.update_message(filter_field, update_field, collection)
        return {"message": "Campo feed actualizado con éxito"}
    except Exception as e:
        print(f"Error al actualizar feed: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar el feed del mensaje") from e
