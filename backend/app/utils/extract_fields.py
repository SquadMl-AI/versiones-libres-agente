# Script para extraer los nombres de los campos del mapping de Elasticsearch
# Uso: python3 backend/app/utils/extract_fields.py
import json
import os

MAPPING_PATH = 'backend/app/utils/elasticsearch_mapping.txt'
OUTPUT_PATH = 'backend/app/utils/elasticsearch_field_names.txt'


def extract_fields(mapping, index_name):
    props = mapping[index_name]['mappings']['properties']

    def walk_props(props, prefix=''):
        fields = []
        for k, v in props.items():
            if 'properties' in v:
                fields += walk_props(v['properties'], prefix + k + '.')
            else:
                fields.append(prefix + k)
        return fields

    return walk_props(props)


if not os.path.exists(MAPPING_PATH):
    print(f'No se encontró el archivo {MAPPING_PATH}. Descarga el mapping primero.')
    exit(1)

with open(MAPPING_PATH, 'r') as f:
    mapping = json.load(f)

index_name = list(mapping.keys())[0]
fields = extract_fields(mapping, index_name)

with open(OUTPUT_PATH, 'w') as out:
    for field in fields:
        out.write(field + '\n')

print(f'Campos extraídos: {len(fields)}. Guardados en {OUTPUT_PATH}')