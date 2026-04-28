import pdb

from dotenv import find_dotenv, load_dotenv
from langchain_experimental.text_splitter import SemanticChunker
from services.ai_services import AzureServices

# Cargar variables de entorno (asegúrate que el .env tenga las de Azure)
load_dotenv(find_dotenv())


def main():
    # Instanciar servicios de Azure
    blob_storage = AzureServices.AzureBlobStorage()
    di = AzureServices.DocumentIntelligence()
    openai = AzureServices.AzureOpenAI()

    # Ruta del blob en el contenedor (ajusta según tu estructura en Azure)
    blob_path = "Bloque Bananero/Sentencia-Jorge-Barney-Veloza-García.pdf"

    # 1. Descargar PDF del Blob Storage
    pdf_bytes = blob_storage.download_file(blob_path)
    print("Bytes descargados:", len(pdf_bytes) if pdf_bytes else "0")
    if pdf_bytes is None:
        print("No se pudo descargar el archivo.")
        return

    # 2. Extraer texto usando Azure Document Intelligence
    texto, tablas, num_paginas, poller = di.extract_doc_text(file_obj=pdf_bytes)
    print("Número de páginas:", num_paginas)
    print("Tablas extraídas:", len(tablas) if tablas else "0")

    # 3. Obtener embeddings del texto extraído
    # embeddings = openai.get_embeddings(texto)
    # print("Embeddings obtenidos:", embeddings

    pdb.set_trace()  # Iniciar el depurador aquí

    # 4. Crea el splitter semántico
    splitter = SemanticChunker(embeddings=openai.client_embeddings)
    # 4. Dividir el texto en chunks semánticos
    chunks = splitter.split_text(texto)

    for idx, chunk in enumerate(chunks):
        print(f"--- Chunk {idx + 1} ---")
        print(chunk)

    # # 3. Chunkear el texto
    # chunks = chunk_text(texto, chunk_size=1000, chunk_overlap=100)
    # print(f"Se dividió el texto en {len(chunks)} partes.")


if __name__ == "__main__":
    main()
