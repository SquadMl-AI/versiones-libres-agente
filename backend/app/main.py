from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
import logging

router = APIRouter()

# # --- Función reutilizable de health check ---
# async def run_health_checks():
#     checks = []
#     # PostgreSQL
#     try:
#         conn = psycopg2.connect(
#             host=os.getenv("POSTGRES_HOST"),
#             port=os.getenv("POSTGRES_PORT"),
#             dbname=os.getenv("POSTGRES_DB"),
#             user=os.getenv("POSTGRES_USER"),
#             password=os.getenv("POSTGRES_PASSWORD"),
#             connect_timeout=2
#         )
#         conn.close()
#         checks.append({"service": "PostgreSQL", "ok": True, "msg": "Conexión exitosa"})
#     except Exception as e:
#         checks.append({"service": "PostgreSQL", "ok": False, "msg": str(e)})

#     # Elasticsearch
#     try:
#         es_host = os.getenv("ELASTICSEARCH_HOST")
#         es_api_key = os.getenv("ES_API_KEY")
#         es = Elasticsearch(es_host, api_key=es_api_key, request_timeout=2)
#         info = es.info()
#         checks.append({
#             "service": "Elasticsearch", "ok": True,
#             "msg": f"Versión {info['version']['number']}"
#         })
#     except Exception as e:
#         checks.append({"service": "Elasticsearch", "ok": False, "msg": str(e)})

#     # Azure OpenAI (gpt-4.1-mini)
#     try:
#         endpoint = os.getenv("GPT41MINI_ENDPOINT")
#         api_key = os.getenv("GPT41MINI_API_KEY")
#         headers = {"api-key": api_key, "Content-Type": "application/json"}
#         data = {"messages": [{"role": "user", "content": "ping"}], "max_tokens": 5}
#         async with httpx.AsyncClient(timeout=3) as client:
#             r = await client.post(endpoint, headers=headers, json=data)
#             if r.status_code == 200:
#                 checks.append({"service": "Azure OpenAI (gpt-4.1-mini)", "ok": True, "msg": "Respuesta OK"})
#             else:
#                 checks.append({
#                     "service": "Azure OpenAI (gpt-4.1-mini)", "ok": False,
#                     "msg": f"Status {r.status_code}"
#                 })
#     except Exception as e:
#         checks.append({"service": "Azure OpenAI (gpt-4.1-mini)", "ok": False, "msg": str(e)})

#     # Embedding endpoint (EMBEDDING_ENDPOINT, EMBEDDING_API_KEY)
#     try:
#         emb_endpoint = os.getenv("EMBEDDING_ENDPOINT")
#         emb_api_key = os.getenv("EMBEDDING_API_KEY")
#         headers = {"api-key": emb_api_key, "Content-Type": "application/json"}
#         data = {"input": ["ping embedding"], "model": "text-embedding-3-large"}
#         async with httpx.AsyncClient(timeout=3) as client:
#             r = await client.post(emb_endpoint, headers=headers, json=data)
#             if r.status_code == 200 and "data" in r.json():
#                 checks.append({"service": "Azure OpenAI Embedding", "ok": True, "msg": "Respuesta OK"})
#             else:
#                 checks.append({
#                     "service": "Azure OpenAI Embedding", "ok": False,
#                     "msg": f"Status {r.status_code}"
#                 })
#     except Exception as e:
#         checks.append({"service": "Azure OpenAI Embedding", "ok": False, "msg": str(e)})

#     return checks

# Endpoint reutilizando la función
# @router.get("/health", tags=["Health"])
# async def health_check():
#     checks = await run_health_checks()
#     return {"checks": checks}

# from app.utils.update_kb_catalog import print_kb_id_catalog_status
# from app.utils_helpers import get_embedding
# from app.model_handlers import initialize_client, invoke_model

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Memorias de Justicia y Paz API")


# @app.on_event("startup")
# async def startup_event():
#     logger.info("Iniciando la aplicación y verificando servicios de modelos...")

#     # Checklist de salud de servicios
#     checks = await run_health_checks()
#     GREEN = '\033[0;32m'
#     RED = '\033[0;31m'
#     NC = '\033[0m'
#     CHECK = '✔'
#     FAIL = '✖'
#     print("\n================= Estado de servicios (checklist) =================")
#     maxlen = max(len(c['service']) for c in checks)
#     all_ok = True
#     for c in checks:
#         name = c['service'].ljust(maxlen)
#         if c["ok"]:
#             print(f"{GREEN}{CHECK} {name}{NC} - {c['msg']}")
#         else:
#             print(f"{RED}{FAIL} {name}{NC} - {c['msg']}")
#             all_ok = False
#     print("=" * 62)
#     if all_ok:
#         print(f"{GREEN}✔ Todos los servicios están OK{NC}\n")
#     else:
#         print(f"{RED}✖ Hay servicios con problemas, revisa el detalle arriba{NC}\n")

#     # Imprimir el estado del catálogo
#     print_kb_id_catalog_status()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Puedes restringir esto a tus dominios frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Al iniciar el backend, imprime el estado del catálogo kb_id_to_name.json
# print_kb_id_catalog_status() # Movido a startup_event

app.include_router(api_router, prefix="/api/v1")
app.include_router(router)