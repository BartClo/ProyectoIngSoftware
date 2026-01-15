from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import Annotated, List, Optional
from datetime import datetime
from pydantic import BaseModel
import os
import logging

from database import get_db
from models import (
    User as UserModel, 
    CustomChatbot, 
    ChatbotAccess, 
    Conversation as ConversationModel,
    Message as MessageModel,
    AccessLevel,
    ChatbotDocument
)
from auth import get_current_user
from services.pinecone_service import pinecone_service
from services.groq_service import groq_service
from services.embedding_service_pinecone import embedding_service

logger = logging.getLogger(__name__)

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
    db: AsyncSession
) -> CustomChatbot:
    """Verifica que el usuario tenga acceso al chatbot (Async)"""
    
    result = await db.execute(select(CustomChatbot).where(
        CustomChatbot.id == chatbot_id,
        CustomChatbot.is_active == True
    ))
    chatbot = result.scalar_one_or_none()
    
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot no encontrado o inactivo")
    
    # Propietario siempre tiene acceso
    if chatbot.created_by == user.id:
        return chatbot
    
    # Verificar acceso otorgado
    result_access = await db.execute(select(ChatbotAccess).where(
        ChatbotAccess.chatbot_id == chatbot_id,
        ChatbotAccess.user_id == user.id
    ))
    access_record = result_access.scalar_one_or_none()
    
    if not access_record:
        raise HTTPException(status_code=403, detail="No tiene acceso a este chatbot")
    
    return chatbot


@router.post("/message", response_model=ChatResponse)
async def send_message_with_rag(
    payload: MessageCreate,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Enviar mensaje con búsqueda RAG en chatbot específico"""
    
    user_text = payload.text.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Mensaje vacío")
    
    # Detectar saludos y respuestas simples (no requieren búsqueda RAG)
    greetings = ["hola", "hello", "hi", "buenos días", "buenas tardes", "buenas noches", "hey", "saludos"]
    thanks = ["gracias", "thank you", "thanks", "muchas gracias"]
    is_greeting = any(greeting in user_text.lower() for greeting in greetings)
    is_thanks = any(thank in user_text.lower() for thank in thanks)
    
    chatbot = None
    chatbot_name = "Asistente General"
    context_chunks = []
    
    # Obtener información del chatbot si se especifica
    if payload.chatbot_id:
        chatbot = await verify_chatbot_access(payload.chatbot_id, current_user, db)
        chatbot_name = chatbot.title
    
    # Respuesta directa para saludos simples
    if is_greeting and len(user_text.split()) <= 3:
        files_info = ""
        if chatbot:
            result = await db.execute(select(ChatbotDocument).where(
                ChatbotDocument.chatbot_id == chatbot.id,
                ChatbotDocument.is_processed == True
            ))
            documents = result.scalars().all()
            
            if documents:
                file_names = [doc.original_filename for doc in documents]
                files_text = ", ".join(file_names)
                files_info = f"\n\nTengo acceso a: {files_text}. ¿Qué te gustaría saber sobre ellos?"
        
        return ChatResponse(
            response=f"¡Hola! ¿En qué puedo ayudarte?{files_info}",
            sources=[],
            chatbot_used=chatbot_name,
            context_chunks=0
        )
    
    # Respuesta directa para agradecimientos
    if is_thanks and len(user_text.split()) <= 5:
        return ChatResponse(
            response="¡De nada! ¿Hay algo más en lo que pueda ayudarte?",
            sources=[],
            chatbot_used=chatbot_name,
            context_chunks=0
        )
    
    # Si se especifica un chatbot, usar RAG
    if payload.chatbot_id:
        chatbot = await verify_chatbot_access(payload.chatbot_id, current_user, db)
        chatbot_name = chatbot.title
        
        try:
            # Generar embedding de la pregunta del usuario
            query_embedding = await embedding_service.generate_query_embedding(user_text)
            
            if query_embedding:
                # Buscar contexto relevante en Pinecone
                search_results = await pinecone_service.query_vectors(
                    index_name=chatbot.pinecone_index_name,
                    query_vector=query_embedding,
                    top_k=int(os.getenv("TOP_K_RESULTS", "5")),
                    namespace=f"chatbot_{chatbot.id}"
                )
                
                # Filtrar resultados por score mínimo
                min_score = 0.70
                context_chunks = [
                    result for result in search_results 
                    if result.get("score", 0) >= min_score
                ]
                
                # Debug: mostrar scores de resultados
                if search_results:
                    logger.info(f"🔍 Búsqueda RAG para: '{user_text}'")
                    for i, result in enumerate(search_results[:3]):
                        score = result.get('score', 0)
                        source = result.get('metadata', {}).get('source', 'N/A')
                        logger.info(f"   Resultado {i+1}: score={score:.3f}, fuente={source}")
                    logger.info(f"   ✅ {len(context_chunks)} chunks pasaron el umbral de {min_score}")
                
        except Exception as e:
            logger.error(f"Error en búsqueda RAG: {str(e)}")
            # Continuar sin contexto en caso de error (Graceful degradation)
    
    # Generar respuesta usando Groq (ultrarrápido y confiable)
    try:
        # Verificar si el chatbot tiene documentos cargados
        has_documents = False
        if chatbot:
            doc_count_res = await db.execute(select(func.count(ChatbotDocument.id)).where(
                ChatbotDocument.chatbot_id == chatbot.id,
                ChatbotDocument.is_processed == True
            ))
            has_documents = doc_count_res.scalar() > 0
        
        response_data = await groq_service.generate_response(
            user_question=user_text,
            context_chunks=context_chunks,
            chatbot_name=chatbot_name,
            has_documents=has_documents
        )
        
        if response_data.get("success"):
            ai_response = response_data.get("response", "")
            sources = response_data.get("sources", [])
        else:
            ai_response = "Lo siento, hubo un error procesando tu consulta."
            sources = []
            
    except Exception as e:
        logger.error(f"Error generando respuesta: {str(e)}")
        ai_response = "Lo siento, no pude procesar tu mensaje en este momento."
        sources = []
    
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
    db: AsyncSession = Depends(get_db)
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
    await db.commit()
    await db.refresh(conversation)
    
    # Mensaje de bienvenida
    if payload.with_welcome:
        if chatbot:
            # Obtener lista de documentos del chatbot
            result = await db.execute(select(ChatbotDocument).where(
                ChatbotDocument.chatbot_id == chatbot.id,
                ChatbotDocument.is_processed == True
            ))
            documents = result.scalars().all()
            
            if documents:
                # Crear lista de nombres de archivos
                file_names = [doc.original_filename for doc in documents]
                files_text = "\n".join([f"📄 {name}" for name in file_names])
                
                # Intentar obtener un resumen del contenido
                try:
                    # Hacer una búsqueda general
                    sample_embedding = await embedding_service.generate_query_embedding(
                        "resumen contenido principal documentos"
                    )
                    
                    if sample_embedding:
                        sample_results = await pinecone_service.query_vectors(
                            index_name=chatbot.pinecone_index_name,
                            query_vector=sample_embedding,
                            top_k=3,
                            namespace=f"chatbot_{chatbot.id}"
                        )
                        
                        # Obtener temas principales de los metadatos
                        topics = set()
                        for result in sample_results:
                            metadata = result.get('metadata', {})
                            text_sample = metadata.get('text', '')[:200]
                            if text_sample:
                                topics.add(text_sample.split('.')[0] if '.' in text_sample else text_sample[:100])
                        
                        topics_text = ""
                        if topics:
                            topics_list = list(topics)[:2]  # Máximo 2 temas
                            topics_text = f"\n\nEstos documentos contienen información sobre:\n" + "\n".join([f"• {t}" for t in topics_list])
                
                except Exception as e:
                    logger.error(f"Error obteniendo resumen de documentos: {str(e)}")
                    topics_text = ""
                
                welcome_text = (
                    f"¡Hola! Soy {chatbot.title}, tu asistente especializado.\n\n"
                    f"Tengo acceso a los siguientes documentos:\n{files_text}"
                    f"{topics_text}\n\n"
                    f"¿Qué te gustaría saber? Puedo ayudarte con cualquier pregunta sobre el contenido de estos archivos."
                )
            else:
                welcome_text = (
                    f"¡Hola! Soy {chatbot.title}. "
                    f"Actualmente no tengo documentos cargados, pero estoy listo para ayudarte."
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
        await db.commit()
    
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
    db: AsyncSession = Depends(get_db)
):
    """Enviar mensaje a una conversación existente"""
    
    # Verificar que la conversación existe y el usuario tiene acceso
    result = await db.execute(select(ConversationModel).where(
        ConversationModel.id == conversation_id
    ))
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    # Verificar acceso (propietario o participante)
    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tiene acceso a esta conversación")
    
    user_text = payload.text.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Mensaje vacío")
    
    # Detectar saludos y respuestas simples (no requieren búsqueda RAG)
    greetings = ["hola", "hello", "hi", "buenos días", "buenas tardes", "buenas noches", "hey", "saludos"]
    thanks = ["gracias", "thank you", "thanks", "muchas gracias"]
    is_greeting = any(greeting in user_text.lower() for greeting in greetings)
    is_thanks = any(thank in user_text.lower() for thank in thanks)
    
    # Guardar mensaje del usuario
    user_msg = MessageModel(
        conversation_id=conversation.id,
        sender="user",
        text=user_text
    )
    db.add(user_msg)
    await db.commit()
    
    chatbot = None
    chatbot_name = "Asistente General"
    context_chunks = []
    
    # Obtener información del chatbot si existe
    if conversation.chatbot_id:
        chatbot = await verify_chatbot_access(conversation.chatbot_id, current_user, db)
        chatbot_name = chatbot.title
    
    # Respuesta directa para saludos simples
    if is_greeting and len(user_text.split()) <= 3:
        # Obtener lista de archivos si hay chatbot
        files_info = ""
        if chatbot:
            result = await db.execute(select(ChatbotDocument).where(
                ChatbotDocument.chatbot_id == chatbot.id,
                ChatbotDocument.is_processed == True
            ))
            documents = result.scalars().all()
            
            if documents:
                file_names = [doc.original_filename for doc in documents]
                files_text = ", ".join(file_names)
                files_info = f"\n\nTengo acceso a: {files_text}. ¿Qué te gustaría saber sobre ellos?"
        
        greeting_response = f"¡Hola! ¿En qué puedo ayudarte?{files_info}"
        
        # Guardar respuesta
        ai_msg = MessageModel(
            conversation_id=conversation.id,
            sender="ai",
            text=greeting_response
        )
        db.add(ai_msg)
        conversation.updated_at = datetime.utcnow()
        await db.commit()
        
        return ChatResponse(
            response=greeting_response,
            sources=[],
            chatbot_used=chatbot_name,
            context_chunks=0
        )
    
    # Respuesta directa para agradecimientos
    if is_thanks and len(user_text.split()) <= 5:
        thanks_response = "¡De nada! ¿Hay algo más en lo que pueda ayudarte?"
        
        # Guardar respuesta
        ai_msg = MessageModel(
            conversation_id=conversation.id,
            sender="ai",
            text=thanks_response
        )
        db.add(ai_msg)
        conversation.updated_at = datetime.utcnow()
        db.commit()
        
        return ChatResponse(
            response=thanks_response,
            sources=[],
            chatbot_used=chatbot_name,
            context_chunks=0
        )
    
    # Si la conversación está vinculada a un chatbot, usar RAG
    if conversation.chatbot_id:
        try:
            chatbot = await verify_chatbot_access(conversation.chatbot_id, current_user, db)
            chatbot_name = chatbot.title
            
            # Generar embedding de la pregunta
            query_embedding = await embedding_service.generate_query_embedding(user_text)
            
            if query_embedding:
                # Buscar contexto en Pinecone
                search_results = await pinecone_service.query_vectors(
                    index_name=chatbot.pinecone_index_name,
                    query_vector=query_embedding,
                    top_k=int(os.getenv("TOP_K_RESULTS", "5")),
                    namespace=f"chatbot_{chatbot.id}"
                )
                
                # Filtrar por score mínimo
                # Usar umbral más alto para evitar falsos positivos
                min_score = 0.70  # ✅ Score alto para asegurar relevancia real
                context_chunks = [
                    result for result in search_results 
                    if result.get("score", 0) >= min_score
                ]
                
                # Debug: mostrar scores de resultados
                if search_results:
                    print(f"🔍 Búsqueda RAG (conversación {conversation_id}): '{user_text}'")
                    for i, result in enumerate(search_results[:3]):
                        score = result.get('score', 0)
                        source = result.get('metadata', {}).get('source', 'N/A')
                        print(f"   Resultado {i+1}: score={score:.3f}, fuente={source}")
                    print(f"   ✅ {len(context_chunks)} chunks pasaron el umbral de {min_score}")
                    if len(context_chunks) == 0 and search_results:
                        max_score = max(r.get('score', 0) for r in search_results)
                        print(f"   ⚠️ Score más alto ({max_score:.3f}) está por debajo del umbral - pregunta probablemente no relacionada")
                
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
        # Verificar si el chatbot tiene documentos cargados
        has_documents = False
        if chatbot:
            from models import ChatbotDocument
            doc_count = db.query(ChatbotDocument).filter(
                ChatbotDocument.chatbot_id == chatbot.id,
                ChatbotDocument.is_processed == True
            ).count()
            has_documents = doc_count > 0
        
        response_data = await groq_service.generate_response(
            user_question=user_text,
            context_chunks=context_chunks,
            chatbot_name=chatbot_name,
            conversation_history=conversation_history,
            has_documents=has_documents
        )
        
        if response_data.get("success"):
            ai_response = response_data.get("response", "")
            sources = response_data.get("sources", [])
        else:
            ai_response = "Lo siento, hubo un error procesando tu consulta."
            sources = []
            
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
    db: AsyncSession = Depends(get_db)
):
    """Listar conversaciones del usuario con información del chatbot"""
    
    result = await db.execute(select(ConversationModel).where(
        ConversationModel.user_id == current_user.id
    ).order_by(desc(ConversationModel.updated_at)))
    conversations = result.scalars().all()
    
    result_list = []
    for conv in conversations:
        chatbot_name = None
        if conv.chatbot_id:
            res = await db.execute(select(CustomChatbot).where(
                CustomChatbot.id == conv.chatbot_id
            ))
            chatbot = res.scalar_one_or_none()
            if chatbot:
                chatbot_name = chatbot.title
        
        result_list.append(ConversationOut(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            chatbot_id=conv.chatbot_id,
            chatbot_name=chatbot_name
        ))
    
    return result_list


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageOut])
async def get_conversation_messages(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    conversation_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db)
):
    """Obtener mensajes de una conversación"""
    
    result = await db.execute(select(ConversationModel).where(
        ConversationModel.id == conversation_id,
        ConversationModel.user_id == current_user.id
    ))
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    res_msgs = await db.execute(select(MessageModel).where(
        MessageModel.conversation_id == conversation_id
    ).order_by(MessageModel.created_at.asc()))
    messages = res_msgs.scalars().all()
    
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
@router.get("/available-chatbots")
async def get_available_chatbots(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Obtener lista de chatbots disponibles para el usuario"""
    
    # Chatbots creados por el usuario
    result_owned = await db.execute(select(CustomChatbot).where(
        CustomChatbot.created_by == current_user.id,
        CustomChatbot.is_active == True
    ))
    owned_chatbots = result_owned.scalars().all()
    
    # Chatbots con acceso otorgado
    result_access = await db.execute(select(ChatbotAccess).where(
        ChatbotAccess.user_id == current_user.id
    ))
    access_records = result_access.scalars().all()
    
    accessible_ids = [access.chatbot_id for access in access_records]
    accessible_chatbots = []
    
    if accessible_ids:
        result_accessible = await db.execute(select(CustomChatbot).where(
            CustomChatbot.id.in_(accessible_ids),
            CustomChatbot.is_active == True
        ))
        accessible_chatbots = result_accessible.scalars().all()
    
    # Combinar y eliminar duplicados
    all_chatbots = {cb.id: cb for cb in list(owned_chatbots) + list(accessible_chatbots)}.values()
    
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
@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    conversation_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db)
):
    """Eliminar una conversación y todos sus mensajes"""
    
    # Verificar que la conversación existe y el usuario tiene acceso
    result = await db.execute(select(ConversationModel).where(
        ConversationModel.id == conversation_id,
        ConversationModel.user_id == current_user.id
    ))
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    try:
        # Eliminar todos los mensajes de la conversación
        await db.execute(delete(MessageModel).where(
            MessageModel.conversation_id == conversation_id
        ))
        
        # Eliminar la conversación
        await db.delete(conversation)
        await db.commit()
        
        return {"message": "Conversación eliminada exitosamente"}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Error eliminando conversación: {str(e)}"
        )


@router.get("/conversations/{conversation_id}/exists")
@router.get("/conversations/{conversation_id}/exists")
async def check_conversation_exists(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    conversation_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db)
):
    """Verificar si una conversación existe y el usuario tiene acceso"""
    
    result = await db.execute(select(ConversationModel).where(
        ConversationModel.id == conversation_id,
        ConversationModel.user_id == current_user.id
    ))
    conversation = result.scalar_one_or_none()
    
    return {"exists": conversation is not None}


@router.patch("/conversations/{conversation_id}")
async def update_conversation(
    payload: dict,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    conversation_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db)
):
    """Actualizar título de una conversación"""
    
    # Verificar que la conversación existe y el usuario tiene acceso
    result = await db.execute(select(ConversationModel).where(
        ConversationModel.id == conversation_id,
        ConversationModel.user_id == current_user.id
    ))
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    # Actualizar título si se proporciona
    if "title" in payload:
        conversation.title = payload["title"]
        conversation.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(conversation)
    
    # Obtener nombre del chatbot si aplica
    chatbot_name = None
    if conversation.chatbot_id:
        result_cb = await db.execute(select(CustomChatbot).where(
            CustomChatbot.id == conversation.chatbot_id
        ))
        chatbot = result_cb.scalar_one_or_none()
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