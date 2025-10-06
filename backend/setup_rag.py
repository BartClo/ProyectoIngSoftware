#!/usr/bin/env python3
"""
Script de inicialización del sistema RAG
Este script prepara el sistema RAG por primera vez
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Agregar el directorio backend al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_manager import RAGManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Verifica que las variables de entorno estén configuradas"""
    load_dotenv()
    
    required_vars = [
        "OLLAMA_BASE_URL",
        "OLLAMA_MODEL",
        "PINECONE_API_KEY",
        "DATABASE_URL"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Variables de entorno faltantes: {missing_vars}")
        logger.error("Por favor, configura estas variables en tu archivo .env")
        return False
    
    logger.info("✓ Variables de entorno configuradas correctamente")
    return True

def check_documents():
    """Verifica que existan documentos para procesar"""
    context_dir = os.path.join(os.path.dirname(__file__), "context_docs")
    
    if not os.path.exists(context_dir):
        logger.error(f"Directorio de documentos no encontrado: {context_dir}")
        return False
    
    pdf_files = [f for f in os.listdir(context_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        logger.error(f"No se encontraron archivos PDF en {context_dir}")
        logger.error("Por favor, agrega los documentos PDF que quieres incluir en el RAG")
        return False
    
    logger.info(f"✓ Encontrados {len(pdf_files)} documentos PDF:")
    for pdf in pdf_files:
        logger.info(f"  - {pdf}")
    
    return True

def initialize_rag():
    """Inicializa el sistema RAG"""
    try:
        logger.info("Iniciando configuración del sistema RAG...")
        
        # Crear instancia del RAG manager
        rag_manager = RAGManager()
        
        # Inicializar el sistema
        logger.info("Procesando documentos y generando embeddings...")
        logger.info("(Esto puede tomar varios minutos la primera vez)")
        
        success = rag_manager.initialize_rag_system(force_refresh=True)
        
        if success:
            # Obtener estadísticas
            status = rag_manager.get_system_status()
            
            logger.info("🎉 ¡Sistema RAG inicializado exitosamente!")
            logger.info(f"✓ Vectores almacenados en Pinecone: {status.get('pinecone_vectors', 0)}")
            logger.info(f"✓ Modelo de embeddings: {status.get('embedding_model', 'N/A')}")
            logger.info(f"✓ Modelo de chat: {status.get('ollama_model', 'N/A')}")
            logger.info(f"✓ URL de Ollama: {status.get('ollama_url', 'N/A')}")
            logger.info(f"✓ Índice de Pinecone: {status.get('pinecone_index', 'N/A')}")
            
            return True
        else:
            logger.error("❌ Error al inicializar el sistema RAG")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error durante la inicialización: {e}")
        return False

def main():
    """Función principal"""
    logger.info("🚀 Iniciando configuración del sistema RAG para Chatbot USS")
    logger.info("=" * 60)
    
    # Verificar entorno
    if not check_environment():
        sys.exit(1)
    
    # Verificar documentos
    if not check_documents():
        sys.exit(1)
    
    # Inicializar RAG
    if not initialize_rag():
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("✅ Configuración completada exitosamente!")
    logger.info("Ya puedes iniciar tu servidor FastAPI con: uvicorn main:app --reload")
    logger.info("El sistema RAG estará listo para responder consultas basadas en tus documentos.")

if __name__ == "__main__":
    main()