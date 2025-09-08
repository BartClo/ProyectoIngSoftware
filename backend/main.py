from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import Annotated
from pydantic import BaseModel # Esta línea es la que faltaba

# Importa las clases y funciones de los archivos que acabas de crear
from database import Base, engine, get_db
from models import User as UserModel

# Crea la aplicación FastAPI
app = FastAPI()

# Configuración de CORS para permitir la comunicación con el frontend
origins = [
    "http://localhost:5173",  # La dirección de tu frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de passlib para el hash de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Crea las tablas en la base de datos si no existen
Base.metadata.create_all(bind=engine)

# Pydantic model para los datos de registro
class UserCreate(BaseModel):
    email: str
    password: str

# Endpoint de registro
@app.post("/register/")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = pwd_context.hash(user.password)
    new_user = UserModel(email=user.email, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Usuario registrado exitosamente"}

# Endpoint de login
@app.post("/login/")
def login_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )
    return {"access_token": user.email, "token_type": "bearer"}