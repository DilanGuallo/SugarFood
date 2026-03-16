from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class MenuItem(BaseModel):
    name: str
    description: Optional[str] = None

class Menu(BaseModel):
    name: str
    price: float
    items: List[MenuItem]

# Nuevo modelo para menú extraído por IA
class MenuAzca(BaseModel):
    menu_del_dia: Optional[str] = None
    precio: Optional[str] = None
    platos: Optional[str] = None
    bar_rest: Optional[str] = None
    dia: Optional[str] = None
    fecha: Optional[date] = None
    telefono: Optional[str] = None
    aperitivo: Optional[str] = None
    primeros: Optional[List[str]] = []
    segundos: Optional[List[str]] = []
    complemento: Optional[List[str]] = []
    postre: Optional[List[str]] = []
    menu_infantil: Optional[List[str]] = []

class PredictionRequest(BaseModel):
    image_url: str

class PredictionResponse(BaseModel):
    menu: MenuAzca
    confidence: float

# Modelo para usuario
class UsuarioBase(BaseModel):
    nombre_usuario: str
    email: str
    rol: str  # 'Bar' o 'Cliente'
    telefono: Optional[str] = None

class UsuarioCreate(UsuarioBase):
    password: str

class Usuario(UsuarioBase):
    id: int

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: str
    password: str