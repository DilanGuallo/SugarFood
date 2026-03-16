# Servicio para Azure Document Intelligence
import requests

def extract_text_from_image(image_url: str) -> str:
    # Lógica para extraer texto de imagen usando Azure Document Intelligence
    endpoint = "TU_ENDPOINT_DOC_INTEL"
    key = "TU_KEY_DOC_INTEL"
    
    headers = {
        "Ocp-Apim-Subscription-Key": key,
        "Content-Type": "application/json"
    }
    
    data = {
        "url": image_url
    }
    
    response = requests.post(f"{endpoint}/formrecognizer/v2.1/layout/analyze", headers=headers, json=data)
    # Procesar respuesta...
    return "Texto extraído"