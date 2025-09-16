from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
import os

<<<<<<< Updated upstream
# La URL de tu base de datos PostgreSQL
DATABASE_URL = "postgresql://postgres:24631111@localhost/mi_proyecto" 

# Crea el motor de la base de datos
engine = create_engine(DATABASE_URL)

# Define la clase base declarativa
=======
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
>>>>>>> Stashed changes
Base = declarative_base()

# Crea la sesión local de la base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Función para obtener la sesión de la base de datos (se usa en los endpoints)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()