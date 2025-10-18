import os
import logging
import json
import aiohttp
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class OllamaService:
    def __init__(self):
        """Inicializa el servicio de Ollama local"""
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = os.getenv("OLLAMA_MODEL", "llama3.2")
        
        # Configuración de generación optimizada para velocidad
        self.generation_options = {
            'temperature': 0.7,
            'top_p': 0.9,
            'top_k': 20,           # Reducido para mayor velocidad
            'num_predict': 512,    # Reducido significativamente para respuestas más rápidas
            'repeat_penalty': 1.1,
            'stop': []
        }
        
        # Configuración aún más rápida para respuestas cortas
        self.fast_options = {
            'temperature': 0.5,
            'top_p': 0.9,
            'top_k': 10,
            'num_predict': 256,    # Respuestas muy cortas
            'repeat_penalty': 1.1,
            'stop': ['\n\n', '---']  # Para cortar respuestas largas
        }
        
        logger.info(f"Ollama Service inicializado - URL: {self.base_url}, Modelo: {self.model_name}")
    
    def create_rag_prompt(
        self,
        user_question: str,
        context_chunks: List[Dict[str, Any]],
        chatbot_name: str = "Asistente"
    ) -> str:
        """
        Crea un prompt optimizado para RAG con contexto
        
        Args:
            user_question: Pregunta del usuario
            context_chunks: Lista de chunks de contexto relevante
            chatbot_name: Nombre del chatbot personalizado
            
        Returns:
            str: Prompt formateado para Ollama
        """
        
        # Formatear contexto de manera más concisa
        context_text = ""
        if context_chunks:
            context_text = "CONTEXTO:\n"
            for i, chunk in enumerate(context_chunks[:3], 1):  # Limitar a 3 chunks para velocidad
                metadata = chunk.get('metadata', {})
                text = metadata.get('text', '')[:300]  # Limitar texto por chunk
                source = metadata.get('source', 'Doc')
                context_text += f"[{i}] {source}: {text}...\n"
        
        # Prompt más conciso para mayor velocidad
        prompt = f"""Eres {chatbot_name}. Responde de forma clara y concisa.

{context_text}

PREGUNTA: {user_question}

RESPUESTA (máximo 3 párrafos):"""

        return prompt
    
    async def _check_ollama_health(self) -> bool:
        """Verifica si Ollama está disponible"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/version", timeout=5) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Ollama no está disponible: {str(e)}")
            return False
    
    async def _ensure_model_available(self) -> bool:
        """Verifica que el modelo esté disponible y lo descarga si es necesario"""
        try:
            async with aiohttp.ClientSession() as session:
                # Verificar modelos disponibles
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [model['name'] for model in data.get('models', [])]
                        
                        # Verificar si el modelo ya está disponible
                        model_available = any(self.model_name in model for model in models)
                        
                        if not model_available:
                            logger.info(f"Descargando modelo {self.model_name}...")
                            # Intentar descargar el modelo
                            pull_data = {"name": self.model_name}
                            async with session.post(
                                f"{self.base_url}/api/pull", 
                                json=pull_data,
                                timeout=300  # 5 minutos para descarga
                            ) as pull_response:
                                if pull_response.status == 200:
                                    logger.info(f"Modelo {self.model_name} descargado exitosamente")
                                    return True
                                else:
                                    logger.error(f"Error descargando modelo: {pull_response.status}")
                                    return False
                        else:
                            logger.info(f"Modelo {self.model_name} ya está disponible")
                            return True
                    return False
        except Exception as e:
            logger.error(f"Error verificando/descargando modelo: {str(e)}")
            return False
    
    async def generate_response(
        self,
        user_question: str,
        context_chunks: List[Dict[str, Any]] = None,
        chatbot_name: str = "Asistente",
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Genera una respuesta usando Ollama local con contexto RAG
        
        Args:
            user_question: Pregunta del usuario
            context_chunks: Chunks de contexto relevante de Pinecone
            chatbot_name: Nombre del chatbot personalizado
            conversation_history: Historial de conversación (opcional)
            
        Returns:
            Dict con la respuesta y metadatos
        """
        try:
            # Verificar que Ollama esté disponible
            if not await self._check_ollama_health():
                return {
                    "success": False,
                    "response": "El servicio de IA local (Ollama) no está disponible. Por favor verifica que esté ejecutándose.",
                    "error": "Ollama no disponible",
                    "model_used": self.model_name,
                    "context_used": 0,
                    "sources": []
                }
            
            # Asegurar que el modelo esté disponible
            if not await self._ensure_model_available():
                return {
                    "success": False,
                    "response": f"El modelo {self.model_name} no está disponible. Por favor verifica la configuración.",
                    "error": "Modelo no disponible",
                    "model_used": self.model_name,
                    "context_used": 0,
                    "sources": []
                }
            
            # Crear prompt con contexto RAG
            if context_chunks:
                prompt = self.create_rag_prompt(user_question, context_chunks, chatbot_name)
            else:
                # Fallback sin contexto - prompt conciso
                prompt = f"""Eres {chatbot_name}. Responde de forma breve y útil.

PREGUNTA: {user_question}

RESPUESTA (máximo 2 párrafos):"""

            # Agregar historial de conversación si existe (limitado para velocidad)
            if conversation_history:
                history_text = "\nHISTORIAL:\n"
                for msg in conversation_history[-2:]:  # Solo últimos 2 mensajes para velocidad
                    role = "U" if msg.get("sender") == "user" else "A"
                    text = msg.get('text', '')[:100]  # Limitar longitud del historial
                    history_text += f"{role}: {text}...\n"
                prompt = history_text + "\n" + prompt
            
            # Generar respuesta con Ollama
            response_text = await self._generate_with_ollama(prompt)
            
            return {
                "success": True,
                "response": response_text,
                "model_used": self.model_name,
                "context_used": len(context_chunks) if context_chunks else 0,
                "sources": [chunk.get('metadata', {}).get('source', 'Desconocido') 
                           for chunk in context_chunks] if context_chunks else []
            }
            
        except Exception as e:
            logger.error(f"Error generando respuesta con Ollama: {str(e)}")
            return {
                "success": False,
                "response": "Lo siento, hubo un error al procesar tu consulta. Por favor intenta nuevamente.",
                "error": str(e),
                "model_used": self.model_name,
                "context_used": 0,
                "sources": []
            }
    
    async def _generate_with_ollama(self, prompt: str, max_retries: int = 3, fast_mode: bool = False) -> str:
        """
        Genera respuesta usando la API de Ollama
        
        Args:
            prompt: Prompt para el modelo
            max_retries: Número máximo de reintentos
            fast_mode: Usar configuración rápida para respuestas cortas
            
        Returns:
            str: Respuesta generada
        """
        # Elegir configuración según el modo
        options = self.fast_options if fast_mode else self.generation_options
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    request_data = {
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": options
                    }
                    
                    async with session.post(
                        f"{self.base_url}/api/generate",
                        json=request_data,
                        timeout=30  # Reducido a 30 segundos para respuestas más rápidas
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            response_text = data.get('response', '').strip()
                            
                            if response_text:
                                return response_text
                            else:
                                logger.warning("Respuesta vacía de Ollama")
                                return "Lo siento, no pude generar una respuesta válida."
                        else:
                            error_text = await response.text()
                            logger.error(f"Error de Ollama (status {response.status}): {error_text}")
                            raise Exception(f"Error HTTP {response.status}: {error_text}")
                            
            except Exception as e:
                logger.warning(f"Intento {attempt + 1} falló: {str(e)}")
                if attempt == max_retries - 1:
                    raise e
                
        return "Error generando respuesta después de múltiples intentos."
    
    async def generate_title_for_conversation(
        self,
        first_message: str,
        max_length: int = 50
    ) -> str:
        """
        Genera un título conciso para una conversación basado en el primer mensaje
        
        Args:
            first_message: Primer mensaje de la conversación
            max_length: Longitud máxima del título
            
        Returns:
            str: Título generado
        """
        try:
            # Prompt más conciso para generar títulos rápido
            prompt = f"""Crea un título breve (máx {max_length} chars) para esta pregunta:
"{first_message[:100]}"

TÍTULO:"""

            response = await self._generate_with_ollama(prompt, fast_mode=True)
            
            # Limpiar y truncar el título
            title = response.strip().strip('"').strip("'")
            if len(title) > max_length:
                title = title[:max_length-3] + "..."
                
            return title if title else "Nueva conversación"
            
        except Exception as e:
            logger.error(f"Error generando título: {str(e)}")
            return "Nueva conversación"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Retorna información sobre el modelo configurado"""
        return {
            "model_name": self.model_name,
            "base_url": self.base_url,
            "temperature": self.generation_options.get('temperature'),
            "max_tokens": self.generation_options.get('num_predict'),
            "provider": "Ollama Local"
        }


# Instancia global del servicio
ollama_service = OllamaService()