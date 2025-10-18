import os
import logging
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class GeminiService:
    def __init__(self):
        """Inicializa el servicio de Gemini 1.5 Flash"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY no encontrada en las variables de entorno")
        
        # Log para verificar que la key se está cargando (solo primeros y últimos caracteres por seguridad)
        logger.info(f"API Key cargada: {api_key[:10]}...{api_key[-10:] if len(api_key) > 20 else 'corta'}")
        
        genai.configure(api_key=api_key)
        
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        logger.info(f"Modelo Gemini configurado: {self.model_name}")
        
        try:
            self.model = genai.GenerativeModel(self.model_name)
            logger.info("Servicio Gemini inicializado correctamente")
        except Exception as e:
            logger.error(f"Error inicializando modelo Gemini: {str(e)}")
            raise
        
        # Configuración de seguridad más permisiva para respuestas académicas
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        
        # Configuración de generación
        self.generation_config = {
            'temperature': 0.7,
            'top_p': 0.8,
            'top_k': 40,
            'max_output_tokens': 2048,
        }
    
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
            str: Prompt formateado para Gemini
        """
        
        # Formatear contexto
        context_text = ""
        if context_chunks:
            context_text = "INFORMACIÓN RELEVANTE ENCONTRADA:\n\n"
            for i, chunk in enumerate(context_chunks, 1):
                metadata = chunk.get('metadata', {})
                text = metadata.get('text', '')
                source = metadata.get('source', 'Documento')
                page = metadata.get('page', 'N/A')
                
                context_text += f"[Fuente {i}] {source} (Página {page}):\n{text}\n\n"
        
        prompt = f"""Eres {chatbot_name}, un asistente especializado y confiable. Tu objetivo es proporcionar respuestas precisas y útiles basadas en la información disponible.

{context_text}

PREGUNTA DEL USUARIO: {user_question}

INSTRUCCIONES:
1. Responde de manera clara y precisa basándote PRINCIPALMENTE en la información relevante proporcionada arriba
2. Si la información relevante no es suficiente para responder completamente, indícalo claramente
3. Estructura tu respuesta de forma organizada y fácil de leer
4. Cita las fuentes cuando sea apropiado (ej: "Según la fuente 1...")
5. Si no hay información relevante, responde con tu conocimiento general pero indica que es información general
6. Mantén un tono profesional y amigable
7. Si la pregunta no está relacionada con el contexto, responde de manera general pero educativa

RESPUESTA:"""

        return prompt
    
    async def generate_response(
        self,
        user_question: str,
        context_chunks: List[Dict[str, Any]] = None,
        chatbot_name: str = "Asistente",
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Genera una respuesta usando Gemini 2.5 Flash con contexto RAG
        
        Args:
            user_question: Pregunta del usuario
            context_chunks: Chunks de contexto relevante de Pinecone
            chatbot_name: Nombre del chatbot personalizado
            conversation_history: Historial de conversación (opcional)
            
        Returns:
            Dict con la respuesta y metadatos
        """
        try:
            # Crear prompt con contexto RAG
            if context_chunks:
                prompt = self.create_rag_prompt(user_question, context_chunks, chatbot_name)
            else:
                # Fallback sin contexto
                prompt = f"""Eres {chatbot_name}, un asistente útil y confiable.

PREGUNTA: {user_question}

Responde de manera clara, precisa y educativa. Si no tienes información específica sobre el tema, indícalo claramente pero proporciona información general útil que puedas."""

            # Agregar historial de conversación si existe
            if conversation_history:
                history_text = "\n\nHISTORIAL DE CONVERSACIÓN RECIENTE:\n"
                for msg in conversation_history[-3:]:  # Solo últimos 3 mensajes
                    role = "Usuario" if msg.get("sender") == "user" else "Asistente"
                    history_text += f"{role}: {msg.get('text', '')}\n"
                prompt = history_text + "\n" + prompt
            
            # Generar respuesta
            response = await self._generate_with_retry(prompt)
            
            return {
                "success": True,
                "response": response,
                "model_used": self.model_name,
                "context_used": len(context_chunks) if context_chunks else 0,
                "sources": [chunk.get('metadata', {}).get('source', 'Desconocido') 
                           for chunk in context_chunks] if context_chunks else []
            }
            
        except Exception as e:
            logger.error(f"Error generando respuesta con Gemini: {str(e)}")
            return {
                "success": False,
                "response": "Lo siento, hubo un error al procesar tu consulta. Por favor intenta nuevamente.",
                "error": str(e),
                "model_used": self.model_name,
                "context_used": 0,
                "sources": []
            }
    
    async def _generate_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """
        Genera respuesta con reintentos en caso de error
        
        Args:
            prompt: Prompt para Gemini
            max_retries: Número máximo de reintentos
            
        Returns:
            str: Respuesta generada
        """
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config=self.generation_config,
                    safety_settings=self.safety_settings
                )
                
                if response.text:
                    return response.text.strip()
                else:
                    # Si el contenido fue bloqueado por filtros de seguridad
                    return "Lo siento, no puedo proporcionar una respuesta a esa consulta debido a las políticas de seguridad."
                    
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
            prompt = f"""Genera un título conciso y descriptivo para una conversación que comienza con esta pregunta:

"{first_message}"

El título debe:
- Ser máximo {max_length} caracteres
- Describir el tema principal
- Ser claro y específico
- No incluir comillas

TÍTULO:"""

            response = await self._generate_with_retry(prompt)
            
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
            "temperature": self.generation_config.get('temperature'),
            "max_tokens": self.generation_config.get('max_output_tokens'),
            "provider": "Google Gemini"
        }


# Instancia global del servicio
gemini_service = GeminiService()