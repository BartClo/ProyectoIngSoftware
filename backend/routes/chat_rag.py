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
                
                # Filtrar resultados por score mínimo
                min_score = 0.45  # Ajustado para obtener más resultados relevantes
                context_chunks = [
                    result for result in search_results 
                    if result.get("score", 0) >= min_score
                ]
                
        except Exception as e:
            print(f"Error en búsqueda RAG: {str(e)}")
            # Continuar sin contexto en caso de error
    
    # Generar respuesta usando Groq (ultrarrápido y confiable)
    try:
        response_data = await groq_service.generate_response(
            user_question=user_text,
            context_chunks=context_chunks,
            chatbot_name=chatbot_name
        )
        
        # Códigos archivados:
        # response_data = await gemini_service.generate_response(...)  # Problemas API Key
        # response_data = await gpt4all_service.generate_response(...)  # Problemas memoria
        
        if response_data.get("success"):
            ai_response = response_data.get("response", "")
            sources = response_data.get("sources", [])
        else:
            ai_response = "Lo siento, hubo un error procesando tu consulta."
            sources = []
            
    except Exception as e:
        print(f"Error generando respuesta: {str(e)}")
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
            welcome_text = f"¡Hola! Soy tu asistente especializado en {chatbot.title}. ¿En qué puedo ayudarte?"
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