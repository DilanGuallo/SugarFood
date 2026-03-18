from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .models.schemas import (
    MenuAzca,
    PredictionResponse,
    UsuarioCreate,
    Usuario,
    LoginRequest,
    RatingCreate,
)
from .services.db_service import (
    get_menus,
    save_menu_azca,
    create_usuario,
    get_usuario_by_email,
    get_all_menus,
    get_menus_by_usuario,
    verify_user_credentials,
)
from .services.doc_intel import analyze_menu_image
from .services.ml_service import predict_dishes_for_date, recommend_dishes_from_menu
import jwt
import datetime

app = FastAPI(title="Azca Project API", version="1.0.0")

# CORS para frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los origenes durante desarrollo
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
        raise HTTPException(status_code=401, detail="Token invalido")


@app.get("/")
async def root():
    return {"message": "Bienvenido a Azca Project API"}


@app.post("/register")
async def register_user(user: UsuarioCreate):
    existing_user = get_usuario_by_email(user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email ya registrado")

    user_id = create_usuario(user)
    return {"message": "Usuario registrado", "user_id": user_id}


@app.post("/login")
async def login_user(login: LoginRequest):
    user = verify_user_credentials(login.email, login.password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales invalidas")

    access_token = create_access_token({"sub": user["email"], "rol": user["rol"], "id": user["id"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user["id"], "nombre": user["nombre_usuario"], "rol": user["rol"]},
    }


@app.get("/menus")
async def get_menus_endpoint(current_user: dict = Depends(verify_token)):
    if current_user["rol"] == "Bar":
        menus = get_menus_by_usuario(current_user["id"])
    else:
        menus = get_all_menus()
    return {"menus": menus}


@app.post("/predict-menu")
async def predict_menu(file: UploadFile = File(...), current_user: dict = Depends(verify_token)):
    file_bytes = await file.read()

    try:
        menu_data = analyze_menu_image(file_bytes, file.content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al analizar el menu: {e}")

    return PredictionResponse(menu=menu_data, confidence=0.85)


@app.post("/menus")
async def create_menu(menu: MenuAzca, current_user: dict = Depends(verify_token)):
    save_menu_azca(menu, current_user["id"])
    return {"message": "Menu guardado"}


@app.get("/recommend-menu")
async def recommend_menu(current_user: dict = Depends(verify_token)):
    """Devuelve una recomendacion de platos usando heuristicas y ML."""
    today = datetime.datetime.utcnow()

    try:
        if current_user["rol"] == "Bar":
            menus = get_menus_by_usuario(current_user["id"])
        else:
            menus = get_all_menus()

        primeros = []
        segundos = []
        postres = []

        if menus:
            for menu in menus:
                if hasattr(menu, "dict"):
                    menu_dict = menu.dict()
                else:
                    menu_dict = menu if isinstance(menu, dict) else {}

                primeros.extend(menu_dict.get("primeros", []) or [])
                segundos.extend(menu_dict.get("segundos", []) or [])
                postres.extend(menu_dict.get("postre", []) or [])

        primeros = list(dict.fromkeys([p for p in primeros if p and str(p).strip()]))
        segundos = list(dict.fromkeys([s for s in segundos if s and str(s).strip()]))
        postres = list(dict.fromkeys([p for p in postres if p and str(p).strip()]))

        recommendation = recommend_dishes_from_menu(
            primeros=primeros,
            segundos=segundos,
            postres=postres,
            month=today.month,
            day=today.day,
        )

        recommendation["menus_available"] = len(menus)
        recommendation["dishes_count"] = {
            "primeros": len(primeros),
            "segundos": len(segundos),
            "postres": len(postres),
        }

        return recommendation

    except Exception as e:
        print(f"[ERROR] Error en recommend_menu: {e}")
        return {
            "error": str(e),
            "date": f"{today.strftime('%A')}, {today.day}/{today.month}",
            "message": "Recomendacion no disponible. Por favor intenta mas tarde.",
        }


@app.post("/menus/{menu_id}/ratings")
async def create_rating(menu_id: int, rating_data: RatingCreate, current_user=Depends(verify_token)):
    """Crear una nueva valoracion para un menu."""
    from .services.db_service import save_rating

    try:
        puntuacion = rating_data.puntuacion
        resena = (rating_data.resena or "").strip()

        if not puntuacion or puntuacion < 1 or puntuacion > 5:
            raise HTTPException(status_code=400, detail="Puntuacion debe estar entre 1 y 5")

        usuario_id = current_user.get("id")
        if not usuario_id:
            raise HTTPException(status_code=401, detail="Usuario no autenticado")

        save_rating(menu_id, usuario_id, puntuacion, resena)
        return {"message": "Valoracion guardada exitosamente", "menu_id": menu_id}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en create_rating: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/menus/{menu_id}/ratings")
async def get_ratings(menu_id: int):
    """Obtener todas las valoraciones de un menu."""
    from .services.db_service import get_ratings_by_menu, get_average_rating

    try:
        ratings = get_ratings_by_menu(menu_id)
        average = get_average_rating(menu_id)

        return {
            "menu_id": menu_id,
            "ratings": ratings,
            "average_rating": average,
        }
    except Exception as e:
        print(f"Error en get_ratings: {e}")
        raise HTTPException(status_code=500, detail=str(e))
