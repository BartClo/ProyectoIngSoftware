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
        Crea un prompt optimizado para RAG con contexto y restricciones estrictas.

        Args:
            user_question: Pregunta del usuario
            context_chunks: Lista de chunks de contexto relevante
            chatbot_name: Nombre del chatbot personalizado

        Returns:
            str: Prompt formateado para Groq/Llama3
        """

        system_prompt = (
            f"Eres {chatbot_name}, un asistente especializado con acceso ÚNICAMENTE a documentos proporcionados.\n\n"
            "RESTRICCIONES CRÍTICAS:\n"
            "1. SOLO puedes responder basándote en la información proporcionada en el CONTEXTO RELEVANTE a continuación.\n"
            "2. Si la pregunta no puede responderse usando ÚNICAMENTE el contexto proporcionado, debes responder exactamente:\n"
            "   \"Lo siento, no puedo responder a esa pregunta ya que se encuentra fuera del alcance de los documentos proporcionados.\"\n"
            "3. NO debes inventar, inferir o agregar información que no esté explícitamente en el contexto.\n"
            "4. Debes citar la fuente específica de cada parte de tu respuesta.\n\n"
            "FORMATO DE RESPUESTA:\n"
            "- Responde de manera concisa y directa.\n"
            "- Incluye las referencias específicas del documento (página/sección) que respaldan tu respuesta.\n\n"
        )

        # Formatear contexto
        context_text = ""
        if context_chunks:
            context_text = "CONTEXTO RELEVANTE:\n\n"
            for i, chunk in enumerate(context_chunks, 1):
                metadata = chunk.get('metadata', {})
                text = metadata.get('text', '')
                source = metadata.get('source', 'Documento')
                page = metadata.get('page', 'N/A')
                context_text += (
                    f"FRAGMENTO {i}:\n"
                    f"Contenido: {text}\n"
                    f"Fuente: {source}\n"
                    f"Página/Sección: {page}\n\n"
                )

        # Nota: no incluimos la pregunta del usuario dentro del contenido del sistema;
        # construiremos los mensajes como [system, ...history, user] para alinearnos mejor
        # con el formato esperado por los modelos de chat.
        prompt = (
            system_prompt
            + context_text
            + "\nINSTRUCCIONES:\n"
            + "1. Responde ÚNICAMENTE basándote en el contexto proporcionado.\n"
            + "2. Si no hay información suficiente, responde exactamente: \"Lo siento, no puedo responder a esa pregunta ya que se encuentra fuera del alcance de los documentos proporcionados.\"\n\n"
        )

        return prompt
    
    async def generate_response(
        self,
        user_question: str,
        context_chunks: List[Dict[str, Any]] = None,
        chatbot_name: str = "Asistente",
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
            Genera una respuesta usando Groq/Llama3 con contexto RAG estricto
        
        Args:
            user_question: Pregunta del usuario
            context_chunks: Chunks de contexto relevante de Pinecone
            chatbot_name: Nombre del chatbot personalizado
            conversation_history: Historial de conversación (opcional)
            
        Returns:
            Dict con la respuesta y metadatos
        """
        try:
            # Si no hay contexto relevante, devolver un mensaje estándar de "fuera de contexto"
            if not context_chunks:
                out_of_context_msg = 'Lo siento, no puedo responder a algo que no sea del "contexto de archivo cargado".'
                return {
                    "success": True,
                    "response": out_of_context_msg,
                    "sources": [],
                    "context_used": 0
                }

            # Construir prompt RAG estricto (sistema + contexto)
            system_content = self.create_rag_prompt(user_question, context_chunks, chatbot_name)

            # Preparar mensajes: system, historial (si existe), y finalmente el user turn
            messages = [{"role": "system", "content": system_content}]
            if conversation_history:
                for msg in conversation_history[-3:]:  # Últimos 3 mensajes
                    role = "user" if msg.get("sender") == "user" else "assistant"
                    messages.append({"role": role, "content": msg.get("text", "")})

            # Añadir el turno del usuario al final (mejora la probabilidad de respuesta adecuada)
            messages.append({"role": "user", "content": user_question})

            # Logging opcional para depuración: tamaño del contexto y del payload
            if os.getenv("GROQ_DEBUG_LOG", "false").lower() in ("1", "true", "yes"):
                logger.info(f"[GROQ DEBUG] context_chunks={len(context_chunks)} messages={len(messages)}")

            # Generar respuesta con reintentos; si falla completamente, raise para que el caller decida
            response_text = await self._generate_with_retry(messages)

            # Extraer fuentes únicas
            sources = []
            for chunk in context_chunks:
                src = chunk.get('metadata', {}).get('source', 'Desconocido')
                if src and src not in sources:
                    sources.append(src)

            return {
                "success": True,
                "response": response_text,
                "model_used": self.model_name,
                "context_used": len(context_chunks),
                "sources": sources
            }

        except Exception as e:
            logger.error(f"Error generando respuesta con Groq: {str(e)}")
            # Devolver success=False para que el caller (ruta) pueda intentar una regeneración
            return {
                "success": False,
                "response": "Lo siento, no pude generar una respuesta adecuada.",
                "error": str(e),
                "model_used": self.model_name,
                "context_used": 0,
                "sources": []
            }
    
    async def _generate_with_retry(self, messages: List[Dict[str, str]], max_retries: int = 4) -> str:
        """
        Genera respuesta con reintentos en caso de error
        
        Args:
            messages: Lista de mensajes para el chat
            max_retries: Número máximo de reintentos
            
        Returns:
            str: Respuesta generada
        """
        import asyncio

        for attempt in range(1, max_retries + 1):
            try:
                # Llamada al cliente (puede ser sync); envolvemos en try para reintentar si devuelve vacío
                chat_completion = self.client.chat.completions.create(
                    messages=messages,
                    model=self.model_name,
                    temperature=self.generation_config['temperature'],
                    max_tokens=self.generation_config['max_tokens'],
                    top_p=self.generation_config['top_p']
                )

                # Validar contenido
                content = None
                if hasattr(chat_completion, 'choices') and chat_completion.choices:
                    choice = chat_completion.choices[0]
                    # Compatibilidad con diferentes SDKs
                    if hasattr(choice, 'message') and getattr(choice.message, 'content', None):
                        content = choice.message.content
                    elif isinstance(choice, dict) and choice.get('message') and choice['message'].get('content'):
                        content = choice['message']['content']
                    elif getattr(choice, 'text', None):
                        content = choice.text

                if content and isinstance(content, str) and content.strip():
                    # Si el modelo devolvió la cadena de guardrail exacta, considerarlo fallo
                    trimmed = content.strip()
                    if "no puedo responder" in trimmed.lower() or "no pude generar" in trimmed.lower():
                        logger.warning(f"Intento {attempt} devolvió texto de guardrail/fallo. Reintentando...")
                        # seguir reintentando (si aún hay intentos)
                        if attempt < max_retries:
                            await asyncio.sleep(0.8 * attempt)
                            continue
                        else:
                            raise RuntimeError("Generación vacía / guardrail repetido")

                    return trimmed

                # Si no hay contenido válido, registrar y reintentar
                logger.warning(f"Intento {attempt} no devolvió contenido. Reintentando...")
                if attempt < max_retries:
                    await asyncio.sleep(0.8 * attempt)
                    continue
                else:
                    raise RuntimeError("Generación vacía después de múltiples intentos")

            except Exception as e:
                logger.warning(f"Intento {attempt} falló: {str(e)}")
                if attempt < max_retries:
                    await asyncio.sleep(0.8 * attempt)
                    continue
                else:
                    # Al final, propagar el error para que el caller lo maneje
                    raise e

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