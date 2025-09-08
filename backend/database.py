from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

# La URL de tu base de datos PostgreSQL
DATABASE_URL = "postgresql://postgres:24631111@localhost/mi_proyecto" 

# Crea el motor de la base de datos
engine = create_engine(DATABASE_URL)

# Define la clase base declarativa
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