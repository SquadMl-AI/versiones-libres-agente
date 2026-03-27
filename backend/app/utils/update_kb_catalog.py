import json
import os


# Paths
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCHEMAS = os.path.join(BASE, "schemas")
KB_IDS_PATH = os.path.join(SCHEMAS, "kb_ids.json")
MAP_PATH = os.path.join(SCHEMAS, "kb_id_to_name.json")


def _load_kb_ids():
    """Load and return list of kb_ids from KB_IDS_PATH."""
    if not os.path.exists(KB_IDS_PATH):
        print(f"Error: El archivo {KB_IDS_PATH} no existe.")
        return []
    with open(KB_IDS_PATH, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _load_kb_id_to_name():
    """Load and return dictionary mapping kb_id to name from MAP_PATH."""
    if os.path.exists(MAP_PATH):
        with open(MAP_PATH, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    else:
        return {}


def print_kb_id_catalog_status():
    """Imprime el estado del catálogo kb_id_to_name.json respecto a kb_ids.json."""
    kb_ids = _load_kb_ids()
    if not kb_ids:
        return

    kb_id_to_name = _load_kb_id_to_name()

    print(f"{'kb_id':<36} | name")
    print("-" * 80)
    for kb_id in kb_ids:
        name = kb_id_to_name.get(kb_id, "NO ENCONTRADO")
        print(f"{kb_id:<36} | {name}")


def update_kb_catalog():
    """Actualiza interactivamente el catálogo de nombres de KB."""
    kb_ids = _load_kb_ids()
    if not kb_ids:
        return

    kb_id_to_name = _load_kb_id_to_name()

    updated = False
    for kb_id in kb_ids:
        if kb_id not in kb_id_to_name or kb_id_to_name[kb_id] == "NO ENCONTRADO":
            name = input(f"Ingrese el nombre para el kb_id '{kb_id}': ")
            if name:
                kb_id_to_name[kb_id] = name
                updated = True

    if updated:
        with open(MAP_PATH, "w") as f:
            json.dump(kb_id_to_name, f, indent=2)
        print("\nCatálogo actualizado exitosamente.")
    else:
        print("\nNo hay nuevos kb_ids que necesiten un nombre.")


def print_kb_id_catalog_status_colored():
    """Imprime la lista de KBs desde kb_id_to_name.json, con color y conteo, aunque no exista kb_ids.json."""
    GREEN = '\033[92m'
    RESET = '\033[0m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    # Intenta cargar el mapeo completo
    if os.path.exists(MAP_PATH):
        with open(MAP_PATH, "r") as f:
            try:
                kb_id_to_name = json.load(f)
            except json.JSONDecodeError:
                kb_id_to_name = {}
    else:
        print(f"{RED}Error: El archivo {MAP_PATH} no existe.{RESET}")
        return
    print(f"{'kb_id':<36} | name")
    print("-" * 80)
    for kb_id, name in kb_id_to_name.items():
        print(f"{GREEN}{kb_id:<36} | {name}{RESET}")
    print(f"{YELLOW}Total de KBs cargadas: {len(kb_id_to_name)}{RESET}")


if __name__ == "__main__":
    print("Estado actual del catálogo:")
    print_kb_id_catalog_status_colored()

    print("\n---")
    update_kb_catalog()

    print("\n---")
    print("Estado final del catálogo:")
    print_kb_id_catalog_status_colored()