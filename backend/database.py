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

# Leer cadena de conexión desde entorno o usar un valor por defecto local
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:24631111@localhost/mi_proyecto")

# Configurar engine con pool_pre_ping para reconexiones resilientes
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
