from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .models.schemas import MenuAzca, PredictionResponse, UsuarioCreate, Usuario, LoginRequest, RatingCreate
from .services.db_service import get_menus, save_menu_azca, create_usuario, get_usuario_by_email, get_all_menus, get_menus_by_usuario, verify_user_credentials
from .services.doc_intel import analyze_menu_image
from .services.ml_service import predict_dishes_for_date, recommend_dishes_from_menu
import jwt
import datetime

app = FastAPI(title="Azca Project API", version="1.0.0")

# CORS para frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes durante desarrollo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "tu_clave_secreta_aqui"  # Cambia por una clave segura
security = HTTPBearer()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

@app.get("/")
async def root():
    return {"message": "Bienvenido a Azca Project API"}

@app.post("/register")
async def register_user(user: UsuarioCreate):
    # Verificar si el email ya existe
    existing_user = get_usuario_by_email(user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email ya registrado")

    user_id = create_usuario(user)
    return {"message": "Usuario registrado", "user_id": user_id}

@app.post("/login")
async def login_user(login: LoginRequest):
    user = verify_user_credentials(login.email, login.password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    access_token = create_access_token({"sub": user['email'], "rol": user['rol'], "id": user['id']})
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": user['id'], "nombre": user['nombre_usuario'], "rol": user['rol']}}

@app.get("/menus")
async def get_menus_endpoint(current_user: dict = Depends(verify_token)):
    if current_user['rol'] == 'Bar':
        menus = get_menus_by_usuario(current_user['id'])
    else:
        menus = get_all_menus()
    return {"menus": menus}

@app.post("/predict-menu")
async def predict_menu(file: UploadFile = File(...), current_user: dict = Depends(verify_token)):
    # Leer bytes del archivo subido
    file_bytes = await file.read()

    try:
        menu_data = analyze_menu_image(file_bytes, file.content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al analizar el menú: {e}")

    return PredictionResponse(menu=menu_data, confidence=0.85)

@app.post("/menus")
async def create_menu(menu: MenuAzca, current_user: dict = Depends(verify_token)):
    save_menu_azca(menu, current_user['id'])
    return {"message": "Menú guardado"}

@app.get("/recommend-menu")
async def recommend_menu(current_user: dict = Depends(verify_token)):
    """Devuelve una recomendación de platos (según mes/día y menú disponible) usando heurísticas y ML."""
    today = datetime.datetime.utcnow()
    
    try:
        # Obtener el menú del usuario (si es restaurante)
        if current_user['rol'] == 'Bar':
            menus = get_menus_by_usuario(current_user['id'])
        else:
            menus = get_all_menus()
        
        # Si hay menús, extraer los platos disponibles
        primeros = []
        segundos = []
        postres = []
        
        if menus:
            for menu in menus:
                # Convertir MenuAzca a dict si es necesario
                if hasattr(menu, 'dict'):
                    menu_dict = menu.dict()
                else:
                    menu_dict = menu if isinstance(menu, dict) else {}
                
                # Agregar platos a las listas
                primeros.extend(menu_dict.get('primeros', []) or [])
                segundos.extend(menu_dict.get('segundos', []) or [])
                postres.extend(menu_dict.get('postre', []) or [])
        
        # Remover duplicados manteniendo orden
        primeros = list(dict.fromkeys([p for p in primeros if p and str(p).strip()]))
        segundos = list(dict.fromkeys([s for s in segundos if s and str(s).strip()]))
        postres = list(dict.fromkeys([p for p in postres if p and str(p).strip()]))
        
        # Obtener recomendaciones del modelo de ML
        recommendation = recommend_dishes_from_menu(
            primeros=primeros,
            segundos=segundos,
            postres=postres,
            month=today.month,
            day=today.day
        )
        
        # Agregar información meta
        recommendation['menus_available'] = len(menus)
        recommendation['dishes_count'] = {
            'primeros': len(primeros),
            'segundos': len(segundos),
            'postres': len(postres)
        }
        
        return recommendation
        
    except Exception as e:
        print(f"[ERROR] Error en recommend_menu: {e}")
        # Devolver al menos algo de información en caso de error
        return {
            'error': str(e),
            'date': f"{today.strftime('%A')}, {today.day}/{today.month}",
            'message': 'Recomendación no disponible. Por favor intenta más tarde.'
        }

# Endpoints para ratings/valoraciones
@app.post("/menus/{menu_id}/ratings")
async def create_rating(menu_id: int, rating_data: RatingCreate, current_user = Depends(verify_token)):
    """Crear una nueva valoración para un menú"""
    from .services.db_service import save_rating
    
    try:
        puntuacion = rating_data.puntuacion
        resena = rating_data.resena
        
        # Validar puntuación (el modelo ya lo hace, pero por si acaso)
        if not puntuacion or puntuacion < 1 or puntuacion > 5:
            raise HTTPException(status_code=400, detail="Puntuación debe estar entre 1 y 5")
        
        # Obtener usuario_id del token
        usuario_id = current_user.get("id")
        
        # Guardar la valoración
        success = save_rating(menu_id, usuario_id, puntuacion, resena)
        if success:
            return {"message": "Valoración guardada exitosamente", "menu_id": menu_id}
        else:
            raise HTTPException(status_code=500, detail="Error guardando la valoración")
    except Exception as e:
        print(f"Error en create_rating: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/menus/{menu_id}/ratings")
async def get_ratings(menu_id: int):
    """Obtener todas las valoraciones de un menú"""
    from .services.db_service import get_ratings_by_menu, get_average_rating
    
    try:
        ratings = get_ratings_by_menu(menu_id)
        average = get_average_rating(menu_id)
        
        return {
            "menu_id": menu_id,
            "ratings": ratings,
            "average_rating": average
        }
    except Exception as e:
        print(f"Error en get_ratings: {e}")
        raise HTTPException(status_code=500, detail=str(e))