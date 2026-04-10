import json
from pathlib import Path

from utils.indexing_pipeline import DocumentProcessingPipeline

pipeline = DocumentProcessingPipeline()

# Obtener lista identificadores de los documentos según el bloque
BASE_DIR = Path(__file__).resolve().parent
kb_ids_path = (BASE_DIR / "../../kb_id_to_name.json").resolve()

with kb_ids_path.open("r", encoding="utf-8") as archivo:
    kb_ids = json.load(archivo)

# Procesar documento
knowledge_base = pipeline.document_processing_indexing_orchestrator(
    kb_ids=kb_ids,
    index_name="index_sentencias",
)

output_path = BASE_DIR / "pdfembeddings2_pruebas_data.json"
with output_path.open("w", encoding="utf-8") as f:
    json.dump(knowledge_base, f, indent=4, ensure_ascii=False)
