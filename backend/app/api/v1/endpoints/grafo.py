# from fastapi import FastAPI, HTTPException, APIRouter
# from pydantic import BaseModel
# import os
# import uvicorn
# from app.services.graph import graph
# from langchain_core.messages import HumanMessage
# from typing import Dict, Any, Optional
# from app.utils.ai_services import AzureServices
# from app.utils.messages_serialize import serialize_message, message_signature, deserialize_message
# import json
# from fastapi.responses import JSONResponse

# router = APIRouter()


# # # Configuración de MongoDB
# db= os.getenv("AZURE_COSMOSDB_DATABASE_NAME")
# collection= os.getenv("AZURE_COSMOSDB_COLLECTION_NAME")
# connection_string= os.getenv("AZURE_COSMOSDB_ENDPOINT")
# # cosmos = AzureServices.CosmosDB(connection_string=connection_string, db_name=db, collection_names="Graphs_Users")

# # Modelo para recibir los datosclass
# class RequestGrafoChat(BaseModel):
#     query: Optional[str] = None
#     user_id: Optional[str] = None

# ##############
# # End-points #
# ##############

# # Endpoint para procesar el mensaje usando el grafo conversacional
# @router.post("/graph/messages")
# async def endpoint_grafo_message(request: RequestGrafoChat):
#     """
#     Endpoint para procesar el mensaje usando el grafo conversacional.
#     """
#     try:
#         messages = cosmos.get_messages_by_user(request.user_id, "Graphs_Users")
#         if not messages:
#             messages = []
#         else:
#             messages = [deserialize_message(m) for m in messages]

#         existing_messages = messages.copy()
#         # print(f"Existng_message: {existing_messages}")

#         # Agregar el query como mensaje de usuario solo si ya hay historial previo
#         if request.query:
#             messages.append(HumanMessage(content=request.query))
#
#         # Construir estado inicial
#         state = {
#             "user_id":request.user_id,
#             "messages": messages,
#         }
#         # Historial actual
#         # print(f"mensajes: {existing_messages}")

#         # Ejecutar grafo
#         final_state = await graph.ainvoke(state)
#         final_messages = final_state["messages"]
#         previus_msg= final_messages[-2]
#         last_msg = final_messages[-1]

#         print(previus_msg)
#         if isinstance(previus_msg, dict) and previus_msg.get("name"):
#             tool_message= serialize_message(msg=previus_msg,user_id=request.user_id)
#             try:
#                 tool_content= tool_message.get("content")
#                 content_json= json.loads(tool_content)
#                 tool_message["content"]= content_json
#                 last_msg= tool_message
#             except Exception:
#                 # Si por alguna razón falla, regresa como antes
#                 pass

#         # print(f"\n Final_messages{final_messages}")
#         # Guardar solo los nuevos mensajes
#         existing_set = {message_signature(m) for m in existing_messages}

#         new_messages = [m for m in final_messages if message_signature(m) not in existing_set]
#
#         for m in new_messages:
#             cosmos.insert_message(serialize_message(m, request.user_id), "Graphs_Users")

#         response_data = {
#             "response": serialize_message(last_msg, request.user_id),}
#

#         return response_data
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
