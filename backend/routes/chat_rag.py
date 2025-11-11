from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from typing import Annotated, List, Optional
from datetime import datetime
from pydantic import BaseModel
import os

from database import get_db
from models import (
    User as UserModel, 
    CustomChatbot, 
    ChatbotAccess, 
    ChatbotDocument,
    Conversation as ConversationModel,
    ConversationParticipant as ConversationParticipantModel,
    Message as MessageModel,
    AccessLevel
)
from auth import get_current_user
from services.pinecone_service import pinecone_service
from services.groq_service import groq_service  # Groq - ultrarrápido y confiable
# from services.gemini_service import gemini_service  # Archivado - problemas con API Key
# from services.ollama_service import ollama_service  # Archivado - problemas de conectividad
# from services.gpt4all_service import gpt4all_service  # Archivado - problemas de memoria
from services.embedding_service import embedding_service

router = APIRouter(prefix="/api/chat", tags=["Chat with RAG"])

# Pydantic Models
class MessageCreate(BaseModel):
    text: str
    chatbot_id: Optional[int] = None

class MessageOut(BaseModel):
    id: int
    sender: str  # 'user' | 'ai'
    text: str
    created_at: datetime
    sources: List[str] = []

class ChatResponse(BaseModel):
    response: str
    sources: List[str] = []
    chatbot_used: Optional[str] = None
    context_chunks: int = 0

class ConversationCreate(BaseModel):
    title: Optional[str] = None
    chatbot_id: Optional[int] = None
    with_welcome: bool = True

class ConversationOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    chatbot_id: Optional[int] = None
    chatbot_name: Optional[str] = None


async def verify_chatbot_access(
    chatbot_id: int,
    user: UserModel,
    db: Session
) -> CustomChatbot:
    """Verifica que el usuario tenga acceso al chatbot"""
    
    chatbot = db.query(CustomChatbot).filter(
        CustomChatbot.id == chatbot_id,
        CustomChatbot.is_active == True
    ).first()
    
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot no encontrado o inactivo")
    
    # Propietario siempre tiene acceso
    if chatbot.created_by == user.id:
        return chatbot
    
    # Verificar acceso otorgado
    access_record = db.query(ChatbotAccess).filter(
        ChatbotAccess.chatbot_id == chatbot_id,
        ChatbotAccess.user_id == user.id
    ).first()
    
    if not access_record:
        raise HTTPException(status_code=403, detail="No tiene acceso a este chatbot")
    
    return chatbot


@router.post("/message", response_model=ChatResponse)
async def send_message_with_rag(
    payload: MessageCreate,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Enviar mensaje con búsqueda RAG en chatbot específico"""
    
    user_text = payload.text.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Mensaje vacío")
    # Detectar saludos simples y manejarlos localmente (persistentes)
    lower_text = user_text.lower()
    greetings = ["hola", "buenos", "buenas", "hi", "hello", "hey", "saludos"]
    is_greeting = any(g in lower_text for g in greetings) and len(user_text) <= 60
    if is_greeting:
        # Crear o recuperar conversación asociada al usuario y chatbot (si aplica)
        try:
            conversation = db.query(ConversationModel).filter(
                ConversationModel.user_id == current_user.id,
                ConversationModel.chatbot_id == payload.chatbot_id
            ).order_by(ConversationModel.updated_at.desc()).first()
            if not conversation:
                conv_title = f"Conversación - {payload.chatbot_id}" if payload.chatbot_id else "Nueva conversación"
                conversation = ConversationModel(
                    user_id=current_user.id,
                    chatbot_id=payload.chatbot_id,
                    title=conv_title
                )
                db.add(conversation)
                db.commit()
                db.refresh(conversation)

            # Guardar mensaje del usuario
            user_msg = MessageModel(
                conversation_id=conversation.id,
                sender="user",
                text=user_text
            )
            db.add(user_msg)

            # Preparar respuesta de saludo basada en documentos si hay chatbot
            reply = None
            sources = []
            if payload.chatbot_id:
                try:
                    chatbot = await verify_chatbot_access(payload.chatbot_id, current_user, db)
                    docs = db.query(ChatbotDocument).filter(
                        ChatbotDocument.chatbot_id == chatbot.id,
                        ChatbotDocument.is_processed == True
                    ).all()
                    filenames = [d.original_filename for d in docs] if docs else []
                    if filenames:
                        sources = filenames
                        reply = f"¡Hola! Puedo ayudarte basándome en los documentos cargados para este chatbot: {', '.join(filenames[:5])}. ¿En qué documento o tema te gustaría que me centre?"
                    else:
                        reply = f"¡Hola! Puedo ayudarte en general, pero actualmente no hay documentos procesados para el chatbot {chatbot.title}. Puedes subir documentos desde el panel de administración."
                except Exception:
                    reply = "¡Hola! Puedo ayudarte. No pude acceder a los documentos en este momento."
            else:
                reply = "¡Hola! Puedo ayudarte. ¿Sobre qué te gustaría conversar?"

            # Guardar respuesta de la IA
            ai_msg = MessageModel(
                conversation_id=conversation.id,
                sender="ai",
                text=reply
            )
            db.add(ai_msg)
            conversation.updated_at = datetime.utcnow()
            db.commit()

            return ChatResponse(
                response=reply,
                sources=sources,
                chatbot_used=(chatbot.title if payload.chatbot_id and 'chatbot' in locals() else None),
                context_chunks=0
            )
        except Exception as e:
            print(f"Error manejando saludo: {str(e)}")
            # continuar con el flujo normal si hay error en manejo del saludo
    
    chatbot = None
    chatbot_name = "Asistente General"
    context_chunks = []
    
    # Si se especifica un chatbot, usar RAG
    if payload.chatbot_id:
        chatbot = await verify_chatbot_access(payload.chatbot_id, current_user, db)
        chatbot_name = chatbot.title
        
        try:
            # Generar embedding de la pregunta del usuario
            query_embedding = await embedding_service.generate_single_embedding(user_text)
            
            if query_embedding:
                # Buscar contexto relevante en Pinecone
                search_results = await pinecone_service.query_vectors(
                    index_name=chatbot.pinecone_index_name,
                    query_vector=query_embedding,
                    top_k=int(os.getenv("TOP_K_RESULTS", "5")),
                    namespace=f"chatbot_{chatbot.id}"
                )
                
                # Filtrar resultados con umbral más estricto de similitud semántica
                min_score = 0.65  # Umbral más alto para asegurar relevancia
                context_chunks = [
                    result for result in search_results 
                    if result.get("score", 0) >= min_score
                ]
                
                if not context_chunks:
                    # Si no hay contexto relevante, permitir respuestas conversacionales simples
                    # Detectar saludos u mensajes cortos para ofrecer ayuda basada en los documentos
                    lower_text = user_text.lower()
                    greetings = ["hola", "buenos", "buenas", "hi", "hello", "hey", "saludos"]
                    is_greeting = any(g in lower_text for g in greetings) and len(user_text) <= 40

                    if is_greeting:
                        try:
                            # Obtener lista de documentos asociados al chatbot
                            docs = db.query(ChatbotDocument).filter(ChatbotDocument.chatbot_id == chatbot.id).all()
                            filenames = [d.original_filename for d in docs] if docs else []
                            if filenames:
                                sources_text = ", ".join(filenames)
                                reply = f"¡Hola! Puedo ayudarte basándome en los documentos cargados para este chatbot: {sources_text}. Hazme una pregunta específica sobre esos documentos."
                                return ChatResponse(
                                    response=reply,
                                    sources=filenames,
                                    chatbot_used=chatbot_name,
                                    context_chunks=0
                                )
                            else:
                                return ChatResponse(
                                    response="¡Hola! Puedo ayudarte. Actualmente no hay documentos procesados para este chatbot. Sube un documento o hazme una pregunta sobre los archivos cargados.",
                                    sources=[],
                                    chatbot_used=chatbot_name,
                                    context_chunks=0
                                )
                        except Exception:
                            return ChatResponse(
                                response="¡Hola! Puedo ayudarte. No pude recuperar la lista de documentos en este momento.",
                                sources=[],
                                chatbot_used=chatbot_name,
                                context_chunks=0
                            )
                    # Si no es un saludo, mantener la política de no responder fuera del contexto
                    out_of_context_msg = 'Lo siento, no puedo responder a algo que no sea del "contexto de archivo cargado".'
                    return ChatResponse(
                        response=out_of_context_msg,
                        sources=[],
                        chatbot_used=chatbot_name,
                        context_chunks=0
                    )
                
        except Exception as e:
            print(f"Error en búsqueda RAG: {str(e)}")
            # Continuar sin contexto en caso de error

        # Buscar o crear una conversación persistente para este usuario + chatbot
        conversation = None
        try:
            conversation = db.query(ConversationModel).filter(
                ConversationModel.user_id == current_user.id,
                ConversationModel.chatbot_id == payload.chatbot_id
            ).order_by(ConversationModel.updated_at.desc()).first()

            if not conversation:
                # Crear conversación inicial
                conv_title = f"Conversación - {chatbot_name}" if chatbot_name else "Nueva conversación"
                conversation = ConversationModel(
                    user_id=current_user.id,
                    chatbot_id=payload.chatbot_id,
                    title=conv_title
                )
                db.add(conversation)
                db.commit()
                db.refresh(conversation)

            # Guardar mensaje del usuario en la conversación
            user_msg = MessageModel(
                conversation_id=conversation.id,
                sender="user",
                text=user_text
            )
            db.add(user_msg)
            conversation.updated_at = datetime.utcnow()
            db.commit()
        except Exception as e:
            print(f"No se pudo crear/guardar la conversación: {str(e)}")

        # Reconstruir historial reciente para pasar al generador de la IA
        recent_messages = db.query(MessageModel).filter(
            MessageModel.conversation_id == conversation.id
        ).order_by(MessageModel.created_at.desc()).limit(6).all()  # Últimos 6 mensajes

        conversation_history = []
        for msg in reversed(recent_messages[1:]):  # Excluir mensaje actual
            conversation_history.append({
                "sender": msg.sender,
                "text": msg.text
            })
    
    # Generar respuesta usando Groq (ultrarrápido y confiable)
    try:
        response_data = await groq_service.generate_response(
            user_question=user_text,
            context_chunks=context_chunks,
            chatbot_name=chatbot_name,
            conversation_history=conversation_history if 'conversation_history' in locals() else None
        )
        
        # Códigos archivados:
        # response_data = await gemini_service.generate_response(...)  # Problemas API Key
        # response_data = await gpt4all_service.generate_response(...)  # Problemas memoria
        
        ai_response = None
        sources = []
        out_of_context_msg = 'Lo siento, no puedo responder a algo que no sea del "contexto de archivo cargado".'
        if response_data.get("success"):
            ai_response = response_data.get("response", "")
            sources = response_data.get("sources", [])
        else:
            raw_resp = response_data.get("response", "Lo siento, hubo un error procesando tu consulta.")
            lower_raw = raw_resp.lower() if isinstance(raw_resp, str) else ""
            # Si el servicio indica que no hay información relevante, mapear a mensaje de contexto
            if any(kw in lower_raw for kw in ["no hay información relevante", "no puedo responder", "fuera del alcance", "no hay información"]):
                ai_response = out_of_context_msg
            else:
                ai_response = raw_resp
            sources = response_data.get("sources", []) if response_data.get("sources") else []

        # Si la respuesta es una negativa/muy corta, intentar regenerar automáticamente una vez
        try:
            bad_patterns = ["no puedo responder", "no puedo generar", "no pude generar", "no pude procesar", "Lo siento"]
            should_retry = False
            if not ai_response or len(ai_response.strip()) < 40:
                should_retry = True
            else:
                lower = ai_response.lower()
                if any(pat in lower for pat in bad_patterns):
                    should_retry = True

            if should_retry:
                retry_data = await groq_service.generate_response(
                    user_question=user_text,
                    context_chunks=context_chunks,
                    chatbot_name=chatbot_name,
                    conversation_history=conversation_history if 'conversation_history' in locals() else None
                )
                if retry_data.get("success") and retry_data.get("response"):
                    ai_response = retry_data.get("response")
                    sources = retry_data.get("sources", [])
        except Exception as e:
            print(f"Retry generacion fallo: {str(e)}")
            # Intento automático adicional en caso de fallo inicial
            try:
                retry_data = await groq_service.generate_response(
                    user_question=user_text,
                    context_chunks=context_chunks,
                    chatbot_name=chatbot_name,
                    conversation_history=conversation_history if 'conversation_history' in locals() else None
                )
                if retry_data.get("success") and retry_data.get("response"):
                    ai_response = retry_data.get("response")
                    sources = retry_data.get("sources", [])
            except Exception as e:
                print(f"Retry generacion fallo: {str(e)}")
            
    except Exception as e:
        print(f"Error generando respuesta: {str(e)}")
        ai_response = "Lo siento, no pude procesar tu mensaje en este momento."
        sources = []
    
    # Si existe una conversación persistente, guardar la respuesta de la IA
    try:
        if 'conversation' in locals() and conversation:
            ai_msg = MessageModel(
                conversation_id=conversation.id,
                sender="ai",
                text=ai_response
            )
            db.add(ai_msg)
            conversation.updated_at = datetime.utcnow()
            db.commit()
    except Exception as e:
        print(f"No se pudo guardar el mensaje de IA: {str(e)}")

    return ChatResponse(
        response=ai_response,
        sources=sources,
        chatbot_used=chatbot_name if chatbot else None,
        context_chunks=len(context_chunks)
    )


@router.post("/conversations", response_model=ConversationOut, status_code=201)
async def create_conversation_with_chatbot(
    payload: ConversationCreate,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Crear nueva conversación, opcionalmente vinculada a un chatbot"""
    
    chatbot = None
    chatbot_name = None
    
    # Verificar acceso al chatbot si se especifica
    if payload.chatbot_id:
        chatbot = await verify_chatbot_access(payload.chatbot_id, current_user, db)
        chatbot_name = chatbot.title
    
    # Generar título si no se proporciona
    title = payload.title
    if not title:
        if chatbot:
            title = f"Conversación - {chatbot.title}"
        else:
            title = "Nueva conversación"
    
    # Crear conversación
    conversation = ConversationModel(
        user_id=current_user.id,
        chatbot_id=payload.chatbot_id,
        title=title
    )
    
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    # Mensaje de bienvenida
    if payload.with_welcome:
        if chatbot:
            # Obtener documentos procesados para este chatbot
            try:
                docs = db.query(ChatbotDocument).filter(
                    ChatbotDocument.chatbot_id == chatbot.id,
                    ChatbotDocument.is_processed == True
                ).all()
                filenames = [d.original_filename for d in docs] if docs else []
            except Exception:
                filenames = []

            if filenames:
                sources_text = ", ".join(filenames[:5])
                welcome_text = (
                    f"¡Hola! Soy tu asistente especializado en {chatbot.title}. "
                    f"Puedo ayudarte en el contexto de los documentos cargados: {sources_text}. "
                    "Hazme una pregunta específica sobre esos documentos."
                )
            else:
                welcome_text = (
                    f"¡Hola! Soy tu asistente especializado en {chatbot.title}. "
                    "Actualmente no hay documentos procesados para este chatbot. Puedes subir documentos desde el panel de administración."
                )
        else:
            welcome_text = "¡Hola! Soy tu asistente de IA. ¿Cómo puedo ayudarte hoy?"

        welcome_msg = MessageModel(
            conversation_id=conversation.id,
            sender="ai", 
            text=welcome_text
        )
        db.add(welcome_msg)
        conversation.updated_at = datetime.utcnow()
        db.commit()
    
    return ConversationOut(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        chatbot_id=conversation.chatbot_id,
        chatbot_name=chatbot_name
    )


@router.post("/conversations/{conversation_id}/messages", response_model=ChatResponse)
async def send_message_to_conversation(
    payload: MessageCreate,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    conversation_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """Enviar mensaje a una conversación existente"""
    
    # Verificar que la conversación existe y el usuario tiene acceso
    conversation = db.query(ConversationModel).filter(
        ConversationModel.id == conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    # Verificar acceso: propietario o participante
    if conversation.user_id != current_user.id:
        participant = db.query(ConversationParticipantModel).filter(
            ConversationParticipantModel.conversation_id == conversation.id,
            ConversationParticipantModel.user_id == current_user.id
        ).first()
        if not participant:
            raise HTTPException(status_code=403, detail="No tiene acceso a esta conversación")
    
    user_text = payload.text.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Mensaje vacío")
    
    # Guardar mensaje del usuario
    user_msg = MessageModel(
        conversation_id=conversation.id,
        sender="user",
        text=user_text
    )
    db.add(user_msg)
    db.commit()

    # Detectar saludo y responder localmente si corresponde
    lower_text = user_text.lower()
    greetings = ["hola", "buenos", "buenas", "hi", "hello", "hey", "saludos"]
    is_greeting = any(g in lower_text for g in greetings) and len(user_text) <= 60
    if is_greeting:
        try:
            reply = None
            sources = []
            if conversation.chatbot_id:
                try:
                    chatbot = db.query(CustomChatbot).filter(CustomChatbot.id == conversation.chatbot_id).first()
                    docs = db.query(ChatbotDocument).filter(
                        ChatbotDocument.chatbot_id == conversation.chatbot_id,
                        ChatbotDocument.is_processed == True
                    ).all()
                    filenames = [d.original_filename for d in docs] if docs else []
                    if filenames:
                        sources = filenames
                        reply = f"¡Hola! Puedo ayudarte basándome en los documentos cargados: {', '.join(filenames[:5])}. ¿En qué documento o tema te gustaría que me centre?"
                    else:
                        reply = f"¡Hola! Estoy listo para ayudar, pero no hay documentos procesados para este chatbot."
                except Exception:
                    reply = "¡Hola! Puedo ayudarte. No pude acceder a los documentos en este momento."
            else:
                reply = "¡Hola! ¿En qué puedo ayudarte hoy?"

            ai_msg = MessageModel(
                conversation_id=conversation.id,
                sender="ai",
                text=reply
            )
            db.add(ai_msg)
            conversation.updated_at = datetime.utcnow()
            db.commit()

            return ChatResponse(
                response=reply,
                sources=sources,
                chatbot_used=(chatbot.title if conversation.chatbot_id and 'chatbot' in locals() else None),
                context_chunks=0
            )
        except Exception as e:
            print(f"Error manejando saludo en conversación: {str(e)}")
    
    chatbot = None
    chatbot_name = "Asistente General"
    context_chunks = []
    
    # Si la conversación está vinculada a un chatbot, usar RAG
    if conversation.chatbot_id:
        try:
            chatbot = await verify_chatbot_access(conversation.chatbot_id, current_user, db)
            chatbot_name = chatbot.title
            
            # Generar embedding de la pregunta
            query_embedding = await embedding_service.generate_single_embedding(user_text)
            
            if query_embedding:
                # Buscar contexto en Pinecone
                search_results = await pinecone_service.query_vectors(
                    index_name=chatbot.pinecone_index_name,
                    query_vector=query_embedding,
                    top_k=int(os.getenv("TOP_K_RESULTS", "5")),
                    namespace=f"chatbot_{chatbot.id}"
                )
                
                # Filtrar por score mínimo
                min_score = 0.45  # Ajustado para obtener más resultados relevantes
                context_chunks = [
                    result for result in search_results 
                    if result.get("score", 0) >= min_score
                ]

                if not context_chunks:
                    # Intentar fallback si hay resultados (usar top-k sin filtrar)
                    if search_results:
                        fallback_k = int(os.getenv("FALLBACK_TOP_K", "3"))
                        sorted_results = sorted(search_results, key=lambda r: r.get("score", 0), reverse=True)
                        context_chunks = sorted_results[:fallback_k]
                        print(f"[RAG FALLBACK CONV] usando {len(context_chunks)} chunks de fallback (scores: {[c.get('score') for c in context_chunks]})")
                    # si no hay search_results, context_chunks se queda vacío y se seguirá la lógica posterior
                
        except Exception as e:
            print(f"Error en RAG para conversación: {str(e)}")
    
    # Obtener historial de la conversación para contexto
    recent_messages = db.query(MessageModel).filter(
        MessageModel.conversation_id == conversation.id
    ).order_by(MessageModel.created_at.desc()).limit(6).all()  # Últimos 6 mensajes
    
    conversation_history = []
    for msg in reversed(recent_messages[1:]):  # Excluir mensaje actual
        conversation_history.append({
            "sender": msg.sender,
            "text": msg.text
        })
    
    # Generar respuesta con Groq (ultrarrápido y confiable)
    try:
        response_data = await groq_service.generate_response(
            user_question=user_text,
            context_chunks=context_chunks,
            chatbot_name=chatbot_name,
            conversation_history=conversation_history
        )
        
        # Códigos archivados:
        # response_data = await gemini_service.generate_response(...)  # Problemas API Key
        # response_data = await gpt4all_service.generate_response(...)  # Problemas memoria
        
        out_of_context_msg = 'Lo siento, no puedo responder a algo que no sea del "contexto de archivo cargado".'
        if response_data.get("success"):
            ai_response = response_data.get("response", "")
            sources = response_data.get("sources", [])
        else:
            raw_resp = response_data.get("response", "Lo siento, hubo un error procesando tu consulta.")
            lower_raw = raw_resp.lower() if isinstance(raw_resp, str) else ""
            if any(kw in lower_raw for kw in ["no hay información relevante", "no puedo responder", "fuera del alcance", "no hay información"]):
                ai_response = out_of_context_msg
            else:
                ai_response = raw_resp
            sources = response_data.get("sources", []) if response_data.get("sources") else []
            
    except Exception as e:
        print(f"Error generando respuesta: {str(e)}")
        ai_response = "Lo siento, no pude procesar tu mensaje."
        sources = []
    
    # Guardar respuesta de la IA
    ai_msg = MessageModel(
        conversation_id=conversation.id,
        sender="ai",
        text=ai_response
    )
    db.add(ai_msg)
    
    # Actualizar timestamp de conversación
    conversation.updated_at = datetime.utcnow()
    db.commit()
    
    return ChatResponse(
        response=ai_response,
        sources=sources,
        chatbot_used=chatbot_name,
        context_chunks=len(context_chunks)
    )


@router.get("/conversations", response_model=List[ConversationOut])
async def list_user_conversations(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Listar conversaciones del usuario con información del chatbot"""
    
    # Conversaciones del usuario como propietario
    owned_conversations = db.query(ConversationModel).filter(
        ConversationModel.user_id == current_user.id
    ).all()

    # Conversaciones donde es participante
    participant_links = db.query(ConversationParticipantModel).filter(
        ConversationParticipantModel.user_id == current_user.id
    ).all()
    participant_conv_ids = [p.conversation_id for p in participant_links]
    participant_conversations = (
        db.query(ConversationModel)
        .filter(ConversationModel.id.in_(participant_conv_ids))
        .all()
        if participant_conv_ids else []
    )

    # Combinar y ordenar por updated_at desc, sin duplicados
    conv_map = {c.id: c for c in owned_conversations + participant_conversations}
    conversations = sorted(conv_map.values(), key=lambda c: c.updated_at, reverse=True)
    
    result = []
    for conv in conversations:
        chatbot_name = None
        if conv.chatbot_id:
            chatbot = db.query(CustomChatbot).filter(
                CustomChatbot.id == conv.chatbot_id
            ).first()
            if chatbot:
                chatbot_name = chatbot.title
        
        result.append(ConversationOut(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            chatbot_id=conv.chatbot_id,
            chatbot_name=chatbot_name
        ))
    
    return result


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageOut])
async def get_conversation_messages(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    conversation_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """Obtener mensajes de una conversación"""
    
    conversation = db.query(ConversationModel).filter(
        ConversationModel.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    # Verificar acceso: propietario o participante
    if conversation.user_id != current_user.id:
        participant = db.query(ConversationParticipantModel).filter(
            ConversationParticipantModel.conversation_id == conversation.id,
            ConversationParticipantModel.user_id == current_user.id
        ).first()
        if not participant:
            raise HTTPException(status_code=403, detail="No tiene acceso a esta conversación")
    
    messages = db.query(MessageModel).filter(
        MessageModel.conversation_id == conversation_id
    ).order_by(MessageModel.created_at.asc()).all()
    # Si no hay mensajes (por ejemplo conversación creada pero sin seed), crear mensaje de bienvenida
    if not messages:
        try:
            chatbot_name = None
            if conversation.chatbot_id:
                chatbot = db.query(CustomChatbot).filter(CustomChatbot.id == conversation.chatbot_id).first()
                chatbot_name = chatbot.title if chatbot else None

                # Obtener documentos procesados
                docs = db.query(ChatbotDocument).filter(
                    ChatbotDocument.chatbot_id == conversation.chatbot_id,
                    ChatbotDocument.is_processed == True
                ).all()
                filenames = [d.original_filename for d in docs] if docs else []
            else:
                filenames = []

            if chatbot_name:
                if filenames:
                    sources_text = ", ".join(filenames[:5])
                    welcome_text = (
                        f"¡Hola! Soy tu asistente especializado en {chatbot_name}. "
                        f"Puedo ayudarte en el contexto de los documentos cargados: {sources_text}. "
                        "Hazme una pregunta específica sobre esos documentos."
                    )
                else:
                    welcome_text = (
                        f"¡Hola! Soy tu asistente especializado en {chatbot_name}. "
                        "Actualmente no hay documentos procesados para este chatbot. Puedes subir documentos desde el panel de administración."
                    )
            else:
                welcome_text = "¡Hola! Soy tu asistente de IA. ¿Cómo puedo ayudarte hoy?"

            welcome_msg = MessageModel(
                conversation_id=conversation.id,
                sender="ai",
                text=welcome_text
            )
            db.add(welcome_msg)
            db.commit()
            messages = [welcome_msg]
        except Exception as e:
            print(f"Error creando mensaje de bienvenida automático: {str(e)}")

    return [
        MessageOut(
            id=msg.id,
            sender=msg.sender,
            text=msg.text,
            created_at=msg.created_at,
            sources=[]  # TODO: guardar fuentes en base de datos si es necesario
        )
        for msg in messages
    ]


@router.get("/available-chatbots")
async def get_available_chatbots(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Obtener lista de chatbots disponibles para el usuario"""
    
    # Chatbots creados por el usuario
    owned_chatbots = db.query(CustomChatbot).filter(
        CustomChatbot.created_by == current_user.id,
        CustomChatbot.is_active == True
    ).all()
    
    # Chatbots con acceso otorgado
    access_records = db.query(ChatbotAccess).filter(
        ChatbotAccess.user_id == current_user.id
    ).all()
    
    accessible_ids = [access.chatbot_id for access in access_records]
    accessible_chatbots = db.query(CustomChatbot).filter(
        CustomChatbot.id.in_(accessible_ids),
        CustomChatbot.is_active == True
    ).all() if accessible_ids else []
    
    # Combinar y eliminar duplicados
    all_chatbots = {cb.id: cb for cb in owned_chatbots + accessible_chatbots}.values()
    
    return [
        {
            "id": chatbot.id,
            "title": chatbot.title,
            "description": chatbot.description,
            "is_owner": chatbot.created_by == current_user.id
        }
        for chatbot in sorted(all_chatbots, key=lambda x: x.title)
    ]


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    conversation_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """Eliminar una conversación y todos sus mensajes"""
    
    # Verificar que la conversación existe y el usuario tiene acceso
    conversation = db.query(ConversationModel).filter(
        ConversationModel.id == conversation_id,
        ConversationModel.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    try:
        # Eliminar todos los mensajes de la conversación
        db.query(MessageModel).filter(
            MessageModel.conversation_id == conversation_id
        ).delete()
        
        # Eliminar la conversación
        db.delete(conversation)
        db.commit()
        
        return {"message": "Conversación eliminada exitosamente"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Error eliminando conversación: {str(e)}"
        )


@router.patch("/conversations/{conversation_id}")
async def update_conversation(
    payload: dict,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    conversation_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """Actualizar título de una conversación"""
    
    # Verificar que la conversación existe y el usuario tiene acceso
    conversation = db.query(ConversationModel).filter(
        ConversationModel.id == conversation_id,
        ConversationModel.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    # Actualizar título si se proporciona
    if "title" in payload:
        conversation.title = payload["title"]
        conversation.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(conversation)
    
    # Obtener nombre del chatbot si aplica
    chatbot_name = None
    if conversation.chatbot_id:
        chatbot = db.query(CustomChatbot).filter(
            CustomChatbot.id == conversation.chatbot_id
        ).first()
        if chatbot:
            chatbot_name = chatbot.title
    
    return ConversationOut(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        chatbot_id=conversation.chatbot_id,
        chatbot_name=chatbot_name
    )


# Importar os para variables de entorno
import os