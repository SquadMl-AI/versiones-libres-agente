import json
import logging
import os
import re

# Ajustar path para importaciones del proyecto
import sys
import traceback
import unicodedata

import fitz
from bs4 import BeautifulSoup
from dotenv import find_dotenv, load_dotenv
from langchain.docstore.document import Document
from langchain_experimental.text_splitter import SemanticChunker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.ai_services import AzureServices
from utils.index_config import create_fields, create_semantic_config, create_vectorsearch

load_dotenv(find_dotenv())


class DocumentProcessingPipeline:
    def __init__(
        self,
        blob_storage=AzureServices.AzureBlobStorage(),
        document_intelligence=AzureServices.DocumentIntelligence(),
        aoi_client=AzureServices.AzureOpenAI(),
        search_client=AzureServices.AzureIASearch(),
    ):
        self.blob_storage = blob_storage
        self.di = document_intelligence
        self.aoi_client = aoi_client
        self.search_client = search_client
        self.embeddings = aoi_client.client_embeddings
        self.chunker = SemanticChunker(
            embeddings=self.embeddings,
            breakpoint_threshold_type="percentile",
            breakpoint_threshold_amount=70,
            min_chunk_size=300,
            buffer_size=1,
        )

    def reading_processing_documents(self, blob: str, kb_ids: dict[str, str], index_name: str):
        """
        Lee y procesa los documentos PDF desde Blob Storage, extrayendo texto y tablas.
        Evita reprocesar documentos ya indexados en Azure Search.
        """
        data_json, tables_json = [], []

        logging.info(f"Procesando blob: {blob}")
        blob_split = blob.split("/")
        group_id = self.search_client.consistent_encode(f"{blob_split[0]}_{blob_split[1]}")
        print(f"Verificando si el documento {blob} ya existe en el índice {index_name} con group_id {group_id}.")
        try:
            check_document_exists = self.search_client.check_document_exists(
                index_name=index_name, hash_group_id=group_id
            )
        except Exception:
            print(f"Índice {index_name} no existe todavía. Continuando con procesamiento.")
            check_document_exists = False

        # Verificar si el documento ya existe en el índice para no procesarlo de nuevo
        if check_document_exists:
            logging.info(f"El documento {blob} ya existe en el índice. Se omite.")
            return None, None

        print(f"Documento nuevo, procesando: {blob}")
        # 1. Descargar el archivo PDF del blob storage
        pdf_bytes = self.blob_storage.download_file(blob)
        if not pdf_bytes:
            logging.warning(f"No se pudo descargar el archivo {blob}.")
            return None, None

        kd_id = next((k for k, v in kb_ids.items() if v == blob.split("/")[0]), None)

        # Obtener número total de páginas para hacer los lotes
        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = pdf_doc.page_count
        pdf_doc.close()

        batch_size = 2000

        for start in range(0, total_pages, batch_size):
            end = min(start + batch_size, total_pages)
            # Extraer lote de páginas (batch)
            temp_pdf = fitz.open()
            for page_num in range(start, end):
                temp_pdf.insert_pdf(fitz.open(stream=pdf_bytes, filetype="pdf"), from_page=page_num, to_page=page_num)
            batch_bytes = temp_pdf.tobytes()
            temp_pdf.close()

        # Obtener número total de páginas para hacer los lotes
        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = pdf_doc.page_count
        pdf_doc.close()

        batch_size = 2000

        for start in range(0, total_pages, batch_size):
            end = min(start + batch_size, total_pages)
            # Extraer lote de páginas (batch)
            temp_pdf = fitz.open()
            for page_num in range(start, end):
                temp_pdf.insert_pdf(fitz.open(stream=pdf_bytes, filetype="pdf"), from_page=page_num, to_page=page_num)
            batch_bytes = temp_pdf.tobytes()
            temp_pdf.close()
        # 2. Extraer texto usando Azure Document Intelligence
        _, tablas, _, poller = self.di.extract_doc_text(file_obj=batch_bytes)

        # 3. extraer los datos del poller
        data_poller = poller.result()
        paragraphs = data_poller.paragraphs
        tables = data_poller.tables
        filtered_paragraphs = [p for p in paragraphs if p.role not in ["pageHeader", "pageFooter", "footnote"]]

        # For para extarer la información de los párrafos filtrados
        for para in filtered_paragraphs:
            content = para.content
            if para.bounding_regions and len(para.bounding_regions) > 0:
                page_number = start + para.bounding_regions[0].page_number
                # polygon = [(point.x, point.y) for point in para.bounding_regions[0].polygon]
            else:
                page_number = None
                # polygon = None
            data_json.append(
                {
                    "docnm_kwd": blob.split("/")[-1].replace(".pdf", ""),
                    "docnm": blob.split("/")[-1],
                    "bloque": blob.split("/")[0],
                    "kb_id": kd_id,
                    "content": content,
                    "page_number": page_number,
                }
            )

        # Procesar tablas ajustando el número de página global
        for i, table in enumerate(tables):
            page_number_table = start + table.bounding_regions[0].page_number
            tables_json.append(
                {
                    "docnm_kwd": blob.split("/")[-1].replace(".pdf", ""),
                    "docnm": blob.split("/")[-1],
                    "bloque": blob.split("/")[0],
                    "kb_id": kd_id,
                    "content": tablas[i],
                    "page_number": [page_number_table],
                }
            )

        print(f"Se procesaron {len(data_json)} párrafos y {len(tables_json)} tablas del documento {blob}.")
        return data_json, tables_json

    def semantic_chunking(self, json_data: list[dict], tables_json: list[dict]) -> list[dict]:
        """
        Aplica SemanticChunker sobre el contenido textual agrupado por documento.
        Mapea la metadata correspondiente a cada chunk generado.
        """
        # Agrupar párrafos por documento (docnm)
        docs = {}
        for item in json_data:
            docnm = item["docnm"]
            if docnm not in docs:
                docs[docnm] = []
            docs[docnm].append(item)

        result_chunks = []
        for _, items in docs.items():
            # Concatenar contenido y mantener mapeo de offsets a metadata
            full_text = ""
            offset_to_metadata = {}
            current_offset = 0

            for item in items:
                content = item["content"]
                start_offset = current_offset
                end_offset = current_offset + len(content)
                # Mapear el rango de offsets a la metadata
                offset_to_metadata[(start_offset, end_offset)] = {
                    "docnm_kwd": item["docnm_kwd"],
                    "docnm": item["docnm"],
                    "bloque": item["bloque"],
                    "kb_id": item["kb_id"],
                    "page_number": item["page_number"],
                }
                full_text += content + " "
                current_offset = end_offset + 1

            # Crear un documento de LangChain
            doc = Document(page_content=full_text.strip())

            # Aplicar SemanticChunker
            chunks = self.chunker.split_documents([doc])

            # Asociar metadata a cada chunk
            for chunk in chunks:
                chunk_content = chunk.page_content
                chunk_start = full_text.find(chunk_content)
                chunk_end = chunk_start + len(chunk_content)

                # Encontrar la metadata correspondiente
                page_numbers = set()
                metadata = None
                for (start, end), meta in offset_to_metadata.items():
                    if not (chunk_end < start or chunk_start > end):
                        page_numbers.add(meta["page_number"])
                        if metadata is None:  # Tomar la metadata del primer párrafo
                            metadata = {
                                "docnm_kwd": meta["docnm_kwd"],
                                "docnm": meta["docnm"],
                                "bloque": meta["bloque"],
                                "kb_id": meta["kb_id"],
                            }

                result_chunks.append({"content": chunk_content, **metadata, "page_number": list(page_numbers)})
        print(f"Se generaron {len(result_chunks)} chunks semánticos a partir de {len(json_data)} párrafos.")
        logging.info(f"Se generaron {len(result_chunks)} chunks semánticos a partir de {len(json_data)} párrafos.")
        return result_chunks + tables_json  # Añadir las tablas al final

    def normalize_data(self, json_data: list[dict]) -> list[dict]:
        """
        Normaliza campos content y docnm_kwd para facilitar búsquedas
        (lowercase, sin tildes, sin signos, sin html).
        """

        def normalize_text(text: str, field: str) -> str:
            soup = BeautifulSoup(text, "html.parser")
            texto = soup.get_text(separator=" ").lower()
            if field != "docnm_tks":
                texto = unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("utf-8")
                texto = re.sub(r"[^\w\s]", "", texto)
                texto = re.sub(r"\s+", " ", texto).strip()
            return texto

        print(f"Se normalizaron {len(json_data)} registros: content_ltks y docnm_tks.")
        return [
            {
                **item,
                "content_ltks": normalize_text(item["content"], "content_ltks"),
                "docnm_tks": normalize_text(item["docnm_kwd"], "docnm_tks"),
            }
            for item in json_data
        ]

    def create_knowledge_base(self, index_name: str, knowledge_base: list[dict]):
        """
        Crea o actualiza una base de conocimiento en Azure Search para el índice "index_name".

        Parámetros:
            index_name (str): Nombre del índice en Azure Search.
            knowledge_base (list): lista de diccionarios que contiene la base de conocimiento a cargar.

        Retorna:
            None: La función no retorna ningún valor, pero realiza operaciones de creación/actualización del índice
                y carga de documentos en Azure Search.
        """

        # Crear el índice en Azure Search
        self.search_client.create_index(
            index_name=index_name,
            fields=create_fields(),
            vector_search=create_vectorsearch(),
            semantic_config=[create_semantic_config()],
        )
        # Convertir la base de conocimiento a minúsculas

        # Agregar una nueva columna que combine el contenido de todas las columnas
        for doc in knowledge_base:
            combined_str = " ".join(
                str(v) for v in doc.values()
            )  # Convertir todos los valores del diccionario a string
            combined_kb_id_docnm = f"{doc['bloque']}_{doc['docnm']}"
            doc["doc_id"] = self.search_client.consistent_encode(combined_str)
            doc["group_id"] = self.search_client.consistent_encode(combined_kb_id_docnm)

        # Generar embeddings para los nuevos documentos
        docs_with_embeddings = self.aoi_client.embeddings_generation(
            knowledge_base, columns={"content_ltks": "embedded_content_ltks"}
        )

        # Subir nuevos documentos al índice (ya con embeddings generados)
        self.search_client.upload_documents(docs_with_embeddings, index_name)

        return docs_with_embeddings

    def document_processing_indexing_orchestrator(self, kb_ids, index_name: str = "index_sentencias"):
        """Ejecuta el pipeline completo: listado de docoumentos, lectura y procesamiento, chunking, normalización"""

        pipeline = DocumentProcessingPipeline()

        metrics = {"blobs": 0, "paragraphs": 0, "tables": 0, "chunks": 0, "normalized": 0}
        all_docs_with_embeddings = []
        errores = []  # Aquí se van a guardar los logs de error
        # PASO 1: Obtener lista de documentos disponibles en el blob storage
        blobs_list = self.blob_storage.list_blobs()
        # PASO 2: Leer y procesar documentos
        for num, blob in enumerate(blobs_list[3:4], 1):
            print("\n")
            print(
                f"################################ Procesando documento [{num}]: {blob} #####################################"
            )
            print("\n")

            try:
                data_json, tables_json = pipeline.reading_processing_documents(
                    blob=blob, kb_ids=kb_ids, index_name=index_name
                )

                if not data_json:
                    logging.warning(f"No se procesó el documento {blob}. Continuando con el siguiente.")
                    continue  # Si no hay datos, saltar al siguiente documento

                # PASO 3: Semantic Chunking
                chunks = pipeline.semantic_chunking(data_json, tables_json)

                # PASO 4: Normalizar datos (Valores de content_ltks y docnm_tks)
                normalized_data = self.normalize_data(chunks)

                # PASO 5: Verifica documentos nuevos, genera embeddings e indexa en Azure Search
                docs_with_embeddings = self.create_knowledge_base(index_name=index_name, knowledge_base=normalized_data)

                metrics["blobs"] += 1
                metrics["paragraphs"] += len(data_json)
                metrics["tables"] += len(tables_json)
                metrics["chunks"] += len(chunks)
                metrics["normalized"] += len(normalized_data)
                all_docs_with_embeddings.extend(docs_with_embeddings)
            except Exception as e:
                # Log de error: guarda el número, blob, tipo de error y traceback
                error_msg = (
                    f"Error en la iteración {num} procesando blob {blob}:\n"
                    f"Tipo de error: {type(e).__name__}\n"
                    f"Mensaje: {str(e)}\n"
                    f"Traceback:\n{traceback.format_exc()}"
                )
                logging.error(error_msg)
                errores.append({"num": num, "blob": blob, "error": str(e), "traceback": traceback.format_exc()})
                continue  # Sigue con el siguiente documento

        print(
            f"Procesados {metrics['blobs']} documentos, {metrics['paragraphs']} párrafos, "
            f"{metrics['tables']} tablas, {metrics['chunks']} chunks y normalizados {metrics['normalized']} registros."
        )
        logging.info(
            f"Procesados {metrics['blobs']} documentos, {metrics['paragraphs']} párrafos, "
            f"{metrics['tables']} tablas, {metrics['chunks']} chunks y normalizados {metrics['normalized']} registros."
        )

        if errores:
            print(f"\nSe encontraron {len(errores)} errores durante la ejecución.")
            print(errores)

        return docs_with_embeddings


if __name__ == "__main__":
    pipeline = DocumentProcessingPipeline()

    # Obtener lista identificadores de los documentos segun el bloque
    with open("../../kb_id_to_name.json", encoding="utf-8") as archivo:
        kb_ids = json.load(archivo)

    # Procesar documento
    knowledge_base = pipeline.document_processing_indexing_orchestrator(kb_ids=kb_ids)

    with open("pdfembeddings_pruebas_data.json", "w", encoding="utf-8") as f:
        json.dump(knowledge_base, f, indent=4, ensure_ascii=False)
