# Script para generar un árbol kb_id -> lista de PDFs únicos (docnm_kwd) y un doc_id representativo por PDF
# Guarda el resultado en backend/schemas/tree_kb_id_pdf_and_docid.json

import os
import json
from collections import defaultdict

input_path = os.path.join(os.path.dirname(__file__), "doc_id_to_pdf_and_kb.json")
output_path = os.path.join(os.path.dirname(__file__), "tree_kb_id_pdf_and_docid.json")

with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Estructura: {kb_id: {docnm_kwd: doc_id_representativo}}
tree = defaultdict(dict)
for entry in data:
    doc_id = entry["doc_id"]
    docnm_kwd = entry["docnm_kwd"]
    kb_ids = entry["kb_id"] if isinstance(entry["kb_id"], list) else [entry["kb_id"]]
    for kb in kb_ids:
        # Solo guardar el primer doc_id encontrado para cada docnm_kwd en cada kb_id
        if docnm_kwd and docnm_kwd not in tree[kb]:
            tree[kb][docnm_kwd] = doc_id

# Convertir a formato árbol: {kb_id: [{docnm_kwd, doc_id}, ...]}
tree_json = {
    kb: [
        {"docnm_kwd": docnm_kwd, "doc_id": doc_id}
        for docnm_kwd, doc_id in pdfs.items()
    ]
    for kb, pdfs in tree.items()
}

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(tree_json, f, indent=2, ensure_ascii=False)

print(f"Árbol kb_id -> PDF único (docnm_kwd) y doc_id representativo guardado en {output_path}")