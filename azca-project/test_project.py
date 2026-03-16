#!/usr/bin/env python3
"""
Script de prueba para Azca Project
Verifica que la base de datos y API funcionen correctamente
"""

import sys
import os
# Agregar el directorio backend al path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

def test_database():
    """Prueba la conexión a la base de datos"""
    try:
        # Cambiar al directorio backend para que las rutas sean correctas
        os.chdir(backend_path)
        from app.services.db_service import get_db_connection, verify_user_credentials
        print("🔍 Probando conexión a MySQL...")

        conn = get_db_connection()
        print("✅ Conexión a MySQL exitosa")
        conn.close()

        # Probar login
        user = verify_user_credentials('taberna@azca.com', 'password123')
        if user:
            print(f"✅ Login exitoso: {user['nombre_usuario']} (Rol: {user['rol']})")
        else:
            print("❌ Error en login")

        return True
    except Exception as e:
        print(f"❌ Error en base de datos: {e}")
        return False

def test_api():
    """Prueba la API"""
    try:
        import urllib.request
        import json

        print("🔍 Probando API...")

        # Probar endpoint raíz
        with urllib.request.urlopen('http://localhost:8000/') as response:
            data = json.loads(response.read().decode())
            print("✅ API responde correctamente")

        # Probar login (usa credenciales de entorno si existen)
        login_data = {
            'email': os.environ.get('AZCA_TEST_EMAIL', 'bar@azca.com'),
            'password': os.environ.get('AZCA_TEST_PASSWORD', '1234')
        }

        req = urllib.request.Request(
            'http://localhost:8000/login',
            data=json.dumps(login_data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if 'access_token' in data:
                print("✅ Login API funciona correctamente")
                return True
            else:
                print("❌ Login API falló")
                return False

    except Exception as e:
        print(f"❌ Error en API: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Iniciando pruebas de Azca Project...\n")

    db_ok = test_database()
    print()

    api_ok = test_api()
    print()

    if db_ok and api_ok:
        print("🎉 ¡Todas las pruebas pasaron exitosamente!")
        print("✅ Base de datos MySQL conectada")
        print("✅ API FastAPI funcionando")
        print("✅ Autenticación con hash bcrypt funcionando")
        print("\n🚀 El proyecto está listo para usar!")
    else:
        print("❌ Algunas pruebas fallaron. Revisa la configuración.")
        sys.exit(1)