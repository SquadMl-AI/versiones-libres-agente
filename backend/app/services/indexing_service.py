import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.indexing_pipeline import DocumentProcessingPipeline

pipeline = DocumentProcessingPipeline()

# Obtener lista identificadores de los documentos segun el bloque
with open('../../kb_id_to_name.json', 'r', encoding='utf-8') as archivo:
    kb_ids= json.load(archivo)

# Procesar documento
knowledge_base = pipeline.document_processing_indexing_orchestrator(kb_ids=kb_ids, index_name='index_sentencias')

with open("pdfembeddings2_pruebas_data.json", "w", encoding="utf-8") as f:
    json.dump(knowledge_base, f, indent=4, ensure_ascii=False)