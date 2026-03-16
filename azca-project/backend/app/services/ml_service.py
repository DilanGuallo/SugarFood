# Servicio para conectar con un endpoint de Azure Machine Learning (Online Endpoint)

import json
from pathlib import Path
from typing import Any, Dict

import requests


def _load_config() -> Dict[str, Any]:
    """Carga la configuración de Azure ML desde backend/config/azure_ml.json."""
    config_path = Path(__file__).resolve().parents[2] / 'config' / 'azure_ml.json'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise RuntimeError(
            f"No se encontró la configuración de Azure ML en {config_path}. "
            "Crea ese archivo con endpoint y key." 
        ) from e


def predict_dishes_for_date(month: int, day: int) -> Dict[str, Any]:
    """Consulta el endpoint de Azure ML para predecir platos según mes/día."""
    cfg = _load_config()

    endpoint = cfg.get('endpoint')
    api_key = cfg.get('key')
    if not endpoint or not api_key:
        raise RuntimeError('Falta endpoint o key en backend/config/azure_ml.json')

    auth_header = cfg.get('auth_header', 'Authorization')
    auth_scheme = cfg.get('auth_scheme', 'Bearer')

    headers = {
        'Content-Type': 'application/json',
        auth_header: f"{auth_scheme} {api_key}"
    }

    # Payload que se envía al modelo. Ajusta según el schema del modelo.
    payload = {
        'month': month,
        'day': day
    }

    response = requests.post(endpoint, headers=headers, json=payload)
    if not response.ok:
        raise RuntimeError(
            f"Error al consultar Azure ML: {response.status_code} {response.text}"
        )

    return response.json()
