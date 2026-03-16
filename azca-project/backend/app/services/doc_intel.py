# Servicio para Azure Document Intelligence (Form Recognizer)

import json
from typing import List

import requests

from ..models.schemas import MenuAzca


from pathlib import Path


def _load_config() -> dict:
    """Carga la configuración local para Document Intelligence."""
    config_path = Path(__file__).resolve().parents[2] / 'config' / 'azure_doc_intel.json'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise RuntimeError(
            f"No se encontró la configuración de Azure Document Intelligence en {config_path}. "
            "Crea ese archivo con endpoint y key." 
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


def _parse_menu_text(text: str) -> MenuAzca:
    """Intenta mapear texto libre a los campos del modelo MenuAzca."""
    menu = MenuAzca()
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # Bucles simples para intentar capturar cabeceras y secciones.
    current_section = None
    sections = {
        'primeros': [],
        'segundos': [],
        'complemento': [],
        'postre': [],
        'menu_infantil': []
    }

    for line in lines:
        low = line.lower()

        # Campos generales
        if not menu.menu_del_dia and 'menú' in low and 'día' in low:
            menu.menu_del_dia = line
            continue
        if not menu.precio and ('precio' in low or '€' in line):
            menu.precio = line
            continue
        if not menu.bar_rest and ('bar' in low or 'rest' in low or 'restaurante' in low):
            menu.bar_rest = line
            continue
        if not menu.telefono and ('tel' in low or 'tlf' in low or 'telefono' in low or 'mobile' in low):
            menu.telefono = line
            continue
        if not menu.aperitivo and 'aperitivo' in low:
            menu.aperitivo = line
            continue

        # Secciones de platos
        if 'primeros' in low:
            current_section = 'primeros'
            continue
        if 'segundos' in low or 'segundo' in low:
            current_section = 'segundos'
            continue
        if 'complemento' in low or 'acompa' in low or 'guarnici' in low:
            current_section = 'complemento'
            continue
        if 'postre' in low:
            current_section = 'postre'
            continue
        if 'infantil' in low or 'niños' in low or 'kids' in low:
            current_section = 'menu_infantil'
            continue

        # Si estamos dentro de una sección, intentar agregar platos
        if current_section:
            # Saltar líneas que parecen ser títulos u otros datos
            if any(k in low for k in ['menú', 'precio', 'tel', 'bar', 'rest', 'aperitivo']):
                continue
            if len(line) > 2:
                sections[current_section].append(line)

    menu.primeros = sections['primeros']
    menu.segundos = sections['segundos']
    menu.complemento = sections['complemento']
    menu.postre = sections['postre']
    menu.menu_infantil = sections['menu_infantil']

    # Guardar texto crudo en platos para facilitar depuración
    menu.platos = text

    return menu


def analyze_menu_image(file_bytes: bytes, content_type: str) -> MenuAzca:
    """Analiza la imagen usando Azure Document Intelligence y devuelve un MenuAzca."""
    cfg = _load_config()

    endpoint = cfg.get('endpoint')
    key = cfg.get('key')
    if not endpoint or not key:
        raise RuntimeError('Falta endpoint o key en backend/config/azure_doc_intel.json')

    api_version = cfg.get('api_version', '2023-07-31')
    url = f"{endpoint.rstrip('/')}/formrecognizer/documentModels/prebuilt-layout:analyze?api-version={api_version}"

    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Content-Type': content_type or 'application/octet-stream'
    }

    response = requests.post(url, headers=headers, data=file_bytes)

    if not response.ok:
        raise RuntimeError(
            f"Error al analizar la imagen: {response.status_code} {response.text}"
        )

    json_response = response.json()
    text = _extract_text_from_layout_response(json_response)
    menu = _parse_menu_text(text)
    return menu
