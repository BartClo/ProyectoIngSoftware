import os
import logging
from typing import List, Dict, Any, Optional
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class GroqService:
    def __init__(self):
        """Inicializa el servicio de Groq con Llama3"""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY no encontrada en las variables de entorno")
        
        # Verificar que la API Key no sea placeholder
        if api_key in ["REEMPLAZAR_CON_TU_API_KEY_VALIDA", "tu_api_key_aqui"]:
            raise ValueError(
                "⚠️ API Key de Groq no válida. "
                "Obtener una nueva en: https://console.groq.com/keys "
                "y configurar en backend/.env"
            )
        
        # Log para verificar que la key se está cargando (solo primeros y últimos caracteres por seguridad)
        logger.info(f"API Key cargada: {api_key[:10]}...{api_key[-10:] if len(api_key) > 20 else 'corta'}")
        
        # Inicializar cliente Groq
        self.client = Groq(api_key=api_key)
        
        self.model_name = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        logger.info(f"Modelo Groq configurado: {self.model_name}")
        
        try:
            # Test básico del modelo
            logger.info("Servicio Groq inicializado correctamente")
        except Exception as e:
            logger.error(f"Error inicializando modelo Groq: {str(e)}")
            raise
        
        # Configuración de generación para Groq
        self.generation_config = {
            'temperature': 0.7,
            'max_tokens': 2048,
            'top_p': 0.8,
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
            str: Prompt formateado para Groq/Llama3
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
        Genera una respuesta usando Groq/Llama3 con contexto RAG
        
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

            # Preparar mensajes para el chat
            messages = [
                {
                    "role": "system",
                    "content": "Eres un asistente inteligente y útil. Responde de manera precisa y organizada."
                }
            ]

            # Agregar historial de conversación si existe
            if conversation_history:
                for msg in conversation_history[-3:]:  # Solo últimos 3 mensajes
                    role = "user" if msg.get("sender") == "user" else "assistant"
                    messages.append({
                        "role": role,
                        "content": msg.get("text", "")
                    })
            
            # Agregar pregunta actual
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Generar respuesta
            response = await self._generate_with_retry(messages)
            
            return {
                "success": True,
                "response": response,
                "model_used": self.model_name,
                "context_used": len(context_chunks) if context_chunks else 0,
                "sources": [chunk.get('metadata', {}).get('source', 'Desconocido') 
                           for chunk in context_chunks] if context_chunks else []
            }
            
        except Exception as e:
            logger.error(f"Error generando respuesta con Groq: {str(e)}")
            return {
                "success": False,
                "response": "Lo siento, hubo un error al procesar tu consulta. Por favor intenta nuevamente.",
                "error": str(e),
                "model_used": self.model_name,
                "context_used": 0,
                "sources": []
            }
    
    async def _generate_with_retry(self, messages: List[Dict[str, str]], max_retries: int = 3) -> str:
        """
        Genera respuesta con reintentos en caso de error
        
        Args:
            messages: Lista de mensajes para el chat
            max_retries: Número máximo de reintentos
            
        Returns:
            str: Respuesta generada
        """
        for attempt in range(max_retries):
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=messages,
                    model=self.model_name,
                    temperature=self.generation_config['temperature'],
                    max_tokens=self.generation_config['max_tokens'],
                    top_p=self.generation_config['top_p']
                )
                
                if chat_completion.choices and chat_completion.choices[0].message.content:
                    return chat_completion.choices[0].message.content.strip()
                else:
                    return "Lo siento, no pude generar una respuesta adecuada."
                    
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
            messages = [
                {
                    "role": "system",
                    "content": "Eres un experto en crear títulos concisos y descriptivos."
                },
                {
                    "role": "user", 
                    "content": f"""Genera un título conciso y descriptivo para una conversación que comienza con esta pregunta:

"{first_message}"

El título debe:
- Ser máximo {max_length} caracteres
- Describir el tema principal
- Ser claro y específico
- No incluir comillas

TÍTULO:"""
                }
            ]

            chat_completion = self.client.chat.completions.create(
                messages=messages,
                model=self.model_name,
                temperature=0.3,  # Más determinístico para títulos
                max_tokens=20,
                top_p=0.8
            )
            
            if chat_completion.choices and chat_completion.choices[0].message.content:
                title = chat_completion.choices[0].message.content.strip().strip('"').strip("'")
                
                # Truncar si es necesario
                if len(title) > max_length:
                    title = title[:max_length-3] + "..."
                    
                return title if title else "Nueva conversación"
            else:
                return "Nueva conversación"
            
        except Exception as e:
            logger.error(f"Error generando título: {str(e)}")
            return "Nueva conversación"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Retorna información sobre el modelo configurado"""
        return {
            "model_name": self.model_name,
            "temperature": self.generation_config.get('temperature'),
            "max_tokens": self.generation_config.get('max_tokens'),
            "provider": "Groq (Llama3)"
        }


# Instancia global del servicio
groq_service = GroqService()