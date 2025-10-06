#!/usr/bin/env python3
"""
Script de prueba del sistema RAG
Ejecuta pruebas básicas para verificar que el sistema funciona correctamente
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

def test_rag_system():
    """Prueba básica del sistema RAG"""
    try:
        logger.info("🧪 Iniciando pruebas del sistema RAG")
        
        # Crear instancia del RAG manager
        rag_manager = RAGManager()
        
        # Verificar estado del sistema
        status = rag_manager.get_system_status()
        logger.info(f"Estado del sistema: {status}")
        
        if not status.get("rag_initialized", False):
            logger.warning("Sistema RAG no inicializado, inicializando...")
            success = rag_manager.initialize_rag_system()
            if not success:
                logger.error("❌ No se pudo inicializar el sistema RAG")
                return False
        
        # Pruebas de consulta
        test_queries = [
            "¿Cuáles son las políticas de calidad?",
            "¿Cómo funciona el proceso de mejora continua?",
            "¿Qué es un indicador de calidad?",
            "Hola, ¿cómo estás?",  # Consulta sin contexto específico
        ]
        
        logger.info("🔍 Ejecutando consultas de prueba...")
        
        for i, query in enumerate(test_queries, 1):
            logger.info(f"Consulta {i}: {query}")
            
            try:
                response, sources = rag_manager.generate_response(query)
                
                logger.info(f"✅ Respuesta: {response[:100]}...")
                if sources:
                    logger.info(f"📚 Fuentes: {', '.join(sources)}")
                else:
                    logger.info("📚 Sin fuentes específicas")
                
                # Buscar contexto solo
                context_docs = rag_manager.search_context(query, top_k=3)
                logger.info(f"🔍 Documentos relevantes encontrados: {len(context_docs)}")
                
            except Exception as e:
                logger.error(f"❌ Error en consulta {i}: {e}")
            
            logger.info("-" * 50)
        
        # Estadísticas finales
        final_status = rag_manager.get_system_status()
        logger.info("📊 Estadísticas finales:")
        logger.info(f"  - Vectores en Pinecone: {final_status.get('pinecone_vectors', 0)}")
        logger.info(f"  - Modelo de embeddings: {final_status.get('embedding_model', 'N/A')}")
        logger.info(f"  - Modelo de chat: {final_status.get('ollama_model', 'N/A')}")
        logger.info(f"  - URL de Ollama: {final_status.get('ollama_url', 'N/A')}")
        
        logger.info("✅ Pruebas completadas exitosamente!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error durante las pruebas: {e}")
        return False

def test_embedding_cache():
    """Prueba el sistema de caché de embeddings"""
    try:
        logger.info("🧪 Probando sistema de caché de embeddings")
        
        from embedding_service import EmbeddingService
        embedding_service = EmbeddingService()
        
        # Primera generación (debería crear caché)
        logger.info("Primera generación de embeddings...")
        embeddings1, docs1 = embedding_service.generate_embeddings(force_refresh=False)
        
        # Segunda generación (debería usar caché)
        logger.info("Segunda generación de embeddings (debería usar caché)...")
        embeddings2, docs2 = embedding_service.generate_embeddings(force_refresh=False)
        
        if len(embeddings1) == len(embeddings2) and len(docs1) == len(docs2):
            logger.info("✅ Sistema de caché funcionando correctamente")
            return True
        else:
            logger.warning("⚠️ Posible problema con el sistema de caché")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error probando caché: {e}")
        return False

def test_pinecone_connection():
    """Prueba la conexión con Pinecone"""
    try:
        logger.info("🧪 Probando conexión con Pinecone")
        
        from pinecone_service import PineconeService
        pinecone_service = PineconeService()
        
        stats = pinecone_service.get_index_stats()
        logger.info(f"✅ Conexión exitosa. Estadísticas: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error conectando con Pinecone: {e}")
        return False

def main():
    """Función principal de pruebas"""
    logger.info("🚀 Iniciando pruebas del sistema RAG completo")
    logger.info("=" * 60)
    
    # Cargar variables de entorno
    load_dotenv()
    
    all_tests_passed = True
    
    # Prueba 1: Conexión con Pinecone
    if not test_pinecone_connection():
        all_tests_passed = False
    
    logger.info("")
    
    # Prueba 2: Sistema de caché
    if not test_embedding_cache():
        all_tests_passed = False
    
    logger.info("")
    
    # Prueba 3: Sistema RAG completo
    if not test_rag_system():
        all_tests_passed = False
    
    logger.info("=" * 60)
    
    if all_tests_passed:
        logger.info("🎉 ¡Todas las pruebas pasaron exitosamente!")
        logger.info("Tu sistema RAG está listo para usar.")
    else:
        logger.error("❌ Algunas pruebas fallaron.")
        logger.error("Revisa los logs anteriores para más detalles.")
        sys.exit(1)

if __name__ == "__main__":
    main()