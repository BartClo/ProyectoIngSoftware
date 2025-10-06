from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# Cargar variables de entorno desde .env si existe
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

# Leer cadena de conexión desde entorno
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Fallback para desarrollo local con SQLite
    DATABASE_URL = "sqlite:///./chatbot.db"
    print("⚠️ DATABASE_URL no configurada, usando SQLite local: chatbot.db")

# Configurar engine con parámetros específicos según el tipo de base de datos
if DATABASE_URL.startswith("sqlite"):
    # Configuración para SQLite
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False},  # Para SQLite
        echo=False  # Cambiar a True para ver consultas SQL en desarrollo
    )
else:
    # Configuración para PostgreSQL u otras bases de datos
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
