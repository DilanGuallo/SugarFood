#!/usr/bin/env python3
"""
Servidor HTTP simple para servir el frontend de Azca Project
Ejecutar: python serve_frontend.py
"""

import http.server
import socketserver
import os
from pathlib import Path

# Puerto para el servidor frontend
FRONTEND_PORT = 8080

# Directorio del frontend
FRONTEND_DIR = Path(__file__).parent / "frontend"

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def end_headers(self):
        # Agregar headers CORS para desarrollo
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

    def do_GET(self):
        # Servir index.html por defecto cuando se accede a /
        if self.path == '/':
            self.path = '/index.html'
        return super().do_GET()

def run_frontend_server():
    """Inicia el servidor HTTP para el frontend"""
    try:
        with socketserver.TCPServer(("", FRONTEND_PORT), CustomHTTPRequestHandler) as httpd:
            print(f"🚀 Servidor frontend ejecutándose en: http://localhost:{FRONTEND_PORT}")
            print(f"📁 Sirviendo archivos desde: {FRONTEND_DIR}")
            print("💡 Presiona Ctrl+C para detener el servidor")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Servidor frontend detenido")
    except Exception as e:
        print(f"❌ Error al iniciar servidor frontend: {e}")

if __name__ == "__main__":
    print("🌐 Iniciando servidor frontend para Azca Project...")
    run_frontend_server()