# Servicio para conectar con un endpoint de Azure Machine Learning (Online Endpoint)

import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

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


def _get_day_recommendations(month: int, day: int, weekday: str) -> Dict[str, Any]:
    """Devuelve recomendaciones base según el día de la semana y fecha."""
    base_recs = {
        'Monday': {
            'theme': 'Lunes energético',
            'description': 'Menú para empezar la semana con energía',
            'dish_hint': 'proteína, potaje',
            'suggested_type': 'primeros'  # Recomendamos primeros en lunes
        },
        'Tuesday': {
            'theme': 'Martes de tradición',
            'description': 'Platos clásicos y reconfortantes',
            'dish_hint': 'legumbres, estofado',
            'suggested_type': 'segundos'
        },
        'Wednesday': {
            'theme': 'Miércoles medio',
            'description': 'Equilibrio perfecto de sabores',
            'dish_hint': 'sopas, cremas, verduras',
            'suggested_type': 'primeros'
        },
        'Thursday': {
            'theme': 'Jueves fuerte',
            'description': 'Platos con sabores intensos',
            'dish_hint': 'carnes, especias, salsa',
            'suggested_type': 'segundos'
        },
        'Friday': {
            'theme': 'Viernes de festa',
            'description': 'Celebremos el fin de semana',
            'dish_hint': 'mariscos, pescado, especialidades',
            'suggested_type': 'segundos'
        },
        'Saturday': {
            'theme': 'Sábado para compartir',
            'description': 'Platos abundantes y para compartir',
            'dish_hint': 'arraiz, paella, estofado',
            'suggested_type': 'segundos'
        },
        'Sunday': {
            'theme': 'Domingo casero',
            'description': 'Comida familiar reconfortante',
            'dish_hint': 'legumbres, potajes, cocidos',
            'suggested_type': 'primeros'
        }
    }
    return base_recs.get(weekday, {
        'theme': 'Recomendación del día',
        'description': 'Prueba algo nuevo',
        'dish_hint': 'sorpresa',
        'suggested_type': 'segundos'
    })


def _build_default_recommendations() -> Dict[str, Any]:
    """Devuelve recomendaciones por defecto cuando no hay platos disponibles."""
    return {
        'first_course': 'Ensalada mixta de la casa',
        'main_course': 'Pollo asado con patatas',
        'dessert': 'Flan casero',
        'reasoning': ['Sugerencia por defecto mientras se carga la recomendacion del dia']
    }


def recommend_dishes_from_menu(
    primeros: Optional[List[str]] = None,
    segundos: Optional[List[str]] = None,
    postres: Optional[List[str]] = None,
    month: int = None,
    day: int = None
) -> Dict[str, Any]:
    """
    Recomienda platos del menú basado en la fecha y disponibilidad.
    Si Azure ML no funciona, usa heurísticas basadas en el día de la semana.
    """
    if month is None or day is None:
        today = datetime.datetime.utcnow()
        month = today.month
        day = today.day
    
    # Obtener información del día
    try:
        current_date = datetime.date(datetime.datetime.utcnow().year, month, day)
        weekday_num = current_date.weekday()  # 0=Monday, 6=Sunday
        weekday_name = current_date.strftime('%A')
    except ValueError:
        # Si la fecha es inválida, usar hoy
        today = datetime.datetime.utcnow()
        current_date = today.date()
        weekday_num = current_date.weekday()
        weekday_name = current_date.strftime('%A')
    
    day_info = _get_day_recommendations(month, day, weekday_name)
    
    # Preparar listas de platos
    primeros = primeros or []
    segundos = segundos or []
    postres = postres or []
    
    # Filtrar strings vacíos
    primeros = [p for p in primeros if p and p.strip()]
    segundos = [s for s in segundos if s and s.strip()]
    postres = [p for p in postres if p and p.strip()]
    
    recommendations = {
        'date': f"{weekday_name}, {day}/{month}",
        'theme': day_info.get('theme', 'Recomendación'),
        'description': day_info.get('description', 'Elige tu plato favorito'),
        'weekday': weekday_name,
        'recommended_dishes': {}
    }
    
    # Intentar conectar con Azure ML
    try:
        ml_recommendation = predict_dishes_for_date(
            month, day, primeros, segundos, postres
        )
        if ml_recommendation:
            recommendations['recommended_dishes'] = ml_recommendation
            recommendations['ml_used'] = True
            return recommendations
    except Exception as e:
        print(f"[WARN] Azure ML no disponible: {e}. Usando recomendaciones heurísticas.")
    
    # Fallback: Recomendaciones heurísticas basadas en el día
    suggestions = _get_heuristic_recommendations(
        weekday_num, primeros, segundos, postres, day_info
    )
    if not any([suggestions.get('first_course'), suggestions.get('main_course'), suggestions.get('dessert')]):
        suggestions = _build_default_recommendations()
    recommendations['recommended_dishes'] = suggestions
    recommendations['ml_used'] = False
    
    return recommendations


def _get_heuristic_recommendations(
    weekday_num: int,
    primeros: List[str],
    segundos: List[str],
    postres: List[str],
    day_info: Dict[str, Any]
) -> Dict[str, Any]:
    """Hace recomendaciones heurísticas basadas en el día de la semana."""
    recommendations = {
        'first_course': None,
        'main_course': None,
        'dessert': None,
        'reasoning': []
    }
    
    suggested_type = day_info.get('suggested_type', 'segundos')
    
    # Lunes, Miércoles: Recomendamos primeros (potajes, sopas, legumbres)
    if suggested_type == 'primeros' and primeros:
        # Buscar platos con palabras clave
        keywords = ['sopa', 'potaje', 'fabada', 'lentejas', 'garbanzos', 'caldo', 'crema']
        recommended = next(
            (p for p in primeros if any(k.lower() in p.lower() for k in keywords)),
            primeros[0]
        )
        recommendations['first_course'] = recommended
        recommendations['reasoning'].append(f"Perfecto para {day_info.get('theme', 'hoy')}: {day_info.get('dish_hint')}")
    elif primeros:
        recommendations['first_course'] = primeros[0]
    
    # Martes, Jueves, Viernes, Sábado: Recomendamos segundos (carnes, pescados, especiales)
    if suggested_type == 'segundos' and segundos:
        # Buscar según el día
        if weekday_num == 1:  # Martes: Clásicos
            keywords = ['estofado', 'guiso', 'salsa', 'tradicional']
        elif weekday_num == 3:  # Jueves: Intensos
            keywords = ['asado', 'frito', 'especial', 'casa']
        elif weekday_num == 4:  # Viernes: Mariscos/Pescado
            keywords = ['salmón', 'bacalao', 'marinero', 'marisco', 'gambas', 'pescado']
        elif weekday_num == 5:  # Sábado: Abundantes
            keywords = ['arroz', 'paella', 'relleno', 'confitado', 'abundant']
        else:
            keywords = day_info.get('dish_hint', '').split(',')
        
        recommended = next(
            (p for p in segundos if any(k.lower() in p.lower() for k in keywords)),
            segundos[0]
        )
        recommendations['main_course'] = recommended
        recommendations['reasoning'].append(f"Sugerencia para {day_info.get('theme')}")
    elif segundos:
        recommendations['main_course'] = segundos[0]
    
    # Postre: Preferir según el ánimo del día
    if postres:
        # Los fines de semana: postres más elaborados
        if weekday_num >= 5:  # Sábado o domingo
            keywords = ['tarta', 'chocolate', 'helado', 'flan', 'brownie']
        else:
            keywords = ['arroz con leche', 'fruta', 'sorbete']
        
        recommended = next(
            (p for p in postres if any(k.lower() in p.lower() for k in keywords)),
            postres[0]
        )
        recommendations['dessert'] = recommended
    
    return recommendations


def predict_dishes_for_date(
    month: int,
    day: int,
    primeros: Optional[List[str]] = None,
    segundos: Optional[List[str]] = None,
    postres: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]:
    """Consulta el endpoint de Azure ML para predecir platos según mes/día/platos disponibles."""
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

    # Payload que se envía al modelo
    # Incluye mes, día y los platos disponibles para que el modelo haga mejor predicción
    payload = {
        'input_data': [
            {
                'month': month,
                'day': day,
                'primeros': primeros or [],
                'segundos': segundos or [],
                'postres': postres or []
            }
        ]
    }

    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=15)
        if response.ok:
            result = response.json()
            print(f"[INFO] Azure ML respondió: {result}")
            if isinstance(result, dict):
                if 'recommended_dishes' in result and isinstance(result['recommended_dishes'], dict):
                    return result['recommended_dishes']
                if 'recommendation' in result:
                    return result['recommendation']
                if any(key in result for key in ['first_course', 'main_course', 'dessert']):
                    return result
            return result
        else:
            print(f"[WARN] Azure ML error: {response.status_code} {response.text}")
            return None
    except requests.exceptions.Timeout:
        print("[WARN] Timeout al conectar con Azure ML")
        return None
    except Exception as e:
        print(f"[WARN] Error conectando con Azure ML: {e}")
        return None

