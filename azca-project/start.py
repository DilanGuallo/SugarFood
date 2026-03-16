#!/usr/bin/env python3
"""
Script de inicio rápido para Azca Project
Inicia tanto el backend como el frontend automáticamente
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def start_backend():
    """Inicia el servidor backend"""
    print("🚀 Iniciando servidor backend...")
    backend_dir = Path(__file__).parent / "backend"
    os.chdir(backend_dir)

    try:
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ])
        print("✅ Backend iniciado en: http://localhost:8000")
        return process
    except Exception as e:
        print(f"❌ Error al iniciar backend: {e}")
        return None

def start_frontend():
    """Inicia el servidor frontend"""
    print("🌐 Iniciando servidor frontend...")
    project_dir = Path(__file__).parent
    os.chdir(project_dir)

    try:
        process = subprocess.Popen([sys.executable, "serve_frontend.py"])
        print("✅ Frontend iniciado en: http://localhost:8080")
        return process
    except Exception as e:
        print(f"❌ Error al iniciar frontend: {e}")
        return None

def main():
    print("🎯 Iniciando Azca Project...\n")

    # Iniciar backend
    backend_process = start_backend()
    if not backend_process:
        print("❌ No se pudo iniciar el backend")
        return

    time.sleep(2)  # Esperar a que el backend inicie

    # Iniciar frontend
    frontend_process = start_frontend()
    if not frontend_process:
        print("❌ No se pudo iniciar el frontend")
        backend_process.terminate()
        return

    print("\n🎉 ¡Ambos servidores iniciados exitosamente!")
    print("📱 Frontend: http://localhost:8080")
    print("🔧 Backend API: http://localhost:8000")
    print("📚 Documentación API: http://localhost:8000/docs")
    print("\n💡 Presiona Ctrl+C para detener ambos servidores")

    try:
        # Mantener los procesos ejecutándose
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\n👋 Deteniendo servidores...")
        backend_process.terminate()
        frontend_process.terminate()
        print("✅ Servidores detenidos")

if __name__ == "__main__":
    main()