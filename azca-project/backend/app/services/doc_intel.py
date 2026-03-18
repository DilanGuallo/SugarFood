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


def _build_analyze_url(endpoint: str, model_id: str, api_version: str) -> str:
    """Construye la URL de análisis según la versión del API."""
    normalized_endpoint = endpoint.rstrip('/')
    base_path = 'documentintelligence' if api_version >= '2024-11-30' else 'formrecognizer'
    return (
        f"{normalized_endpoint}/{base_path}/documentModels/"
        f"{model_id}:analyze?api-version={api_version}"
    )


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


def _extract_nested_value_v2(item: dict) -> str | None:
    """Extrae texto de estructuras anidadas de Document Intelligence."""
    if not isinstance(item, dict):
        return None

    value_string = item.get('valueString')
    if isinstance(value_string, str) and value_string.strip():
        return value_string.strip()

    content = item.get('content')
    if isinstance(content, str) and content.strip():
        return content.strip()

    value_object = item.get('valueObject')
    if isinstance(value_object, dict):
        nested_values = []
        for nested in value_object.values():
            nested_value = _extract_nested_value_v2(nested)
            if nested_value:
                nested_values.append(nested_value)
        if nested_values:
            return " ".join(nested_values).strip()

    return None


def _dedupe_preserve_order_v2(values: List[str]) -> List[str]:
    """Elimina duplicados y valores vacios manteniendo el orden."""
    unique_values: List[str] = []
    seen = set()

    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique_values.append(normalized)

    return unique_values


def _extract_field_value_v2(field_obj: dict) -> str | list:
    """Extrae el valor de un field del modelo custom, manejando strings, arrays y objetos."""
    if not isinstance(field_obj, dict):
        return None

    if 'valueArray' in field_obj:
        array = field_obj['valueArray']
        if isinstance(array, list):
            values = []
            for item in array:
                extracted = _extract_nested_value_v2(item)
                if extracted:
                    values.append(extracted)
            values = _dedupe_preserve_order_v2(values)
            return values if values else None

    return _extract_nested_value_v2(field_obj)


def _apply_menu_fallbacks_v2(menu: MenuAzca) -> MenuAzca:
    """Completa campos derivados para no dejar el menu sin platos visibles."""
    menu.primeros = _dedupe_preserve_order_v2(menu.primeros or [])
    menu.segundos = _dedupe_preserve_order_v2(menu.segundos or [])
    menu.complemento = _dedupe_preserve_order_v2(menu.complemento or [])
    menu.postre = _dedupe_preserve_order_v2(menu.postre or [])
    menu.menu_infantil = _dedupe_preserve_order_v2(menu.menu_infantil or [])

    if not menu.platos:
        parts = []
        if menu.primeros:
            parts.append("Primeros: " + ", ".join(menu.primeros[:3]))
        if menu.segundos:
            parts.append("Segundos: " + ", ".join(menu.segundos[:3]))
        if menu.postre:
            parts.append("Postres: " + ", ".join(menu.postre[:2]))
        menu.platos = " | ".join(parts) if parts else "Menu del dia"

    if not menu.primeros and menu.platos:
        menu.primeros = [menu.platos]

    if not menu.segundos and menu.complemento:
        menu.segundos = menu.complemento[:2]

    if not menu.segundos and menu.postre:
        menu.segundos = ["Segundo por confirmar"]

    return menu


def _extract_field_value(field_obj: dict) -> str | list:
    """Extrae el valor de un field del modelo custom, manejando valueString y valueArray."""
    if not isinstance(field_obj, dict):
        return None
    
    # Intentar extraer valueString (campo simple)
    if 'valueString' in field_obj:
        value = field_obj['valueString']
        if value:
            return value
    
    # Intentar extraer valueArray (múltiples valores)
    if 'valueArray' in field_obj:
        array = field_obj['valueArray']
        if isinstance(array, list):
            values = []
            for item in array:
                if isinstance(item, dict) and 'valueString' in item:
                    val = item['valueString']
                    if val:
                        values.append(val)
            return values if values else None
    
    return None


def _parse_menu_fields(fields: dict) -> MenuAzca:
    """Parsea fields extraídos por un modelo custom de Document Intelligence."""
    menu = MenuAzca()

    # Procesar cada campo extraído por el modelo custom
    for field_name, value_obj in fields.items():
        if not isinstance(value_obj, dict):
            continue
        
        field_lower = field_name.lower()
        extracted_value = _extract_field_value_v2(value_obj)
        
        # Si no hay valor extraído, saltar
        if not extracted_value:
            continue

        # Mapear campos al modelo MenuAzca
        if field_lower == 'menu_del_dia':
            menu.menu_del_dia = extracted_value
        elif field_lower == 'precio':
            menu.precio = extracted_value
        elif field_lower == 'bar/rest' or field_lower == 'bar_rest':
            menu.bar_rest = extracted_value
        elif field_lower == 'telefono':
            menu.telefono = extracted_value
        elif field_lower == 'dia':
            menu.dia = extracted_value
        elif field_lower == 'fecha':
            menu.fecha = extracted_value
        elif field_lower == 'aperitivo':
            menu.aperitivo = extracted_value
        elif field_lower == 'primeros':
            # primeros puede ser string o lista
            menu.primeros = extracted_value if isinstance(extracted_value, list) else [extracted_value]
        elif field_lower == 'segundos':
            menu.segundos = extracted_value if isinstance(extracted_value, list) else [extracted_value]
        elif field_lower == 'complemento':
            menu.complemento = extracted_value if isinstance(extracted_value, list) else [extracted_value]
        elif field_lower == 'postre':
            menu.postre = extracted_value if isinstance(extracted_value, list) else [extracted_value]
        elif field_lower == 'menu_infantil':
            menu.menu_infantil = extracted_value if isinstance(extracted_value, list) else [extracted_value]
        elif field_lower == 'platos':
            menu.platos = extracted_value

    return _apply_menu_fallbacks_v2(menu)


def _parse_menu_key_value_pairs(key_value_pairs: list) -> MenuAzca:
    """Parsea key-value pairs extraídos por Document Intelligence (formato legacy)."""
    menu = MenuAzca()
    
    # Convertir key-value pairs a un diccionario y parsear
    fields_dict = {}
    for pair in key_value_pairs:
        if isinstance(pair, dict):
            key = pair.get('key', {}).get('content', '').lower()
            value = pair.get('value', {}).get('content', '')
            if key and value:
                fields_dict[key] = {'valueString': value}
    
    # Usar el parseador de fields existente
    return _parse_menu_fields(fields_dict)


def analyze_menu_image(file_bytes: bytes, content_type: str) -> MenuAzca:
    """Analiza la imagen usando Azure Document Intelligence y devuelve un MenuAzca."""
    cfg = _load_config()

    endpoint = cfg.get('endpoint')
    key = cfg.get('key')
    model_id = cfg.get('model_id', 'prebuilt-document')
    if not endpoint or not key:
        raise RuntimeError('Falta endpoint, key o model_id en backend/config/connections.json')

    api_version = cfg.get('api_version', '2024-11-30')
    url = _build_analyze_url(endpoint, model_id, api_version)

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

    for attempt in range(max_retries):
        result_response = requests.get(operation_location, headers={'Ocp-Apim-Subscription-Key': key})
        
        if result_response.status_code == 200:
            result_json = result_response.json()
            status = result_json.get('status')
            
            if status == 'succeeded':
                # Extraer fields del resultado
                analyze_result = result_json.get('analyzeResult', {})
                documents = analyze_result.get('documents', [])
                
                if documents:
                    # Usar el primer documento encontrado
                    doc = documents[0]
                    fields = doc.get('fields', {})
                    print(f"DEBUG: Fields extraídos del documento: {list(fields.keys())}")
                    menu = _parse_menu_fields(fields)
                    print(f"DEBUG: MenuAzca parseado: {menu}")
                    return menu
                else:
                    # Fallback a key-value pairs si no hay documentos estructurados
                    key_value_pairs = analyze_result.get('keyValuePairs', [])
                    print(f"DEBUG: Key-value pairs extraídos (fallback): {len(key_value_pairs)} pares")
                    menu = _parse_menu_key_value_pairs(key_value_pairs)
                    return menu
            
            if status == 'failed':
                error_details = result_json.get('error', {}).get('message', 'Error desconocido')
                raise RuntimeError(f"El análisis falló: {error_details}")
        
        # Si no está listo, esperar
        if attempt < max_retries - 1:
            time.sleep(retry_delay)
    
    raise RuntimeError("Tiempo de espera agotado para el análisis de la imagen")
