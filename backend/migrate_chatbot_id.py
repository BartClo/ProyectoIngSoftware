"""
Migración para agregar chatbot_id a la tabla conversations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_add_chatbot_id():
    """Agregar columna chatbot_id a la tabla conversations"""
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL no encontrada en las variables de entorno")
        return False
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Verificar si la columna ya existe
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'conversations' 
                AND column_name = 'chatbot_id'
            """))
            
            if result.fetchone():
                logger.info("✅ La columna chatbot_id ya existe en conversations")
                return True
            
            # Agregar la columna chatbot_id
            logger.info("🔧 Agregando columna chatbot_id a la tabla conversations...")
            
            conn.execute(text("""
                ALTER TABLE conversations 
                ADD COLUMN chatbot_id INTEGER REFERENCES custom_chatbots(id) ON DELETE SET NULL
            """))
            
            conn.commit()
            logger.info("✅ Columna chatbot_id agregada exitosamente")
            
            # Verificar que se agregó correctamente
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'conversations' 
                AND column_name = 'chatbot_id'
            """))
            
            column_info = result.fetchone()
            if column_info:
                logger.info(f"✅ Verificación: {column_info}")
                return True
            else:
                logger.error("❌ Error: No se pudo verificar la creación de la columna")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error durante la migración: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando migración de base de datos...")
    success = migrate_add_chatbot_id()
    if success:
        print("✅ Migración completada exitosamente")
    else:
        print("❌ Error en la migración")
        sys.exit(1)