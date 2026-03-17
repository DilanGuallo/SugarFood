# Servicio para Azure Document Intelligence (Form Recognizer)

import json
from typing import List

import requests

from ..models.schemas import MenuAzca


from pathlib import Path


def _load_config() -> dict:
    """Carga la configuración de Document Intelligence desde connections.json."""
    config_path = Path(__file__).resolve().parents[2] / 'config' / 'connections.json'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            full_config = json.load(f)
        return full_config.get('document_intelligence', {})
    except FileNotFoundError as e:
        raise RuntimeError(
            f"No se encontró la configuración en {config_path}. "
            "Asegúrate de que existe la sección 'document_intelligence'." 
        ) from e


def _extract_text_from_layout_response(response_json: dict) -> str:
    """Extrae todo el texto reconocido por el modelo de layout."""
    # El servicio incluye el texto en response_json.get("content") para muchos formatos.
    if response_json.get('content'):
        return response_json['content']

    # Si no existe el campo content, construimos el texto a partir de las líneas de las páginas.
    pages = response_json.get('pages', [])
    lines: List[str] = []

    for page in pages:
        for line in page.get('lines', []):
            text = line.get('content')
            if text:
                lines.append(text)

    return "\n".join(lines)


def _parse_menu_fields(fields: dict) -> MenuAzca:
    """Parsea fields extraídos por un modelo custom de Document Intelligence."""
    menu = MenuAzca()

    # Mapear campos conocidos - buscar por contenido en el nombre del field
    for field_name, value_obj in fields.items():
        field_lower = field_name.lower()

        if 'menu' in field_lower and 'dia' in field_lower:
            if isinstance(value_obj, dict) and 'valueString' in value_obj and value_obj['valueString']:
                menu.menu_del_dia = value_obj['valueString']
        elif 'precio' in field_lower:
            if isinstance(value_obj, dict) and 'valueString' in value_obj and value_obj['valueString']:
                menu.precio = value_obj['valueString']
        elif 'bar' in field_lower or 'rest' in field_lower:
            if isinstance(value_obj, dict) and 'valueString' in value_obj and value_obj['valueString']:
                menu.bar_rest = value_obj['valueString']
        elif 'telefono' in field_lower or 'tel' in field_lower:
            if isinstance(value_obj, dict) and 'valueString' in value_obj and value_obj['valueString']:
                menu.telefono = value_obj['valueString']
        elif 'aperitivo' in field_lower:
            if isinstance(value_obj, dict) and 'valueString' in value_obj and value_obj['valueString']:
                menu.aperitivo = value_obj['valueString']
        elif 'primero' in field_lower or 'primeros' in field_lower:
            if isinstance(value_obj, dict) and 'valueArray' in value_obj:
                menu.primeros = [item.get('valueString', '') for item in value_obj['valueArray'] if item.get('valueString')]
            elif isinstance(value_obj, dict) and 'valueString' in value_obj and value_obj['valueString']:
                menu.primeros = [value_obj['valueString']]
        elif 'segundo' in field_lower or 'segundos' in field_lower:
            if isinstance(value_obj, dict) and 'valueArray' in value_obj:
                menu.segundos = [item.get('valueString', '') for item in value_obj['valueArray'] if item.get('valueString')]
            elif isinstance(value_obj, dict) and 'valueString' in value_obj and value_obj['valueString']:
                menu.segundos = [value_obj['valueString']]
        elif 'complemento' in field_lower or 'guarnicion' in field_lower:
            if isinstance(value_obj, dict) and 'valueArray' in value_obj:
                menu.complemento = [item.get('valueString', '') for item in value_obj['valueArray'] if item.get('valueString')]
            elif isinstance(value_obj, dict) and 'valueString' in value_obj and value_obj['valueString']:
                menu.complemento = [value_obj['valueString']]
        elif 'postre' in field_lower:
            if isinstance(value_obj, dict) and 'valueArray' in value_obj:
                menu.postre = [item.get('valueString', '') for item in value_obj['valueArray'] if item.get('valueString')]
            elif isinstance(value_obj, dict) and 'valueString' in value_obj and value_obj['valueString']:
                menu.postre = [value_obj['valueString']]
        elif 'infantil' in field_lower or 'nino' in field_lower:
            if isinstance(value_obj, dict) and 'valueArray' in value_obj:
                menu.menu_infantil = [item.get('valueString', '') for item in value_obj['valueArray'] if item.get('valueString')]
            elif isinstance(value_obj, dict) and 'valueString' in value_obj and value_obj['valueString']:
                menu.menu_infantil = [value_obj['valueString']]

    # Guardar fields crudos para depuración
    menu.platos = str(fields)

    return menu


def analyze_menu_image(file_bytes: bytes, content_type: str) -> MenuAzca:
    """Analiza la imagen usando Azure Document Intelligence y devuelve un MenuAzca."""
    cfg = _load_config()

    endpoint = cfg.get('endpoint')
    key = cfg.get('key')
    model_id = cfg.get('model_id', 'prebuilt-document')
    if not endpoint or not key:
        raise RuntimeError('Falta endpoint, key o model_id en backend/config/connections.json')

    api_version = cfg.get('api_version', '2023-07-31')
    url = f"{endpoint.rstrip('/')}/formrecognizer/documentModels/{model_id}:analyze?api-version={api_version}"

    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Content-Type': content_type or 'application/octet-stream'
    }

    # Enviar la solicitud de análisis
    response = requests.post(url, headers=headers, data=file_bytes)

    if response.status_code != 202:
        error_text = response.text
        raise RuntimeError(
            f"Error al iniciar el análisis: {response.status_code} - {error_text}"
        )

    # Obtener la URL de operación para consultar el resultado
    operation_location = response.headers.get('Operation-Location')
    if not operation_location:
        raise RuntimeError("No se recibió la ubicación de la operación")

    # Esperar y consultar el resultado
    import time
    max_retries = 30  # Máximo 30 intentos (aprox. 1 minuto)
    retry_delay = 2   # 2 segundos entre intentos

    for _ in range(max_retries):
        result_response = requests.get(operation_location, headers={'Ocp-Apim-Subscription-Key': key})
        
        if result_response.status_code == 200:
            result_json = result_response.json()
            status = result_json.get('status')
            
            if status == 'succeeded':
                # Extraer fields del resultado (para modelos custom)
                analyze_result = result_json.get('analyzeResult', {})
                documents = analyze_result.get('documents', [])
                if documents:
                    fields = documents[0].get('fields', {})
                    print(f"DEBUG: Fields extraídos: {fields}")
                    for field_name, value_obj in fields.items():
                        print(f"DEBUG: Field {field_name}: {value_obj}")
                    menu = _parse_menu_fields(fields)
                else:
                    key_value_pairs = analyze_result.get('keyValuePairs', [])
                    print(f"DEBUG: Key-value pairs extraídos: {key_value_pairs}")
                    menu = _parse_menu_key_value_pairs(key_value_pairs)
                return menu
            if status == 'failed':
                error_details = result_json.get('error', {}).get('message', 'Error desconocido')
                raise RuntimeError(f"El análisis falló: {error_details}")
        
        time.sleep(retry_delay)
    
    raise RuntimeError("Tiempo de espera agotado para el análisis de la imagen")
