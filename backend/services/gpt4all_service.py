import os
import logging
from typing import List, Dict, Any, Optional
from gpt4all import GPT4All
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class GPT4AllService:
    def __init__(self):
        """Inicializa el servicio de GPT4All local"""
        
        # Configuración del modelo
        self.model_name = os.getenv("GPT4ALL_MODEL", "Meta-Llama-3-8B-Instruct.Q4_0.gguf")
        self.allow_download = True
        self.device = 'cpu'  # o 'gpu' si tienes GPU compatible
        
        # Configuración de generación optimizada
        self.generation_config = {
            'max_tokens': 512,
            'temp': 0.7,
            'top_p': 0.9,
            'top_k': 40,
            'repeat_penalty': 1.1,
        }
        
        # Configuración rápida para respuestas cortas
        self.fast_config = {
            'max_tokens': 256,
            'temp': 0.5,
            'top_p': 0.9,
            'top_k': 20,
            'repeat_penalty': 1.1,
        }
        
        # Inicializar modelo
        self.model = None
        self._initialize_model()
        
        logger.info(f"GPT4All Service inicializado - Modelo: {self.model_name}")
    
    def _initialize_model(self):
        """Inicializa el modelo GPT4All"""
        try:
            logger.info(f"Inicializando modelo GPT4All: {self.model_name}")
            
            self.model = GPT4All(
                model_name=self.model_name,
                allow_download=self.allow_download,
                device=self.device
            )
            
            logger.info("Modelo GPT4All inicializado exitosamente")
            
        except Exception as e:
            logger.error(f"Error inicializando GPT4All: {str(e)}")
            
            # Fallback a modelo más pequeño si el principal falla
            try:
                logger.info("Intentando con modelo alternativo más ligero...")
                self.model_name = "orca-mini-3b-gguf2-q4_0.gguf"
                
                self.model = GPT4All(
                    model_name=self.model_name,
                    allow_download=self.allow_download,
                    device=self.device
                )
                
                logger.info(f"Modelo alternativo {self.model_name} inicializado exitosamente")
                
            except Exception as e2:
                logger.error(f"Error con modelo alternativo: {str(e2)}")
                self.model = None
    
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
            str: Prompt formateado para GPT4All
        """
        
        # Formatear contexto de manera concisa
        context_text = ""
        if context_chunks:
            context_text = "### CONTEXTO RELEVANTE:\n"
            for i, chunk in enumerate(context_chunks[:3], 1):  # Limitar a 3 chunks
                metadata = chunk.get('metadata', {})
                text = metadata.get('text', '')[:400]  # Limitar texto por chunk
                source = metadata.get('source', 'Documento')
                context_text += f"**Fuente {i} ({source}):** {text}...\n\n"
        
        # Prompt optimizado para GPT4All
        prompt = f"""Eres {chatbot_name}, un asistente inteligente y útil.

{context_text}

### INSTRUCCIONES:
- Responde de forma clara, precisa y útil
- Usa el contexto proporcionado cuando sea relevante
- Si no tienes información suficiente, dilo claramente
- Mantén las respuestas concisas pero completas

### PREGUNTA DEL USUARIO:
{user_question}

### RESPUESTA:"""

        return prompt
    
    def _check_model_available(self) -> bool:
        """Verifica si el modelo está disponible"""
        return self.model is not None
    
    async def generate_response(
        self,
        user_question: str,
        context_chunks: List[Dict[str, Any]] = None,
        chatbot_name: str = "Asistente",
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Genera una respuesta usando GPT4All local con contexto RAG
        
        Args:
            user_question: Pregunta del usuario
            context_chunks: Chunks de contexto relevante
            chatbot_name: Nombre del chatbot personalizado
            conversation_history: Historial de conversación (opcional)
            
        Returns:
            Dict con la respuesta y metadatos
        """
        try:
            # Verificar que el modelo esté disponible
            if not self._check_model_available():
                return {
                    "success": False,
                    "response": "El modelo de IA local no está disponible. Por favor verifica la configuración.",
                    "error": "Modelo no disponible",
                    "model_used": self.model_name,
                    "context_used": 0,
                    "sources": []
                }
            
            # Crear prompt con contexto RAG
            if context_chunks:
                prompt = self.create_rag_prompt(user_question, context_chunks, chatbot_name)
            else:
                # Fallback sin contexto
                prompt = f"""Eres {chatbot_name}, un asistente inteligente y útil.

### PREGUNTA:
{user_question}

### RESPUESTA (clara y concisa):"""

            # Agregar historial de conversación si existe (limitado)
            if conversation_history:
                history_text = "\n### CONTEXTO DE CONVERSACIÓN:\n"
                for msg in conversation_history[-2:]:  # Solo últimos 2 mensajes
                    role = "Usuario" if msg.get("sender") == "user" else "Asistente"
                    text = msg.get('text', '')[:150]  # Limitar longitud
                    history_text += f"**{role}:** {text}...\n"
                prompt = history_text + "\n" + prompt
            
            # Generar respuesta con GPT4All
            response_text = self._generate_with_gpt4all(prompt)
            
            return {
                "success": True,
                "response": response_text,
                "model_used": self.model_name,
                "context_used": len(context_chunks) if context_chunks else 0,
                "sources": [chunk.get('metadata', {}).get('source', 'Desconocido') 
                           for chunk in context_chunks] if context_chunks else []
            }
            
        except Exception as e:
            logger.error(f"Error generando respuesta con GPT4All: {str(e)}")
            return {
                "success": False,
                "response": "Lo siento, hubo un error al procesar tu consulta. Por favor intenta nuevamente.",
                "error": str(e),
                "model_used": self.model_name,
                "context_used": 0,
                "sources": []
            }
    
    def _generate_with_gpt4all(self, prompt: str, fast_mode: bool = False) -> str:
        """
        Genera respuesta usando GPT4All
        
        Args:
            prompt: Prompt para el modelo
            fast_mode: Usar configuración rápida
            
        Returns:
            str: Respuesta generada
        """
        try:
            # Elegir configuración
            config = self.fast_config if fast_mode else self.generation_config
            
            # Generar respuesta
            with self.model.chat_session():
                response = self.model.generate(
                    prompt=prompt,
                    max_tokens=config['max_tokens'],
                    temp=config['temp'],
                    top_p=config['top_p'],
                    top_k=config['top_k'],
                    repeat_penalty=config['repeat_penalty']
                )
                
                if response and response.strip():
                    return response.strip()
                else:
                    return "Lo siento, no pude generar una respuesta válida."
                    
        except Exception as e:
            logger.error(f"Error en generación GPT4All: {str(e)}")
            raise e
    
    async def generate_title_for_conversation(
        self,
        first_message: str,
        max_length: int = 50
    ) -> str:
        """
        Genera un título conciso para una conversación
        
        Args:
            first_message: Primer mensaje de la conversación
            max_length: Longitud máxima del título
            
        Returns:
            str: Título generado
        """
        try:
            # Prompt conciso para generar títulos
            prompt = f"""Genera un título muy breve (máximo {max_length} caracteres) para esta conversación:

Mensaje: "{first_message[:100]}"

Título (solo el título, sin comillas):"""

            response = self._generate_with_gpt4all(prompt, fast_mode=True)
            
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
            "device": self.device,
            "max_tokens": self.generation_config.get('max_tokens'),
            "temperature": self.generation_config.get('temp'),
            "provider": "GPT4All Local",
            "available": self._check_model_available()
        }


# Instancia global del servicio
gpt4all_service = GPT4AllService()