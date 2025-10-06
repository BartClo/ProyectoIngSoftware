# rag_manager.py
import os
import logging
from typing import List, Dict, Optional, Tuple
import numpy as np
from embedding_service import EmbeddingService
from pinecone_service import PineconeService
import requests
import json
from dotenv import load_dotenv

# Cargar variables de entorno explícitamente
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

logger = logging.getLogger(__name__)

class RAGManager:
    """
    Gestor principal del sistema RAG que coordina embeddings, Pinecone y Ollama
    """
    
    def __init__(self):
        """Inicializa el gestor RAG"""
        # Configurar Ollama
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
        
        logger.info(f"Configurando Ollama en: {self.ollama_base_url}")
        logger.info(f"Modelo: {self.ollama_model}")
        
        try:
            # Verificar que Ollama esté funcionando
            response = requests.get(f"{self.ollama_base_url}/api/tags")
            if response.status_code == 200:
                logger.info("Ollama configurado exitosamente")
            else:
                logger.warning("Ollama no responde, pero continuando...")
        except Exception as e:
            logger.warning(f"No se pudo conectar a Ollama: {e}")
        
        # Inicializar servicios
        self.embedding_service = EmbeddingService()
        self.pinecone_service = PineconeService()
        
        # Estado de inicialización
        self.is_initialized = False
    
    def initialize_rag_system(self, force_refresh: bool = False) -> bool:
        """
        Inicializa el sistema RAG completo
        
        Args:
            force_refresh: Si True, regenera embeddings y los sube a Pinecone
            
        Returns:
            True si la inicialización fue exitosa
        """
        try:
            logger.info("Iniciando sistema RAG...")
            
            # Verificar si ya hay datos en Pinecone
            has_data = self.pinecone_service.index_exists_and_has_data()
            
            if has_data and not force_refresh:
                logger.info("Pinecone ya tiene datos, usando índice existente")
                self.is_initialized = True
                return True
            
            # Generar embeddings
            logger.info("Generando embeddings de documentos...")
            embeddings, documents = self.embedding_service.generate_embeddings(force_refresh)
            
            if len(embeddings) == 0:
                logger.error("No se pudieron generar embeddings")
                return False
            
            # Subir a Pinecone
            if force_refresh or not has_data:
                logger.info("Subiendo embeddings a Pinecone...")
                if force_refresh and has_data:
                    # Limpiar índice existente si forzamos refresh
                    self.pinecone_service.clear_index()
                
                self.pinecone_service.upload_embeddings(embeddings, documents)
            
            self.is_initialized = True
            logger.info("Sistema RAG inicializado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error al inicializar sistema RAG: {e}")
            self.is_initialized = False
            return False
    
    def search_context(self, query: str, top_k: int = 5, min_score: float = 0.3) -> List[Dict]:
        """
        Busca contexto relevante para una consulta
        
        Args:
            query: Consulta del usuario
            top_k: Número máximo de documentos a devolver
            min_score: Score mínimo de similitud
            
        Returns:
            Lista de documentos relevantes
        """
        if not self.is_initialized:
            logger.error("Sistema RAG no inicializado")
            return []
        
        try:
            # Generar embedding de la consulta
            query_embedding = self.embedding_service.get_embedding(query)
            
            # Buscar en Pinecone
            similar_docs = self.pinecone_service.search_similar(
                query_embedding=query_embedding,
                top_k=top_k,
                min_score=min_score
            )
            
            return similar_docs
            
        except Exception as e:
            logger.error(f"Error al buscar contexto: {e}")
            return []
    
    def generate_response(self, query: str, conversation_history: List[Dict] = None) -> Tuple[str, List[str]]:
        """
        Genera respuesta usando RAG con Gemini
        
        Args:
            query: Consulta del usuario
            conversation_history: Historial de conversación
            
        Returns:
            Tupla de (respuesta, fuentes)
        """
        if not self.is_initialized:
            return "El sistema RAG no está inicializado.", []
        
        try:
            # Buscar contexto relevante
            relevant_docs = self.search_context(query)
            
            if not relevant_docs:
                # Si no hay contexto, responder que no se encontró información
                return self._generate_no_context_response(query), []
            
            # Preparar contexto
            context_texts = []
            sources = []
            
            for doc in relevant_docs:
                context_texts.append(f"Fuente: {doc['source']}\n{doc['text']}")
                if doc['source'] not in sources:
                    sources.append(doc['source'])
            
            context = "\n\n---\n\n".join(context_texts)
            
            # Preparar historial de conversación
            history_text = ""
            if conversation_history:
                history_parts = []
                for msg in conversation_history[-6:]:  # Últimos 6 mensajes
                    role = "Usuario" if msg.get("sender") == "user" else "Asistente"
                    history_parts.append(f"{role}: {msg.get('text', '')}")
                history_text = "\n".join(history_parts)
            
            # Generar prompt
            if history_text:
                prompt = f"""Eres un asistente especializado en responder preguntas basándote únicamente en la información proporcionada. Responde de manera clara, precisa y útil.

Contexto de la conversación anterior:
{history_text}

Información relevante de la base de conocimientos:
{context}

Pregunta del usuario: {query}

Instrucciones:
1. Responde SOLO basándote en la información proporcionada arriba
2. Si la información no es suficiente para responder completamente, indícalo claramente
3. Mantén un tono profesional y útil
4. Estructura tu respuesta de manera clara y fácil de entender
5. Si hay múltiples aspectos en la pregunta, abórdalos todos si la información lo permite

Respuesta:"""
            else:
                prompt = f"""Eres un asistente especializado en responder preguntas basándote únicamente en la información proporcionada. Responde de manera clara, precisa y útil.

Información relevante de la base de conocimientos:
{context}

Pregunta del usuario: {query}

Instrucciones:
1. Responde SOLO basándote en la información proporcionada arriba
2. Si la información no es suficiente para responder completamente, indícalo claramente
3. Mantén un tono profesional y útil
4. Estructura tu respuesta de manera clara y fácil de entender

Respuesta:"""
            
            # Generar respuesta con Ollama
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 500
                }
            }
            
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=120  # Aumentar timeout para primera ejecución
            )
            
            if response.status_code == 200:
                ai_response = response.json().get("response", "No se pudo generar una respuesta.")
            else:
                ai_response = "Error al comunicarse con Ollama."
            
            logger.info(f"Respuesta RAG generada. Fuentes: {sources}")
            return ai_response, sources
            
        except Exception as e:
            logger.error(f"Error al generar respuesta RAG: {e}")
            return "Lo siento, hubo un error al procesar tu consulta.", []
    
    def _generate_no_context_response(self, query: str) -> str:
        """Genera respuesta cuando no se encuentra contexto relevante"""
        try:
            prompt = f"""El usuario preguntó: "{query}"

No se encontró información específica en la base de conocimientos para responder esta pregunta.

Genera una respuesta breve y útil que:
1. Indique cortésmente que no tienes información específica sobre ese tema
2. Sugiera reformular la pregunta o preguntar sobre temas relacionados con gestión de calidad, políticas universitarias, o procedimientos institucionales
3. Mantén un tono profesional y servicial

Respuesta:"""
            
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.5,
                    "num_predict": 200
                }
            }
            
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=45  # Timeout más largo para esta función también
            )
            
            if response.status_code == 200:
                return response.json().get("response", "No encontré información específica sobre tu consulta. ¿Podrías reformular la pregunta o preguntar sobre algún tema específico?")
            else:
                return "No encontré información específica sobre tu consulta. ¿Podrías reformular la pregunta o preguntar sobre algún tema específico?"
            
        except Exception as e:
            logger.error(f"Error al generar respuesta sin contexto: {e}")
            return "No encontré información específica sobre tu consulta en la base de conocimientos."
    
    def get_system_status(self) -> Dict:
        """Obtiene el estado del sistema RAG"""
        try:
            pinecone_stats = self.pinecone_service.get_index_stats()
            
            return {
                "rag_initialized": self.is_initialized,
                "embedding_model": self.embedding_service.model_name,
                "pinecone_vectors": pinecone_stats.get("total_vector_count", 0),
                "pinecone_index": pinecone_stats.get("index_name", ""),
                "ollama_model": self.ollama_model,
                "ollama_url": self.ollama_base_url
            }
        except Exception as e:
            logger.error(f"Error al obtener estado del sistema: {e}")
            return {
                "rag_initialized": False,
                "error": str(e)
            }
    
    def rebuild_index(self) -> bool:
        """Reconstruye completamente el índice"""
        logger.info("Reconstruyendo índice RAG...")
        return self.initialize_rag_system(force_refresh=True)