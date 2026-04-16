from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter, HTTPException
from app.utils.ai_services import AzureServices
from datetime import datetime
import os
import uuid
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

router_interaction= APIRouter()
router_graph= APIRouter()
router_synthe= APIRouter()
router_stats_synthe= APIRouter()

connection_string= os.getenv("AZURE_COSMOSDB_ENDPOINT")
db_name=os.getenv("AZURE_COSMOSDB_DATABASE_NAME")
collection= "Feedbacks"

cosmos = AzureServices.CosmosDB(connection_string=connection_string, db_name= db_name, collection_names= collection)

class Request(BaseModel):
    user_email: Optional[str]
    query: Optional[str]
    model: Optional[str]
    results: Optional[list]
    stars_graph: Optional[int]
    feed_graph: Optional[str]
    stars_synthe: Optional[int]
    feed_synthe: Optional[str]
    synthesis: Optional[str]

@router_interaction.post("/feedbacks")
def feed_back(request: Request):
    feedback_id = str(uuid.uuid4())
    feed = {
        "_id": feedback_id,
        "user_email": request.user_email,
        "query": request.query,
        "model":request.model,
        "results": request.results,
        "stars_graph": request.stars_graph,
        "feed_graph": request.feed_graph,
        "stars_synthe":request.stars_synthe,
        "feed_synthe": request.feed_synthe,
        "synthesis": request.synthesis,
    }
    try:
        cosmos.insert_message(data=feed, collection_name=collection)
    except Exception as e:
        # Puedes imprimir el error o loguearlo según tu necesidad
        print(f"Error al insertar en CosmosDB: {e}")
        raise HTTPException(status_code=500, detail="Error al guardar el feedback en la base de datos")

    return {"message": "Feedback guardado con éxito", "feedback_id": feedback_id}


##### Modificar variables de grafo #####
class UpdateGraphRequest(BaseModel):
    feedback_id: str
    stars_graph: int
    feed_graph: str

@router_graph.put("/feedbacks/graph")
def update_graph_feedback(update: UpdateGraphRequest):
    filter_query = {"_id": update.feedback_id}
    update_fields = {
        "stars_graph": update.stars_graph,
        "feed_graph": update.feed_graph
    }
    try:
        cosmos.update_message(filter_query, update_fields, collection)
        return {"message": "Campos stars_graph y feed_graph actualizados con éxito"}
    except Exception as e:
        print(f"Error al actualizar feedback: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar el feedbackde grafo")

##### Modificar variables de synthesis #####
class UpdateSyntheRequest(BaseModel):
    feedback_id: str
    synthesis: str

@router_synthe.put("/feedbacks/synthe")
def update_synthe_feedback(update: UpdateSyntheRequest):
    filter_query = {"_id": update.feedback_id}
    update_fields = {
        "synthesis": update.synthesis
    }
    try:
        cosmos.update_message(filter_query, update_fields, collection)
        return {"message": "Campo synthesis actualizado con éxito"}
    except Exception as e:
        print(f"Error al actualizar feedback: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar el feedback de la sintesis")


## Modificar las estrellas y feedback  de sistesis ##########

class UpdateStatsSyntheRequest(BaseModel):
    feedback_id: str
    stars_synthe: int
    feed_synthe: str

@router_stats_synthe.put("/feedbacks/stat_synthe")
def update_synthe_feedback(update: UpdateStatsSyntheRequest):
    filter_query = {"_id": update.feedback_id}
    update_fields = {
        "stars_synthe": update.stars_synthe,
        "feed_synthe": update.feed_synthe,
    }
    try:
        cosmos.update_message(filter_query, update_fields, collection)
        return {"message": "Campos stars_synthe, feed_synthe y synthesis actualizados con éxito"}
    except Exception as e:
        print(f"Error al actualizar feedback: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar el feedback")
