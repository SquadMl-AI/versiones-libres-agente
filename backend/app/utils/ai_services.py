# --------- Importar Azure Search SDK -----------------------------------------------------------------
import hashlib
import logging

# --------- Importar dependencias adicionales ----------------------------------------------------------
import os
from datetime import UTC, datetime, timedelta

import fitz
import numpy as np
import openai
import pandas as pd

# --------- Importar Azure Document Intelligence SDK --------------------------------------------------
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceNotFoundError
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import SearchField, SearchIndex, SemanticSearch
from azure.search.documents.models import (
    QueryType,
    VectorizedQuery,
)

# --------- Importar Azure Blob Storage SDK -----------------------------------------------------------
from azure.storage.blob import BlobServiceClient
from dotenv import find_dotenv, load_dotenv

# --------- Importar Azure OpenAI SDK -----------------------------------------------------------------
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

load_dotenv(find_dotenv())


class AzureServices:
    """Clase base para servicios de Azure.
    Esta clase proporciona una interfaz común para interactuar con servicios de Azure."""

    class AzureBlobStorage:
        """
        Clase para gestionar el almacenamiento de archivos en Azure Blob Storage.
        Permite guardar imágenes, PDFs y archivos de audio en una estructura organizada.
        """

        def __init__(self):
            """
            Inicializa el cliente de Azure Blob Storage con la configuración del sistema.
            """
            self.connection_string = os.getenv("AZURE_BLOB_STORAGE_CONNECTION_STRING")
            self.container_name = os.getenv("AZURE_BLOB_STORAGE_CONTAINER_NAME")

        def _get_blob_service_client(self) -> BlobServiceClient:
            """
            Obtiene un cliente de servicio para Azure Blob Storage.

            :return: Cliente del servicio de Blob Storage.
            """
            return BlobServiceClient.from_connection_string(self.connection_string)

        def download_file(self, blob_path: str) -> bytes | None:
            """
            Descarga un archivo específico del blob storage.

            :param blob_path: Ruta completa del blob a descargar.
            :return: Bytes del archivo descargado.
            """
            try:
                blob_service_client = self._get_blob_service_client()
                container_client = blob_service_client.get_container_client(self.container_name)
                blob_client = container_client.get_blob_client(blob_path)

                download_stream = blob_client.download_blob()
                file_bytes = download_stream.readall()
                print(f"Descargando archivo: {blob_path}")

                print(f"Archivo descargado exitosamente: {blob_path}")
                return file_bytes

            except ResourceNotFoundError:
                logging.error(f"El archivo {blob_path} no existe en el contenedor {self.container_name}")
                return None
            except Exception as e:
                logging.exception(f"Error al descargar archivo en Blob Storage: {str(e)}")
                return None

        def list_blobs(self, prefix: str = "", suffix: str = "pdf") -> list:
            """
            Lista los blobs en el contenedor de Azure Blob Storage dentro de un prefijo ('carpeta')
            y con un sufijo opcional.

            :param prefix: Prefijo (ruta o 'carpeta') para filtrar los blobs.
            :param suffix: Sufijo para filtrar los blobs.
            :return: Lista de nombres de blobs que coinciden con el prefijo y sufijo.
            """
            try:
                blob_service_client = self._get_blob_service_client()
                container_client = blob_service_client.get_container_client(self.container_name)
                blobs = container_client.list_blobs(name_starts_with=prefix)
                return [blob.name for blob in blobs if blob.name.endswith(suffix)]
            except Exception as e:
                logging.error(f"Error al listar blobs: {str(e)}")
                return []

        def get_pdf_page_count(self, file_bytes: bytes) -> int:
            try:
                with fitz.open(stream=file_bytes, filetype="pdf") as pdf:
                    return pdf.page_count
            except Exception as e:
                logging.error(f"Error al contar páginas: {e}")
                return float("inf")

        def list_blobs_by_page_count(self, prefix: str = "", suffix: str = "pdf") -> list[tuple[str, int]]:
            """
            Lista los blobs ordenados por número de páginas de menor a mayor.
            :return: Lista de tuplas (blob_name, num_paginas), ordenadas por num_paginas.
            """
            blobs = self.list_blobs(prefix=prefix, suffix=suffix)
            blobs_with_pages = []
            for blob_name in blobs:
                file_bytes = self.download_file(blob_name)
                if file_bytes:
                    num_pages = self.get_pdf_page_count(file_bytes)
                    blobs_with_pages.append((blob_name, num_pages))
            blobs_with_pages.sort(key=lambda x: x[1])
            return [nombre for nombre, paginas in blobs_with_pages]

    class DocumentIntelligence:
        """
        Clase para gestionar la inteligencia de documentos en Azure.
        Permite realizar operaciones de análisis y procesamiento de documentos.
        """

        def __init__(self):
            """
            Inicializa el cliente de Document Intelligence con la configuración del sistema.
            """
            self.endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
            self.api_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_API_KEY")
            self.document_analysis_client = DocumentAnalysisClient(
                endpoint=self.endpoint, credential=AzureKeyCredential(self.api_key)
            )

        def extract_doc_text(
            self,
            model: str = "prebuilt-layout",
            file_obj: bytes = None,
            file_path: str = None,
            batch_size: int = 2000,
            return_tables: bool = True,
        ):
            if file_obj is not None:
                pdf_doc = fitz.open(stream=file_obj, filetype="pdf")
            elif file_path is not None:
                pdf_doc = fitz.open(file_path)
            else:
                raise ValueError("Debe proporcionarse 'file_obj' o 'file_path'.")

            total_pages = pdf_doc.page_count
            full_content_list = []
            last_result = None  # para almacenar el último resultado útil

            for start in range(0, total_pages, batch_size):
                end = min(start + batch_size, total_pages)
                temp_pdf = fitz.open()
                for page_num in range(start, end):
                    temp_pdf.insert_pdf(pdf_doc, from_page=page_num, to_page=page_num)
                batch_bytes = temp_pdf.tobytes()
                temp_pdf.close()

                print(
                    f"Procesando páginas {start}-{end - 1} | Tamaño del batch: {len(batch_bytes) / 1024 / 1024:.2f} MB"
                )

                try:
                    poller = self.document_analysis_client.begin_analyze_document(model, document=batch_bytes)
                    result = poller.result(timeout=600)
                    last_result = result
                except Exception as e:
                    print(f"Error procesando páginas {start}-{end - 1}: {e}")
                    continue

                for batch_page_index, page in enumerate(result.pages):
                    real_page_num = start + batch_page_index + 1
                    page_text_lines = [line.content for line in page.lines]
                    page_text = f"Page {real_page_num}:\n" + " ".join(page_text_lines)
                    full_content_list.append(page_text)

            pdf_doc.close()
            texto_completo = " ".join(full_content_list)
            if return_tables and last_result and last_result.tables:
                tables = self._extract_tables(last_result)
                return texto_completo, tables, total_pages, poller
            else:
                return None, None, None, poller

        def _extract_tables(self, result, min_rows=0, min_cols=0):
            """
            Extrae tablas útiles del análisis del documento.

            :param result: Resultado del análisis del documento.
            :param min_rows: Mínimo de filas para considerar la tabla.
            :param min_cols: Mínimo de columnas para considerar la tabla.
            :return: Lista de tablas HTML (o DataFrame si prefieres).
            """
            tables = []
            for table in result.tables:
                max_idx = np.max([cell.row_index for cell in table.cells])
                max_jdx = np.max([cell.column_index for cell in table.cells])

                tb = pd.DataFrame(np.zeros((max_idx + 1, max_jdx + 1)), dtype=str)
                for cell in table.cells:
                    tb.iloc[cell.row_index, cell.column_index] = str(cell.content)

                if tb.shape[0] < min_rows or tb.shape[1] < min_cols:
                    continue

                if tb.apply(lambda x: x.str.strip()).replace("", np.nan).isnull().all().all():
                    continue

                html_table = tb.to_html(index=False)
                tables.append(html_table)
            return tables

    class AzureOpenAI:
        """
        Clase para gestionar la interacción con Azure OpenAI.
        Permite enviar solicitudes a modelos de lenguaje y obtener respuestas.
        """

        def __init__(self):
            """
            Inicializa el cliente de Azure OpenAI con la configuración del sistema.
            """
            self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            self.api_key = os.getenv("AZURE_OPENAI_API_KEY")

            self.model_chat_41 = os.getenv("AZURE_OPENAI_CHAT_MODEL_41")
            self.model_chat_api_version_41 = os.getenv("AZURE_OPENAI_CHAT_API_VERSION_41")

            self.model_chat_41mini = os.getenv("AZURE_OPENAI_CHAT_MODEL_41MINI")
            self.model_chat_api_version_41mini = os.getenv("AZURE_OPENAI_CHAT_API_VERSION_41MINI")

            self.model_embedding = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL")
            self.embedding_api_version = os.getenv("AZURE_OPENAI_EMBEDDING_API_VERSION")

            if not all([self.endpoint, self.api_key, self.model_embedding]):
                raise ValueError("Faltan variables de entorno para Azure OpenAI.")

            self.client_embeddings = AzureOpenAIEmbeddings(
                azure_endpoint=self.endpoint,
                api_key=self.api_key,
                api_version=self.embedding_api_version,
                azure_deployment=self.model_embedding,
            )
            self.openai_client = openai.AzureOpenAI(
                api_key=self.api_key,
                api_version=self.embedding_api_version,
                azure_endpoint=self.endpoint,
            )

            self.llm_4 = AzureChatOpenAI(
                azure_deployment=self.model_chat_41,
                azure_endpoint=self.endpoint,
                api_key=self.api_key,
                api_version=self.model_chat_api_version_41,
                temperature=0.4,
            )

            self.models = {"gpt-41": self.llm_4}

        def load_model(self, model_name: str):
            try:
                return self.models[model_name]
            except AttributeError as e:
                print(f"Model not initialized: {e}")
                return e

        def embeddings_generation(self, docs: list, columns: dict = None) -> pd.DataFrame:
            """
            Genera embeddings para las claves especificadas de una lista de diccionarios
            y asigna un ID único si no existe.
            Usada para generar embeddings de documentos en Azure OpenAI.(Indexar)

            :param docs: Lista de diccionarios con los datos a procesar.
            :param columns: Diccionario donde las claves son los nombres de las llaves originales
                            y los valores son los nombres de las nuevas llaves donde se almacenarán
                            los embeddings.
            :return: Lista de diccionarios con los embeddings generados.
            """
            df = pd.DataFrame(docs)
            for col_name, col_name_embeddings in columns.items():
                df[col_name_embeddings] = df[col_name].apply(lambda x: self.client_embeddings.embed_query(x))
            return df.to_dict(orient="records")

        def get_embedding(self, text: str) -> list[float]:
            """
            Genera un vector (embedding) para un texto dado usando el modelo de OpenAI.

            Args:
                text (str): El texto a vectorizar.

            Returns:
                list[float]: La representación vectorial del texto.
            """
            embedding = self.openai_client.embeddings.create(input=[text], model=self.model_embedding).data[0].embedding
            return embedding

        def model_response_with_history(
            self, query: str, system_prompt: str, history_msg: list[dict] = None, response_format: dict = None
        ) -> tuple[str, str]:
            """
            Genera una respuesta basada en el prompt proporcionado utilizando el asistente GPT
            de Azure OpenAI.

            Parámetros
            -----------
            - query (str): La consulta original del usuario.
            - system_prompt (str): El prompt del sistema.
            - history_msg (list[dict]): Historial de mensajes.
            - response_format (dict, optional): Formato de respuesta.

            Return
            --------
            - str: La respuesta generada por el asistente legal.
            - str: El modelo utilizado.
            """
            messages = [{"role": "system", "content": system_prompt}]
            if history_msg:
                messages += history_msg

            messages.append({"role": "user", "content": query})

            print("Messages:", messages)
            print("🤖 Generando respuesta con el modelo de lenguaje...")
            model = self.model_chat_41
            params = {"model": model, "messages": messages, "temperature": 0.1, "max_tokens": 25000}
            if response_format is not None:
                params["response_format"] = response_format

            response = self.openai_client.chat.completions.create(**params)

            return response.choices[0].message.content, model

        def model_response(
            self, query: str, system_prompt: str, response_format: str = None, model: str = "gpt-4.1"
        ) -> tuple[str, str]:
            """
            Genera una respuesta basada en el prompt proporcionado utilizando el asistente GPT
            de Azure OpenAI.

            Parámetros
            -----------
            - query (str): La consulta original del usuario.
            - system_prompt (str): El prompt del sistema.
            - response_format (str, optional): Formato de respuesta.
            - model (str): El modelo a usar.

            Return
            --------
            - str: La respuesta generada por el asistente legal.
            - str: El modelo utilizado.
            """
            print("🤖 Generando respuesta con el modelo de lenguaje...")

            if model == "gpt-4.1":
                model = self.model_chat_41
            if model == "gpt-4.1mini":
                model = self.model_chat_41mini

            print(f"Ejecución usando el modelo: {model}")
            params = {
                "model": model,
                "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": query}],
                "temperature": 0.1,
                "max_tokens": 25000,
            }
            if response_format is not None:
                params["response_format"] = response_format

            response = self.openai_client.chat.completions.create(**params)

            return response.choices[0].message.content, model

    class CosmosDB:
        """Clase para gestionar la conexión y operaciones con Azure Cosmos DB utilizando MongoDB API."""

        def __init__(self, connection_string, db_name, collection_names):
            try:
                if isinstance(collection_names, str):
                    collection_names = [collection_names]

                self.connection_string = connection_string
                self.db_name = db_name
                self.collection_names = collection_names
                self.client = self._initialize_client()
                self.db = self._create_database_and_collections()
            except ServerSelectionTimeoutError as e:
                logging.exception("Error al conectar con la base de datos: %s", str(e))
                raise
            except KeyError as e:
                logging.exception("Error al acceder a la colección 'Users': %s", str(e))
                raise
            except Exception as e:
                logging.exception("Error inesperado durante la inicialización de CosmosDBClient: %s", str(e))
                raise

        def _initialize_client(self):
            try:
                client = MongoClient(self.connection_string)
                client.server_info()
                return client
            except ServerSelectionTimeoutError:
                logging.exception("Invalid API for MongoDB connection string or timed out when attempting to connect.")
                raise

        def _create_database_and_collections(self):
            try:
                db = self.client[self.db_name]
                for collection_name in self.collection_names:
                    if collection_name not in db.list_collection_names():
                        db.create_collection(collection_name)
                        db[collection_name].create_index("user_id")
                        logging.info(f"Colección {collection_name} creada en la base de datos {self.db_name}.")
                    else:
                        logging.info(f"Colección {collection_name} ya existe en la base de datos {self.db_name}.")
                return db
            except Exception as e:
                logging.exception(f"Error al crear la base de datos o colecciones: {e}")
                raise

        def get_database(self):
            try:
                print(f"Conectando a la base de datos {self.db_name}...")
                return self.client[self.db_name]
            except Exception as e:
                logging.error(f"Error al obtener la base de datos: {str(e)}")
                return None

        def test_connection(self):
            try:
                db = self.get_database()
                collections = db.list_collection_names()
                print("Conexión exitosa. Colecciones encontradas:", collections)
                return True
            except Exception as e:
                print("Error en la conexión a CosmosDB Mongo:", str(e))
                return False

        def insert_message(self, data: dict, collection_name: str):
            try:
                result = self.db[collection_name].insert_one(data)
                logging.info(f"Mensaje guardado con ID: {result.inserted_id}")
                return str(result.inserted_id)
            except Exception as e:
                logging.exception(f"Error al insertar mensaje en {collection_name}: {e}")
                return None

        def get_messages_by_user(self, user_id: str, collection_name: str):
            try:
                messages = list(self.db[collection_name].find({"user_id": user_id}))
                for m in messages:
                    m["_id"] = str(m["_id"])
                return messages
            except Exception as e:
                logging.exception(f"Error al recuperar mensajes: {e}")
                return []

        def get_messages_by_user_and_time(self, user_id: str, collection_name: str):
            try:
                now = datetime.now(UTC)
                two_hours_ago = now - timedelta(hours=2)

                messages = list(
                    self.db[collection_name].find({"user_id": user_id, "timestamp": {"$gte": two_hours_ago}})
                )
                for m in messages:
                    m["_id"] = str(m["_id"])
                return messages
            except Exception as e:
                logging.exception(f"Error al recuperar mensajes: {e}")
                return []

        def get_users_lists(self, collection_name: str, doc_ids: list):
            """
            Obtiene y concatena las listas de usuarios ('users') de varios documentos _id
            en una colección.
            """
            try:
                cursor = self.db[collection_name].find({"_id": {"$in": doc_ids}})
                users = []
                for doc in cursor:
                    if "users" in doc:
                        users.extend(doc["users"])
                return users
            except Exception as e:
                logging.exception(f"Error al obtener usuarios de los documentos {doc_ids}: {e}")
                return []

        def update_users_field(self, doc: dict, collection_name: str):
            try:
                result = self.db[collection_name].update_one(
                    {"_id": doc["_id"]}, {"$set": {"users": doc["users"]}}, upsert=True
                )
                return result.modified_count
            except Exception as e:
                logging.exception(f"Error al actualizar users en {collection_name}: {e}")
                return None

        def update_message(self, filter_query: dict, update_fields: dict, collection_name: str):
            collection = self.db[collection_name]
            collection.update_one(filter_query, {"$set": update_fields})

    class AzureIASearch:
        """
        Clase que proporciona funcionalidades para interactuar con Azure AI Search.

        Esta clase permite realizar operaciones como la creación de índices, carga de documentos,
        búsquedas híbridas, eliminación de documentos y gestión de identificadores únicos (hashes)
        en un índice de Azure AI Search.

        Atributos:
            endpoint (str): Punto de conexión para Azure AI Search.
            api_key (str): Clave de API para autenticación en Azure AI Search.
            endpoint_oai (str): Punto de conexión para Azure OpenAI.
            api_key_oai (str): Clave de API para autenticación en Azure OpenAI.
            model_name_oai (str): Nombre del modelo de embeddings en Azure OpenAI.
            api_version_oai (str): Versión de la API de Azure OpenAI.
            index_client (SearchIndexClient): Cliente para la gestión de índices en Azure AI Search.
        """

        def __init__(self):
            """
            Inicializa la clase AzureSearchFunctions con las credenciales y configuración necesarias.

            Carga las credenciales y configuraciones desde variables de entorno y configura el cliente
            para la gestión de índices en Azure AI Search.
            """
            self.endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
            self.api_key = os.getenv("AZURE_AI_SEARCH_API_KEY")

            self.endpoint_oai = os.getenv("AZURE_OPENAI_ENDPOINT")
            self.api_key_oai = os.getenv("AZURE_OPENAI_API_KEY")
            self.model_name_oai = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL")
            self.api_version_oai = os.getenv("AZURE_OPENAI_EMBEDDING_API_VERSION")

            self.index_client = SearchIndexClient(endpoint=self.endpoint, credential=AzureKeyCredential(self.api_key))

        def consistent_encode(self, input_string: str) -> str:
            """
            Codifica una cadena de manera consistente usando SHA-256.

            Parámetros:
                input_string (str): La cadena a codificar.

            Retorna:
                encoded (str): La cadena codificada.
            """
            encoded = hashlib.sha256(input_string.encode()).hexdigest()
            return encoded

        def create_index(
            self, index_name: str, fields: list[SearchField], vector_search=None, semantic_config=None
        ) -> SearchIndex:
            """
            Crea un índice en Azure Search con opciones avanzadas.

            Parámetros:
            - index_name: Nombre del índice.
            - fields: Lista de campos para definir la estructura del índice.
            - vector_search: Configuración opcional para búsqueda vectorial.
            - semantic_config: Configuración opcional para semántica.

            Retorna:
                SearchIndex: El índice creado o actualizado. Retorna None si ocurre un error.
            """
            try:
                existing_indexes = [index.name for index in self.index_client.list_indexes()]
                if index_name in existing_indexes:
                    print("----------------------------------------------------------------")
                    print(f"El índice '{index_name}' ya existe. No se creará un nuevo índice.")
                    print("----------------------------------------------------------------")
                    return None

                print("----------------------------------------------------------------")
                print(f"Creando el índice '{index_name}'...")
                semantic_search = SemanticSearch(configurations=semantic_config)
                index = SearchIndex(
                    name=index_name, fields=fields, vector_search=vector_search, semantic_search=semantic_search
                )

                result = self.index_client.create_or_update_index(index)
                print("----------------------------------------------------------------")
                print(f"Índice '{index_name}' creado exitosamente.")
                return result
            except Exception as e:
                print(f"Error creando el índice '{index_name}': {str(e)}")
                return None

        def upload_documents(self, documents: list[dict], index_name: str) -> None:
            """
            Carga documentos en Azure Search en batches de máximo 950 documentos por petición.

            Parámetros:
                documents (pd.DataFrame): DataFrame de Pandas con los documentos a cargar.
                index_name (str): Nombre del índice donde se cargarán los documentos.

            Retorna:
                None: La función no retorna ningún valor, pero carga los documentos en el índice.
            """
            self.search_client_upload = SearchClient(
                endpoint=self.endpoint, index_name=index_name, credential=AzureKeyCredential(self.api_key)
            )
            batch_size = 950
            total_docs = len(documents)
            print(f"Subiendo {total_docs} documentos al índice {index_name} (batch size={batch_size})")

            for i in range(0, total_docs, batch_size):
                batch = documents[i : i + batch_size]
                print(f"Subiendo documentos {i + 1} a {i + len(batch)}...")
                try:
                    self.search_client_upload.upload_documents(documents=batch)
                except Exception as e:
                    print(f"Error al subir documentos {i + 1} a {i + len(batch)}: {str(e)}")

        def hybrid_search(
            self, query: str, index_name: str, top_k: int = 5, odata_filter: str | None = None
        ) -> list[dict]:
            """
            Realiza una búsqueda híbrida (vector + texto) con reclasificación semántica.

            Args:
                query (str): La consulta del usuario.
                index_name (str): Nombre del índice.
                top_k (int): Número de resultados a devolver.
                odata_filter (Optional[str]): Filtro OData opcional.

            Returns:
                list[str]: Una lista de los fragmentos de contenido más relevantes.
            """
            search_client = SearchClient(
                endpoint=self.endpoint, index_name=index_name, credential=AzureKeyCredential(self.api_key)
            )

            openai_client = AzureServices.AzureOpenAI()
            query_vector = openai_client.get_embedding(query)

            vector_query = VectorizedQuery(
                vector=query_vector, k_nearest_neighbors=top_k, fields="embedded_content_ltks"
            )

            print(f"🔍 Realizando búsqueda híbrida para: '{query}'")

            results = search_client.search(
                search_text=query,
                filter=odata_filter,
                vector_queries=[vector_query],
                query_type=QueryType.SEMANTIC,
                semantic_configuration_name="semantic-config",
                top=top_k,
                select=["doc_id", "content", "page_number", "bloque", "docnm"],
                highlight_fields="content",
            )

            top_content = [content for content in results]

            if not top_content:
                print("⚠️ No se encontraron resultados con un puntaje de reclasificación suficientemente alto.")
                return []

            print(f"📚 Se encontraron {len(top_content)} fragmentos de texto relevantes.")
            return top_content

        def check_document_exists(self, index_name: str, hash_group_id: str) -> bool:
            """
            Verifica si existen documentos en un índice específico de Azure Search.

            Parámetros:
                index_name (str): Nombre del índice a consultar.
                hash_group_id (str): ID del grupo de documentos para filtrar la búsqueda.

            Retorna:
                bool: True si hay documentos en el índice, False si no hay documentos o si ocurre un error.
            """
            search_client = SearchClient(
                endpoint=self.endpoint, index_name=index_name, credential=AzureKeyCredential(self.api_key)
            )

            results = search_client.search(
                search_text="*", filter=f"group_id eq '{hash_group_id}'", select="group_id", top=1000
            )

            for _ in results:
                return True
            return False
