from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .models.schemas import MenuAzca, PredictionResponse, UsuarioCreate, Usuario, LoginRequest
from .services.db_service import get_menus, save_menu_azca, create_usuario, get_usuario_by_email, get_all_menus, get_menus_by_usuario, verify_user_credentials
from .services.doc_intel import analyze_menu_image
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

    # Guardar en DB
    save_menu_azca(menu_data, current_user['id'])

    return PredictionResponse(menu=menu_data, confidence=0.85)

@app.post("/menus")
async def create_menu(menu: MenuAzca, current_user: dict = Depends(verify_token)):
    save_menu_azca(menu, current_user['id'])
    return {"message": "Menú guardado"}