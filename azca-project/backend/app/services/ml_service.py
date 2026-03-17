# Servicio para conectar con un endpoint de Azure Machine Learning (Online Endpoint)

import datetime
import json
from pathlib import Path
from typing import Any, Dict

import requests


def _load_config() -> Dict[str, Any]:
    """Carga la configuración de Azure ML desde connections.json."""
    config_path = Path(__file__).resolve().parents[2] / 'config' / 'connections.json'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            full_config = json.load(f)
        return full_config.get('azure_ml', {})
    except FileNotFoundError as e:
        raise RuntimeError(
            f"No se encontró la configuración en {config_path}. "
            "Asegúrate de que existe la sección 'azure_ml'." 
        ) from e


def predict_dishes_for_date(month: int, day: int) -> Dict[str, Any]:
    """Consulta el endpoint de Azure ML para predecir platos según mes/día."""
    cfg = _load_config()

    endpoint = cfg.get('endpoint')
    api_key = cfg.get('api_key') or cfg.get('key')
    if not endpoint or not api_key:
        raise RuntimeError('Falta endpoint o api_key en la sección "azure_ml" de backend/config/connections.json')

    auth_header = cfg.get('auth_header', 'Authorization')
    auth_scheme = cfg.get('auth_scheme', 'Bearer')

    headers = {
        'Content-Type': 'application/json',
        auth_header: f"{auth_scheme} {api_key}"
    }

    # Payload que se envía al modelo. Ajusta según el schema del modelo.
    # Azure ML Online Endpoints suelen esperar un objeto con key "input_data".
    payload = {
        'input_data': [
            {
                'month': month,
                'day': day
            }
        ]
    }

    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=15)
        if response.ok:
            return response.json()
        else:
            raise RuntimeError(f"Error al consultar Azure ML: {response.status_code} {response.text}")
    except Exception as e:
        # En caso de fallo con Azure ML, devolvemos una recomendación simple basada en la fecha
        print(f"[WARN] Azure ML no respondió correctamente: {e}")
        weekday = datetime.date(2024, month, day).strftime('%A')
        base_recs = {
            'Monday': ['Menú energético para empezar la semana', 'Prueba el plato del chef del lunes'],
            'Tuesday': ['Martes de tapas: elige tu favorito', 'Hoy recomendamos platos ligeros y sabrosos'],
            'Wednesday': ['Delicias de mitad de semana', 'Sopas y guisos recomendados'],
            'Thursday': ['Jueves de sabores fuertes', 'Prueba nuestro especial de la casa'],
            'Friday': ['Viernes de fiesta: cócteles y platos especiales', 'Menú del chef para el fin de semana'],
            'Saturday': ['Sábado para compartir: platos para todos', 'Propuesta de mariscos y platos frescos'],
            'Sunday': ['Domingo tranquilo: platos caseros reconfortantes', 'Menú familiar para compartir']
        }
        return base_recs.get(weekday, ['Prueba algo nuevo hoy', 'Consulta nuestras recomendaciones'])
