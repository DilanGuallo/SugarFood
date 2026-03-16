# Azca Project

Proyecto de Machine Learning para reconocimiento de menús usando Azure AI con **MySQL**.

## Estructura del Proyecto

```
/azca-project
├── /backend                 # API con FastAPI
│   ├── /app
│   │   ├── main.py          # Servidor FastAPI
│   │   ├── /services        # Lógica de negocio
│   │   │   ├── ml_service.py    # Azure ML
│   │   │   ├── doc_intel.py     # Document Intelligence
│   │   │   └── db_service.py    # PostgreSQL
│   │   └── /models          # Modelos Pydantic
│   │       └── schemas.py
│   ├── /config              # Configuraciones
│   │   └── connections.json # Claves secretas
│   ├── init_db.sql          # Script para crear tablas
│   ├── requirements.txt
│   └── .env
├── /frontend                # Interfaz web
│   ├── index.html
│   ├── /css
│   │   └── style.css
│   └── /js
│       ├── main.js          # Lógica de UI
│       └── api_client.js    # Llamadas a API
├── .gitignore
└── README.md
```

## Configuración de Base de Datos

1. Instala MySQL y crea una base de datos llamada `azca_db`
2. Ejecuta el script `backend/init_db.sql` en tu base de datos MySQL
3. **Opcional**: Ejecuta `backend/sample_data.sql` para cargar datos de prueba
4. Actualiza `backend/config/connections.json` con tus credenciales de MySQL

## Datos de Prueba

Para probar el sistema, puedes usar estos usuarios de ejemplo (las contraseñas están hasheadas con bcrypt):

### Usuarios de Restaurantes (rol: 'Bar')
- **La Taberna de Azca** - taberna@azca.com / password123
- **El Rincón Castellano** - rincon@azca.com / password123  
- **Café del Prado** - cafe@azca.com / password123

### Usuarios Clientes (rol: 'Cliente')
- **María González** - maria@email.com / password123
- **Carlos Rodríguez** - carlos@email.com / password123
- **Ana López** - ana@email.com / password123

Los datos incluyen 3 menús completos con todos los platos, precios y detalles.

## 🚀 Inicio Rápido

### Opción 1: Inicio Automático (Más Fácil)
```bash
python start.py
```
Este comando inicia tanto el backend como el frontend automáticamente.

### Opción 2: Servidor Completo Manual
```bash
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
python serve_frontend.py
```
Luego abre: http://localhost:8080

### Opción 3: Solo Backend (para desarrollo)
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Abre `frontend/index.html` directamente en el navegador.

### 4. Verificar Instalación
```bash
python test_project.py
```

Este script verifica que la base de datos y API funcionen correctamente.

## 🔐 Credenciales de Prueba

### Usuarios de Restaurantes (rol: 'Bar')
- **La Taberna de Azca** - taberna@azca.com / password123
- **El Rincón Castellano** - rincon@azca.com / password123
- **Café del Prado** - cafe@azca.com / password123

### Usuarios Clientes (rol: 'Cliente')
- **María González** - maria@email.com / password123
- **Carlos Rodríguez** - carlos@email.com / password123
- **Ana López** - ana@email.com / password123

## 📡 API Endpoints

- `GET /` - Estado de la API
- `POST /register` - Registrar usuario
- `POST /login` - Iniciar sesión
- `GET /menus` - Obtener menús (requiere token)
- `POST /predict-menu` - Procesar imagen de menú (requiere token)

## API Endpoints

- `POST /register` - Registrar usuario
- `POST /login` - Iniciar sesión
- `GET /menus` - Obtener menús (requiere token)
- `POST /predict-menu` - Procesar imagen de menú (requiere token)

## Campos del Modelo IA

El modelo extrae 13 campos de las fotos de menús:
- menu_del_dia, precio, platos, bar_rest, dia, fecha, telefono, aperitivo
- primeros[], segundos[], complemento[], postre[], menu_infantil[]

## Estructura de Base de Datos

### Tabla usuarios_azca
- id, nombre_usuario, email, password, rol ('Bar' o 'Cliente'), telefono

### Tabla menus_azca
- id, menu_del_dia, precio, platos, bar_rest, dia, fecha, telefono, aperitivo, fecha_creacion, usuario_id

### Tablas de platos (relacionadas con menus_azca)
- primeros_platos: id, menu_id, nombre
- segundos_platos: id, menu_id, nombre
- complementos: id, menu_id, nombre
- postres: id, menu_id, nombre
- menus_infantiles: id, menu_id, nombre