"""
Script de diagnóstico RAG - Identifica problemas en el flujo de chatbot
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import logging

# Configurar paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

async def main():
    print("🔍 DIAGNÓSTICO RAG - ANÁLISIS DEL SISTEMA")
    print("=" * 50)
    
    # 1. Verificar configuración básica
    print("\n1️⃣ VERIFICANDO CONFIGURACIÓN BÁSICA")
    
    # Variables críticas
    required_vars = [
        "DATABASE_URL", "GROQ_API_KEY", "GROQ_MODEL", 
        "PINECONE_API_KEY", "PINECONE_ENVIRONMENT", "EMBEDDING_MODEL"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            print(f"❌ {var}: NO CONFIGURADA")
        else:
            if "API_KEY" in var:
                print(f"✅ {var}: {value[:10]}...{value[-6:] if len(value) > 16 else 'corta'}")
            else:
                print(f"✅ {var}: {value}")
    
    if missing_vars:
        print(f"\n⚠️ Variables faltantes: {missing_vars}")
        return
    
    # 2. Verificar servicios
    print("\n2️⃣ VERIFICANDO SERVICIOS")
    
    try:
        # Importar servicios
        from services.groq_service import groq_service
        from services.embedding_service import embedding_service
        from services.pinecone_service import pinecone_service
        from database import get_db, SessionLocal
        from models import CustomChatbot, ChatbotDocument
        
        print("✅ Importaciones exitosas")
        
        # Test Groq
        print("\n🤖 TESTING GROQ SERVICE:")
        try:
            model_info = groq_service.get_model_info()
            print(f"✅ Modelo configurado: {model_info['model_name']}")
            
            # Test simple de generación
            test_response = await groq_service.generate_response(
                user_question="Hola, ¿cómo estás?",
                context_chunks=[],
                chatbot_name="Test"
            )
            
            if test_response.get("success"):
                print("✅ Groq responde correctamente")
                print(f"   Respuesta: {test_response.get('response', '')[:100]}...")
            else:
                print(f"❌ Error en Groq: {test_response.get('error', 'Desconocido')}")
                
        except Exception as e:
            print(f"❌ Error inicializando Groq: {str(e)}")
        
        # Test Embeddings
        print("\n🧠 TESTING EMBEDDING SERVICE:")
        try:
            model_info = embedding_service.get_model_info()
            print(f"✅ Modelo embeddings: {model_info['model_name']}")
            print(f"✅ Dimensión: {model_info['dimension']}")
            
            # Test de embedding
            test_embedding = await embedding_service.generate_single_embedding("Test de embedding")
            if test_embedding and len(test_embedding) == model_info['dimension']:
                print(f"✅ Embeddings funcionan correctamente (dim: {len(test_embedding)})")
            else:
                print(f"❌ Error generando embeddings: {len(test_embedding) if test_embedding else 0} dims")
                
        except Exception as e:
            print(f"❌ Error con embeddings: {str(e)}")
        
        # Test Pinecone
        print("\n📍 TESTING PINECONE SERVICE:")
        try:
            # Listar índices existentes
            existing_indexes = pinecone_service.pc.list_indexes()
            index_names = [idx.name for idx in existing_indexes] if existing_indexes else []
            
            print(f"✅ Conectado a Pinecone")
            print(f"📊 Índices existentes ({len(index_names)}): {index_names}")
            
            if len(index_names) >= 5:
                print("⚠️ PROBLEMA IDENTIFICADO: Tienes 5+ índices (límite del plan gratuito)")
                print("   Esto explica el error 403 al crear nuevos chatbots")
                print("   SOLUCIONES:")
                print("   - Eliminar índices no usados desde Pinecone Console")
                print("   - Usar un índice compartido con namespaces")
                
        except Exception as e:
            print(f"❌ Error conectando a Pinecone: {str(e)}")
        
        # 3. Verificar base de datos
        print("\n3️⃣ VERIFICANDO BASE DE DATOS")
        
        try:
            db = SessionLocal()
            
            # Contar chatbots y documentos
            chatbots_count = db.query(CustomChatbot).count()
            docs_count = db.query(ChatbotDocument).count()
            processed_docs = db.query(ChatbotDocument).filter(
                ChatbotDocument.is_processed == True
            ).count()
            
            print(f"✅ Conexión a BD exitosa")
            print(f"📊 Chatbots creados: {chatbots_count}")
            print(f"📄 Documentos subidos: {docs_count}")
            print(f"✅ Documentos procesados: {processed_docs}")
            
            if docs_count > 0 and processed_docs == 0:
                print("⚠️ PROBLEMA IDENTIFICADO: Ningún documento ha sido procesado")
                print("   Esto explica por qué RAG no funciona")
            
            # Examinar un chatbot específico si existe
            if chatbots_count > 0:
                sample_chatbot = db.query(CustomChatbot).first()
                print(f"\n🔍 ANALIZANDO CHATBOT: '{sample_chatbot.title}' (ID: {sample_chatbot.id})")
                print(f"   Índice Pinecone: {sample_chatbot.pinecone_index_name}")
                
                # Verificar documentos de este chatbot
                chatbot_docs = db.query(ChatbotDocument).filter(
                    ChatbotDocument.chatbot_id == sample_chatbot.id
                ).all()
                
                print(f"   Documentos: {len(chatbot_docs)}")
                for doc in chatbot_docs:
                    status = "✅ Procesado" if doc.is_processed else "❌ Pendiente"
                    print(f"   - {doc.original_filename}: {status} ({doc.chunks_count} chunks)")
                
                # Test de búsqueda en Pinecone si hay documentos procesados
                if any(doc.is_processed for doc in chatbot_docs):
                    print(f"\n🔍 TESTING BÚSQUEDA RAG EN CHATBOT '{sample_chatbot.title}':")
                    try:
                        # Generar embedding de prueba
                        test_query = "¿Qué información tienes?"
                        query_embedding = await embedding_service.generate_single_embedding(test_query)
                        
                        if query_embedding:
                            # Buscar en Pinecone
                            search_results = await pinecone_service.query_vectors(
                                index_name=sample_chatbot.pinecone_index_name,
                                query_vector=query_embedding,
                                top_k=3,
                                namespace=f"chatbot_{sample_chatbot.id}"
                            )
                            
                            print(f"✅ Búsqueda ejecutada")
                            print(f"📊 Resultados encontrados: {len(search_results)}")
                            
                            if search_results:
                                for i, result in enumerate(search_results):
                                    score = result.get('score', 0)
                                    metadata = result.get('metadata', {})
                                    text_preview = metadata.get('text', '')[:100] + "..." if metadata.get('text') else 'Sin texto'
                                    print(f"   {i+1}. Score: {score:.3f} | {text_preview}")
                                    
                                # Test completo RAG
                                print(f"\n🚀 TEST COMPLETO RAG:")
                                min_score = 0.7
                                relevant_chunks = [r for r in search_results if r.get('score', 0) >= min_score]
                                print(f"   Chunks relevantes (score >= {min_score}): {len(relevant_chunks)}")
                                
                                if relevant_chunks:
                                    # Generar respuesta con contexto
                                    response_data = await groq_service.generate_response(
                                        user_question=test_query,
                                        context_chunks=relevant_chunks,
                                        chatbot_name=sample_chatbot.title
                                    )
                                    
                                    if response_data.get("success"):
                                        print("✅ RAG FUNCIONANDO CORRECTAMENTE")
                                        print(f"   Respuesta: {response_data.get('response', '')[:200]}...")
                                    else:
                                        print(f"❌ Error generando respuesta RAG: {response_data.get('error')}")
                                else:
                                    print("⚠️ No hay chunks con score suficiente (podrías bajar min_score)")
                            else:
                                print("⚠️ No se encontraron resultados en Pinecone")
                                print("   Posibles causas:")
                                print("   - Índice vacío o namespace incorrecto")
                                print("   - Error en el procesamiento de documentos")
                        else:
                            print("❌ Error generando embedding de consulta")
                            
                    except Exception as e:
                        print(f"❌ Error en test RAG: {str(e)}")
            
            db.close()
            
        except Exception as e:
            print(f"❌ Error conectando a BD: {str(e)}")
        
        # 4. Recomendaciones
        print("\n4️⃣ RECOMENDACIONES")
        print("🔧 Para solucionar problemas identificados:")
        
        if len(index_names) >= 5:
            print("1. LÍMITE PINECONE:")
            print("   - Ve a https://app.pinecone.io y elimina índices no usados")
            print("   - O modifica el código para usar un índice compartido con namespaces")
        
        if docs_count > 0 and processed_docs == 0:
            print("2. DOCUMENTOS NO PROCESADOS:")
            print("   - Ejecuta el procesamiento manual: POST /api/chatbots/{id}/documents/process")
            print("   - Revisa logs del backend para errores en background tasks")
        
        print("3. CONFIGURACIÓN RECOMENDADA:")
        print("   - GROQ_MODEL=llama-3.1-8b-instant (ya configurado)")
        print("   - Bajar min_score de 0.7 a 0.5 para más resultados")
        print("   - USE_LITE_EMBEDDINGS=false para mejor calidad")
        
    except ImportError as e:
        print(f"❌ Error importando módulos: {str(e)}")
        print("   Asegúrate de ejecutar desde la carpeta backend con el venv activado")
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🏁 DIAGNÓSTICO COMPLETADO")

if __name__ == "__main__":
    asyncio.run(main())