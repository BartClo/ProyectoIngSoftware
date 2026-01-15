from fastapi import APIRouter, Depends, HTTPException, status, Path, Form, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, delete
from typing import Annotated, List, Optional
from datetime import datetime
from pydantic import BaseModel
import os
import shutil
import logging
from pathlib import Path as FilePath

from database import get_db
from models import User as UserModel, CustomChatbot, ChatbotAccess, AccessLevel, ChatbotDocument
from auth import get_current_user
from services.pinecone_service import pinecone_service

router = APIRouter(prefix="/api/chatbots", tags=["Chatbots"])
logger = logging.getLogger(__name__)

# Pydantic Models
class ChatbotCreate(BaseModel):
    title: str
    description: Optional[str] = None

class ChatbotUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class ChatbotOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    created_by: int
    pinecone_index_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    documents_count: int = 0
    users_count: int = 0

class UserAccessCreate(BaseModel):
    user_ids: List[int]
    access_level: AccessLevel = AccessLevel.READ

class UserAccessOut(BaseModel):
    id: int
    user_id: int
    user_email: str
    user_name: Optional[str]
    access_level: AccessLevel
    granted_at: datetime


@router.post("/", response_model=ChatbotOut, status_code=201)
async def create_chatbot(
    payload: ChatbotCreate,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Crear un nuevo chatbot personalizado"""
    chatbot = None
    try:
        # Generar nombre único para índice de Pinecone
        import uuid
        index_name = f"chatbot-{uuid.uuid4().hex[:12]}"
        
        # Primero intentar crear índice en Pinecone
        logger.info(f"Creando chatbot '{payload.title}' con índice {index_name}")
        success = await pinecone_service.create_index(index_name)
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Error creando índice en Pinecone. Verifique la configuración de Pinecone."
            )
        
        # Crear chatbot en base de datos solo después de que Pinecone esté OK
        chatbot = CustomChatbot(
            title=payload.title.strip(),
            description=payload.description,
            created_by=current_user.id,
            pinecone_index_name=index_name
        )
        
        db.add(chatbot)
        await db.commit()
        await db.refresh(chatbot)
        
        # Crear directorio de uploads para el chatbot
        upload_dir = FilePath("uploads") / f"chatbot_{chatbot.id}"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Chatbot {chatbot.id} creado exitosamente con índice {index_name}")
        
        return ChatbotOut(
            id=chatbot.id,
            title=chatbot.title,
            description=chatbot.description,
            created_by=chatbot.created_by,
            pinecone_index_name=chatbot.pinecone_index_name,
            is_active=chatbot.is_active,
            created_at=chatbot.created_at,
            updated_at=chatbot.updated_at,
            documents_count=0,
            users_count=0
        )
        
    except HTTPException:
        # Re-lanzar HTTPExceptions sin modificar
        if chatbot:
            await db.rollback()
        raise
    except Exception as e:
        logger.error(f"Error inesperado creando chatbot: {str(e)}")
        if chatbot:
            await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creando chatbot: {str(e)}"
        )


@router.get("/", response_model=List[ChatbotOut])
async def list_user_chatbots(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
):
    """Listar chatbots accesibles para el usuario actual"""
    
    # Chatbots creados por el usuario
    result_owned = await db.execute(select(CustomChatbot).where(
        CustomChatbot.created_by == current_user.id
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
        result_acc = await db.execute(select(CustomChatbot).where(
            CustomChatbot.id.in_(accessible_ids),
            CustomChatbot.is_active == True
        ))
        accessible_chatbots = result_acc.scalars().all()
    
    # Combinar y eliminar duplicados
    all_chatbots = {cb.id: cb for cb in list(owned_chatbots) + list(accessible_chatbots)}.values()
    
    # Agregar conteos
    result = []
    for chatbot in all_chatbots:
        # Contar documentos
        doc_count_res = await db.execute(select(func.count()).select_from(ChatbotDocument).where(
            ChatbotDocument.chatbot_id == chatbot.id
        ))
        docs_count = doc_count_res.scalar()
        
        # Contar usuarios con acceso
        user_count_res = await db.execute(select(func.count()).select_from(ChatbotAccess).where(
            ChatbotAccess.chatbot_id == chatbot.id
        ))
        users_count = user_count_res.scalar()
        
        result.append(ChatbotOut(
            id=chatbot.id,
            title=chatbot.title,
            description=chatbot.description,
            created_by=chatbot.created_by,
            pinecone_index_name=chatbot.pinecone_index_name,
            is_active=chatbot.is_active,
            created_at=chatbot.created_at,
            updated_at=chatbot.updated_at,
            documents_count=docs_count,
            users_count=users_count
        ))
    
    return sorted(result, key=lambda x: x.updated_at, reverse=True)


@router.get("/{chatbot_id}", response_model=ChatbotOut)
async def get_chatbot(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    chatbot_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db)
):
    """Obtener detalles de un chatbot específico"""
    
    result = await db.execute(select(CustomChatbot).where(
        CustomChatbot.id == chatbot_id
    ))
    chatbot = result.scalar_one_or_none()
    
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot no encontrado")
    
    # Verificar acceso
    has_access = False
    if chatbot.created_by == current_user.id:
        has_access = True
    else:
        res_access = await db.execute(select(ChatbotAccess).where(
            ChatbotAccess.chatbot_id == chatbot_id,
            ChatbotAccess.user_id == current_user.id
        ))
        if res_access.scalar_one_or_none():
            has_access = True
    
    if not has_access:
        raise HTTPException(status_code=403, detail="No tiene acceso a este chatbot")
    
    # Contar documentos y usuarios
    doc_count_res = await db.execute(select(func.count()).select_from(ChatbotDocument).where(
        ChatbotDocument.chatbot_id == chatbot_id
    ))
    docs_count = doc_count_res.scalar()
    
    users_count_res = await db.execute(select(func.count()).select_from(ChatbotAccess).where(
        ChatbotAccess.chatbot_id == chatbot_id
    ))
    users_count = users_count_res.scalar()
    
    return ChatbotOut(
        id=chatbot.id,
        title=chatbot.title,
        description=chatbot.description,
        created_by=chatbot.created_by,
        pinecone_index_name=chatbot.pinecone_index_name,
        is_active=chatbot.is_active,
        created_at=chatbot.created_at,
        updated_at=chatbot.updated_at,
        documents_count=docs_count,
        users_count=users_count
    )


@router.put("/{chatbot_id}", response_model=ChatbotOut)
async def update_chatbot(
    payload: ChatbotUpdate,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    chatbot_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db)
):
    """Actualizar un chatbot (solo propietario o admin)"""
    
    result = await db.execute(select(CustomChatbot).where(
        CustomChatbot.id == chatbot_id
    ))
    chatbot = result.scalar_one_or_none()
    
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot no encontrado")
    
    # Verificar permisos (propietario o admin)
    has_admin_access = False
    if chatbot.created_by == current_user.id:
        has_admin_access = True
    else:
        res_access = await db.execute(select(ChatbotAccess).where(
            ChatbotAccess.chatbot_id == chatbot_id,
            ChatbotAccess.user_id == current_user.id,
            ChatbotAccess.access_level == AccessLevel.ADMIN
        ))
        if res_access.scalar_one_or_none():
            has_admin_access = True
    
    if not has_admin_access:
        raise HTTPException(status_code=403, detail="Sin permisos para editar este chatbot")
    
    # Actualizar campos
    if payload.title is not None:
        chatbot.title = payload.title.strip()
    if payload.description is not None:
        chatbot.description = payload.description
    if payload.is_active is not None:
        chatbot.is_active = payload.is_active
    
    chatbot.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(chatbot)
    
    # Contar documentos y usuarios
    doc_count_res = await db.execute(select(func.count()).select_from(ChatbotDocument).where(
        ChatbotDocument.chatbot_id == chatbot_id
    ))
    docs_count = doc_count_res.scalar()
    
    users_count_res = await db.execute(select(func.count()).select_from(ChatbotAccess).where(
        ChatbotAccess.chatbot_id == chatbot_id
    ))
    users_count = users_count_res.scalar()
    
    return ChatbotOut(
        id=chatbot.id,
        title=chatbot.title,
        description=chatbot.description,
        created_by=chatbot.created_by,
        pinecone_index_name=chatbot.pinecone_index_name,
        is_active=chatbot.is_active,
        created_at=chatbot.created_at,
        updated_at=chatbot.updated_at,
        documents_count=docs_count,
        users_count=users_count
    )


@router.delete("/{chatbot_id}", status_code=204)
async def delete_chatbot(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    chatbot_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db)
):
    """Eliminar un chatbot (solo propietario)"""
    
    result = await db.execute(select(CustomChatbot).where(
        CustomChatbot.id == chatbot_id
    ))
    chatbot = result.scalar_one_or_none()
    
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot no encontrado")
    
    # Solo el propietario puede eliminar
    if chatbot.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Solo el propietario puede eliminar el chatbot")
    
    index_name = chatbot.pinecone_index_name
    
    try:
        logger.info(f"Eliminando chatbot {chatbot_id} con índice {index_name}")
        
        # Verificar si existen conversaciones relacionadas antes de eliminar
        from models import Conversation
        result_conv = await db.execute(select(Conversation).where(
            Conversation.chatbot_id == chatbot_id
        ))
        related_conversations = result_conv.scalars().all()
        
        if related_conversations:
            logger.info(f"Eliminando {len(related_conversations)} conversaciones relacionadas")
            for conv in related_conversations:
                conv.chatbot_id = None  # Desasociar en lugar de eliminar
        
        # Eliminar de base de datos (cascada eliminará documentos y accesos)
        await db.delete(chatbot)
        await db.commit()
        logger.info(f"Chatbot {chatbot_id} eliminado de la base de datos")
        
        # Intentar eliminar índice de Pinecone (no crítico si falla)
        pinecone_success = await pinecone_service.delete_index(index_name)
        if pinecone_success:
            logger.info(f"Índice {index_name} eliminado de Pinecone")
        else:
            logger.warning(f"No se pudo eliminar el índice {index_name} de Pinecone")
        
        # Eliminar archivos de uploads
        upload_dir = FilePath("uploads") / f"chatbot_{chatbot_id}"
        if upload_dir.exists():
            shutil.rmtree(upload_dir)
            logger.info(f"Directorio de archivos eliminado: {upload_dir}")
        
        logger.info(f"Chatbot {chatbot_id} eliminado completamente")
        
    except Exception as e:
        logger.error(f"Error eliminando chatbot {chatbot_id}: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error eliminando chatbot: {str(e)}"
        )


@router.post("/{chatbot_id}/users", status_code=201)
async def grant_user_access(
    payload: UserAccessCreate,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    chatbot_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db)
):
    """Otorgar acceso a usuarios (solo propietario o admin)"""
    
    result = await db.execute(select(CustomChatbot).where(
        CustomChatbot.id == chatbot_id
    ))
    chatbot = result.scalar_one_or_none()
    
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot no encontrado")
    
    # Verificar permisos
    has_admin_access = False
    if chatbot.created_by == current_user.id:
        has_admin_access = True
    else:
        res_access = await db.execute(select(ChatbotAccess).where(
            ChatbotAccess.chatbot_id == chatbot_id,
            ChatbotAccess.user_id == current_user.id,
            ChatbotAccess.access_level == AccessLevel.ADMIN
        ))
        if res_access.scalar_one_or_none():
            has_admin_access = True
    
    if not has_admin_access:
        raise HTTPException(status_code=403, detail="Sin permisos para gestionar accesos")
    
    granted_users = []
    errors = []
    
    for user_id in payload.user_ids:
        try:
            # Verificar que el usuario existe
            res_user = await db.execute(select(UserModel).where(UserModel.id == user_id))
            user = res_user.scalar_one_or_none()
            if not user:
                errors.append(f"Usuario {user_id} no encontrado")
                continue
            
            # Verificar si ya tiene acceso
            res_exist = await db.execute(select(ChatbotAccess).where(
                ChatbotAccess.chatbot_id == chatbot_id,
                ChatbotAccess.user_id == user_id
            ))
            existing_access = res_exist.scalar_one_or_none()
            
            if existing_access:
                # Actualizar nivel de acceso
                existing_access.access_level = payload.access_level
                existing_access.granted_by = current_user.id
                existing_access.granted_at = datetime.utcnow()
            else:
                # Crear nuevo acceso
                new_access = ChatbotAccess(
                    chatbot_id=chatbot_id,
                    user_id=user_id,
                    access_level=payload.access_level,
                    granted_by=current_user.id
                )
                db.add(new_access)
            
            granted_users.append({
                "user_id": user_id,
                "email": user.email,
                "access_level": payload.access_level.value
            })
            
        except Exception as e:
            errors.append(f"Error con usuario {user_id}: {str(e)}")
    
    await db.commit()
    
    return {
        "granted_users": granted_users,
        "errors": errors
    }


@router.get("/{chatbot_id}/users", response_model=List[UserAccessOut])
async def list_chatbot_users(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    chatbot_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db)
):
    """Listar usuarios con acceso al chatbot"""
    
    result = await db.execute(select(CustomChatbot).where(
        CustomChatbot.id == chatbot_id
    ))
    chatbot = result.scalar_one_or_none()
    
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot no encontrado")
    
    # Verificar acceso
    has_access = False
    if chatbot.created_by == current_user.id:
        has_access = True
    else:
        res_check = await db.execute(select(ChatbotAccess).where(
            ChatbotAccess.chatbot_id == chatbot_id,
            ChatbotAccess.user_id == current_user.id
        ))
        if res_check.scalar_one_or_none():
            has_access = True
            
    if not has_access:
        raise HTTPException(status_code=403, detail="No tiene acceso a este chatbot")
    
    # Obtener lista de usuarios
    res_recs = await db.execute(select(ChatbotAccess).where(
        ChatbotAccess.chatbot_id == chatbot_id
    ))
    access_records = res_recs.scalars().all()
    
    result = []
    for access in access_records:
        res_u = await db.execute(select(UserModel).where(UserModel.id == access.user_id))
        user = res_u.scalar_one_or_none()
        if user:
            result.append(UserAccessOut(
                id=access.id,
                user_id=user.id,
                user_email=user.email,
                user_name=user.nombre,
                access_level=access.access_level,
                granted_at=access.granted_at
            ))
    
    return result


@router.delete("/{chatbot_id}/users/{user_id}", status_code=204)
async def revoke_user_access(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    chatbot_id: int = Path(..., ge=1),
    user_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db)
):
    """Revocar acceso de un usuario (solo propietario o admin)"""
    
    result = await db.execute(select(CustomChatbot).where(
        CustomChatbot.id == chatbot_id
    ))
    chatbot = result.scalar_one_or_none()
    
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot no encontrado")
    
    # Verificar permisos
    has_admin_access = False
    if chatbot.created_by == current_user.id:
        has_admin_access = True
    else:
        res_chk = await db.execute(select(ChatbotAccess).where(
            ChatbotAccess.chatbot_id == chatbot_id,
            ChatbotAccess.user_id == current_user.id,
            ChatbotAccess.access_level == AccessLevel.ADMIN
        ))
        if res_chk.scalar_one_or_none():
            has_admin_access = True
            
    if not has_admin_access:
        raise HTTPException(status_code=403, detail="Sin permisos para gestionar accesos")
    
    # No permitir auto-revocación del propietario
    if user_id == chatbot.created_by:
        raise HTTPException(status_code=400, detail="No se puede revocar acceso al propietario")
    
    # Buscar y eliminar acceso
    res_acc = await db.execute(select(ChatbotAccess).where(
        ChatbotAccess.chatbot_id == chatbot_id,
        ChatbotAccess.user_id == user_id
    ))
    access_record = res_acc.scalar_one_or_none()
    
    if access_record:
        await db.delete(access_record)
        await db.commit()


@router.post("/{chatbot_id}/recreate-index", status_code=200)
async def recreate_pinecone_index(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    chatbot_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db)
):
    """Recrear el índice de Pinecone para un chatbot (solo propietario)"""
    
    result = await db.execute(select(CustomChatbot).where(
        CustomChatbot.id == chatbot_id
    ))
    chatbot = result.scalar_one_or_none()
    
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot no encontrado")
    
    # Solo el propietario puede recrear el índice
    if chatbot.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Solo el propietario puede recrear el índice")
    
    try:
        logger.info(f"Recreando índice Pinecone para chatbot {chatbot_id}")
        
        # Intentar eliminar índice existente (si existe)
        await pinecone_service.delete_index(chatbot.pinecone_index_name)
        
        # Crear nuevo índice
        success = await pinecone_service.create_index(chatbot.pinecone_index_name)
        
        if success:
            logger.info(f"Índice {chatbot.pinecone_index_name} recreado exitosamente")
            return {"message": "Índice recreado exitosamente", "index_name": chatbot.pinecone_index_name}
        else:
            raise HTTPException(
                status_code=500,
                detail="No se pudo recrear el índice de Pinecone"
            )
            
    except Exception as e:
        logger.error(f"Error recreando índice para chatbot {chatbot_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error recreando índice: {str(e)}"
        )

@router.get("/debug/pinecone-status")
async def get_pinecone_status(
    current_user: Annotated[UserModel, Depends(get_current_user)]
):
    """Obtener estado de la conexión con Pinecone (para debug)"""
    try:
        from services.pinecone_service import pinecone_service
        
        # TODO: Implementar un metodo get_all_indexes en el servicio para evitar acceso directo a pc
        # Por ahora, usamos un try-catch si el metodo no existe
        index_names = []
        try:
             # run_in_executor para no bloquear
             import asyncio
             loop = asyncio.get_running_loop()
             # Acceso directo al cliente (sync) envuelto
             indexes = await loop.run_in_executor(None, pinecone_service.pc.list_indexes)
             index_names = [index.name for index in indexes]
        except Exception:
             index_names = ["(Error listando indices)"]

        return {
            "status": "connected",
            "existing_indexes": index_names,
            "environment": pinecone_service.environment,
            "dimension": pinecone_service.dimension
        }
        
    except Exception as e:
        logger.error(f"Error verificando estado de Pinecone: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "existing_indexes": [],
            "environment": "unknown",
            "dimension": 0
        }

@router.get("/{chatbot_id}/stats")
async def get_chatbot_stats(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    chatbot_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db)
):
    """Obtener estadísticas del chatbot"""
    
    result = await db.execute(select(CustomChatbot).where(
        CustomChatbot.id == chatbot_id
    ))
    chatbot = result.scalar_one_or_none()
    
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot no encontrado")
    
    # Verificar acceso
    has_access = False
    if chatbot.created_by == current_user.id:
        has_access = True
    else:
        res_chk = await db.execute(select(ChatbotAccess).where(
            ChatbotAccess.chatbot_id == chatbot_id,
            ChatbotAccess.user_id == current_user.id
        ))
        if res_chk.scalar_one_or_none():
            has_access = True
            
    if not has_access:
        raise HTTPException(status_code=403, detail="No tiene acceso a este chatbot")
    
    # Obtener estadísticas
    doc_total_res = await db.execute(select(func.count()).select_from(ChatbotDocument).where(
        ChatbotDocument.chatbot_id == chatbot_id
    ))
    docs_count = doc_total_res.scalar()
    
    doc_proc_res = await db.execute(select(func.count()).select_from(ChatbotDocument).where(
        ChatbotDocument.chatbot_id == chatbot_id,
        ChatbotDocument.is_processed == True
    ))
    processed_docs = doc_proc_res.scalar()
    
    user_cnt_res = await db.execute(select(func.count()).select_from(ChatbotAccess).where(
        ChatbotAccess.chatbot_id == chatbot_id
    ))
    users_count = user_cnt_res.scalar()
    
    # Estadísticas de Pinecone
    pinecone_stats = await pinecone_service.get_index_stats(chatbot.pinecone_index_name)
    
    return {
        "chatbot_id": chatbot_id,
        "title": chatbot.title,
        "documents": {
            "total": docs_count,
            "processed": processed_docs,
            "pending": docs_count - processed_docs
        },
        "users": {
            "total": users_count
        },
        "vectors": {
            "total": pinecone_stats.get("total_vectors", 0),
            "dimension": pinecone_stats.get("dimension", 0)
        },
        "created_at": chatbot.created_at,
        "updated_at": chatbot.updated_at
    }