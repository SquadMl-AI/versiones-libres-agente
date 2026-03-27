import os
import json


MAP_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "../schemas/kb_id_to_name.json")
DOC_CATALOG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "../schemas/kb_id_to_documents.json")


def get_kb_name_from_id(kb_id: str) -> str:
    """Devuelve el nombre legible de un kb_id usando el catálogo local."""
    if not hasattr(get_kb_name_from_id, "kb_map"):
        if os.path.exists(MAP_PATH):
            with open(MAP_PATH, "r") as f:
                try:
                    get_kb_name_from_id.kb_map = json.load(f)
                except json.JSONDecodeError:
                    get_kb_name_from_id.kb_map = {}
        else:
            get_kb_name_from_id.kb_map = {}
    return get_kb_name_from_id.kb_map.get(kb_id, "Nombre no encontrado")


def load_kb_id_to_name_map():
    """Carga el mapeo de kb_id a nombre desde el archivo JSON."""
    if os.path.exists(MAP_PATH):
        with open(MAP_PATH, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def load_kb_id_to_documents_map():
    """Carga el mapeo de kb_id a documentos desde el archivo JSON."""
    if os.path.exists(DOC_CATALOG_PATH):
        with open(DOC_CATALOG_PATH, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}