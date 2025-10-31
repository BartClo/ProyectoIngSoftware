"""
Módulo de autenticación y autorización
Contiene funciones de JWT, validación de usuarios y middleware de seguridad
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Annotated, Optional
import bcrypt
import os

from database import get_db
from models import User as UserModel

# Configuración JWT
SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_ME_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/")

# --------------- Funciones de Hash de Contraseñas ------------------

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar contraseña usando bcrypt"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """Generar hash de contraseña usando bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


# --------------- Funciones JWT ------------------

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crear token JWT de acceso"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# --------------- Funciones de Usuario ------------------

def get_user_by_email(db: Session, email: str) -> Optional[UserModel]:
    """Obtener usuario por email"""
    return db.query(UserModel).filter(UserModel.email == email).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[UserModel]:
    """Autenticar usuario con email y contraseña"""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


# --------------- Dependencias FastAPI ------------------

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], 
    db: Session = Depends(get_db)
) -> UserModel:
    """Obtener usuario actual desde token JWT"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(
    current_user: Annotated[UserModel, Depends(get_current_user)]
) -> UserModel:
    """Obtener usuario actual activo (extensión para verificar estado activo)"""
    if hasattr(current_user, 'activo') and not current_user.activo:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user