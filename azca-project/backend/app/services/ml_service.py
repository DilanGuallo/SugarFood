# Servicio para conectar con Azure ML Endpoint
import requests
import json

def predict_menu(image_url: str) -> dict:
    # Aquí va la lógica para llamar a tu endpoint de Azure ML
    # Ejemplo básico
    endpoint_url = "TU_ENDPOINT_AZURE_ML"
    api_key = "TU_API_KEY"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "image_url": image_url
    }
    
    response = requests.post(endpoint_url, headers=headers, json=data)
    return response.json()