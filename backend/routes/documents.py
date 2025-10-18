from fastapi import APIRouter, Depends, HTTPException, status, Path, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Annotated, List, Optional
from datetime import datetime
from pydantic import BaseModel
import os
import aiofiles
from pathlib import Path as FilePath

from database import get_db
from models import User as UserModel, CustomChatbot, ChatbotDocument, ChatbotAccess, AccessLevel
from auth import get_current_user
from main import get_current_user
from services.pinecone_service import pinecone_service
from services.document_processor import document_processor
from services.embedding_service import embedding_service

router = APIRouter(prefix="/api/chatbots/{chatbot_id}/documents", tags=["Documents"])

# Pydantic Models
class DocumentOut(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    chunks_count: int
    is_processed: bool
    processed_at: Optional[datetime]
    uploaded_at: datetime
    uploader_email: Optional[str] = None

class ProcessingStatus(BaseModel):
    document_id: int
    filename: str
    status: str  # 'pending', 'processing', 'completed', 'failed'
    chunks_created: int = 0
    error_message: Optional[str] = None


async def verify_chatbot_access(
    chatbot_id: int,
    user: UserModel,
    db: Session,
    required_level: AccessLevel = AccessLevel.READ
) -> CustomChatbot:
    """Verifica acceso del usuario al chatbot"""
    
    chatbot = db.query(CustomChatbot).filter(
        CustomChatbot.id == chatbot_id
    ).first()
    
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot no encontrado")
    
    # Propietario siempre tiene acceso completo
    if chatbot.created_by == user.id:
        return chatbot
    
    # Verificar acceso otorgado
    access_record = db.query(ChatbotAccess).filter(
        ChatbotAccess.chatbot_id == chatbot_id,
        ChatbotAccess.user_id == user.id
    ).first()
    
    if not access_record:
        raise HTTPException(status_code=403, detail="No tiene acceso a este chatbot")
    
    # Verificar nivel de acceso
    if required_level == AccessLevel.WRITE and access_record.access_level == AccessLevel.READ:
        raise HTTPException(status_code=403, detail="Necesita permisos de escritura")
    
    if required_level == AccessLevel.ADMIN and access_record.access_level in [AccessLevel.READ, AccessLevel.WRITE]:
        raise HTTPException(status_code=403, detail="Necesita permisos de administrador")
    
    return chatbot


@router.post("/upload", response_model=List[DocumentOut], status_code=201)
async def upload_documents(
    background_tasks: BackgroundTasks,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    chatbot_id: int = Path(..., ge=1),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Subir documentos al chatbot"""
    
    # Verificar acceso de escritura
    chatbot = await verify_chatbot_access(chatbot_id, current_user, db, AccessLevel.WRITE)
    
    if not files:
        raise HTTPException(status_code=400, detail="No se proporcionaron archivos")
    
    # Verificar tipos de archivo
    max_file_size = int(os.getenv("MAX_FILE_SIZE_MB", "50")) * 1024 * 1024  # MB a bytes
    uploaded_docs = []
    errors = []
    
    # Crear directorio de uploads
    upload_dir = FilePath("uploads") / f"chatbot_{chatbot_id}"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    for file in files:
        try:
            # Validaciones
            if not document_processor.is_valid_file_type(file.filename):
                errors.append(f"{file.filename}: Tipo de archivo no soportado")
                continue
            
            # Leer contenido para verificar tamaño
            content = await file.read()
            if len(content) > max_file_size:
                errors.append(f"{file.filename}: Archivo demasiado grande (máximo {max_file_size // (1024*1024)}MB)")
                continue
            
            # Generar nombre único para evitar colisiones
            file_extension = FilePath(file.filename).suffix
            unique_filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
            file_path = upload_dir / unique_filename
            
            # Guardar archivo
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            # Crear registro en base de datos
            doc_record = ChatbotDocument(
                chatbot_id=chatbot_id,
                filename=unique_filename,
                original_filename=file.filename,
                file_path=str(file_path),
                file_size=len(content),
                file_type=file_extension.lower(),
                uploaded_by=current_user.id
            )
            
            db.add(doc_record)
            db.flush()  # Para obtener el ID
            
            # Programar procesamiento en background
            background_tasks.add_task(
                process_document_background,
                doc_record.id,
                chatbot_id
            )
            
            uploaded_docs.append(DocumentOut(
                id=doc_record.id,
                filename=doc_record.filename,
                original_filename=doc_record.original_filename,
                file_size=doc_record.file_size,
                file_type=doc_record.file_type,
                chunks_count=0,
                is_processed=False,
                processed_at=None,
                uploaded_at=doc_record.uploaded_at,
                uploader_email=current_user.email
            ))
            
        except Exception as e:
            errors.append(f"{file.filename}: Error subiendo archivo - {str(e)}")
    
    db.commit()
    
    if errors:
        # Si hay errores pero también archivos exitosos, devolver ambos
        response = {
            "uploaded": uploaded_docs,
            "errors": errors
        }
        if not uploaded_docs:  # Solo errores
            raise HTTPException(status_code=400, detail=response)
        return uploaded_docs  # Por ahora solo devolver exitosos
    
    return uploaded_docs


@router.get("/", response_model=List[DocumentOut])
async def list_documents(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    chatbot_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """Listar documentos del chatbot"""
    
    # Verificar acceso de lectura
    chatbot = await verify_chatbot_access(chatbot_id, current_user, db, AccessLevel.READ)
    
    documents = db.query(ChatbotDocument).filter(
        ChatbotDocument.chatbot_id == chatbot_id
    ).order_by(ChatbotDocument.uploaded_at.desc()).all()
    
    result = []
    for doc in documents:
        uploader = None
        if doc.uploaded_by:
            uploader = db.query(UserModel).filter(UserModel.id == doc.uploaded_by).first()
        
        result.append(DocumentOut(
            id=doc.id,
            filename=doc.filename,
            original_filename=doc.original_filename,
            file_size=doc.file_size,
            file_type=doc.file_type,
            chunks_count=doc.chunks_count,
            is_processed=doc.is_processed,
            processed_at=doc.processed_at,
            uploaded_at=doc.uploaded_at,
            uploader_email=uploader.email if uploader else None
        ))
    
    return result


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    chatbot_id: int = Path(..., ge=1),
    document_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """Eliminar documento del chatbot"""
    
    # Verificar acceso de escritura
    chatbot = await verify_chatbot_access(chatbot_id, current_user, db, AccessLevel.WRITE)
    
    document = db.query(ChatbotDocument).filter(
        ChatbotDocument.id == document_id,
        ChatbotDocument.chatbot_id == chatbot_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    try:
        # Eliminar vectores de Pinecone si el documento fue procesado
        if document.is_processed and document.chunks_count > 0:
            # Generar IDs de vectores basados en el documento
            vector_ids = [f"doc_{document.id}_chunk_{i}" for i in range(document.chunks_count)]
            await pinecone_service.delete_vectors(
                chatbot.pinecone_index_name,
                vector_ids,
                namespace=f"chatbot_{chatbot_id}"
            )
        
        # Eliminar archivo físico
        file_path = FilePath(document.file_path)
        if file_path.exists():
            file_path.unlink()
        
        # Eliminar de base de datos
        db.delete(document)
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error eliminando documento: {str(e)}"
        )


@router.post("/process", status_code=202)
async def process_all_documents(
    background_tasks: BackgroundTasks,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    chatbot_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """Procesar todos los documentos pendientes del chatbot"""
    
    # Verificar acceso de escritura
    chatbot = await verify_chatbot_access(chatbot_id, current_user, db, AccessLevel.WRITE)
    
    # Obtener documentos no procesados
    pending_docs = db.query(ChatbotDocument).filter(
        ChatbotDocument.chatbot_id == chatbot_id,
        ChatbotDocument.is_processed == False
    ).all()
    
    if not pending_docs:
        return {"message": "No hay documentos pendientes de procesar"}
    
    # Programar procesamiento en background
    for doc in pending_docs:
        background_tasks.add_task(
            process_document_background,
            doc.id,
            chatbot_id
        )
    
    return {
        "message": f"Procesamiento iniciado para {len(pending_docs)} documentos",
        "document_ids": [doc.id for doc in pending_docs]
    }


@router.get("/{document_id}/status", response_model=ProcessingStatus)
async def get_document_status(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    chatbot_id: int = Path(..., ge=1),
    document_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    """Obtener estado de procesamiento de un documento"""
    
    # Verificar acceso
    chatbot = await verify_chatbot_access(chatbot_id, current_user, db, AccessLevel.READ)
    
    document = db.query(ChatbotDocument).filter(
        ChatbotDocument.id == document_id,
        ChatbotDocument.chatbot_id == chatbot_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    # Determinar estado
    if document.is_processed:
        status = "completed"
    elif document.processed_at is not None:
        status = "failed"  # Procesado pero sin éxito
    else:
        status = "pending"
    
    return ProcessingStatus(
        document_id=document.id,
        filename=document.original_filename,
        status=status,
        chunks_created=document.chunks_count,
        error_message=None  # TODO: agregar campo de error en el modelo
    )


async def process_document_background(document_id: int, chatbot_id: int):
    """Procesar documento en background"""
    from database import SessionLocal
    
    db = SessionLocal()
    try:
        # Obtener documento y chatbot
        document = db.query(ChatbotDocument).filter(
            ChatbotDocument.id == document_id
        ).first()
        
        if not document:
            return
        
        chatbot = db.query(CustomChatbot).filter(
            CustomChatbot.id == chatbot_id
        ).first()
        
        if not chatbot:
            return
        
        print(f"Procesando documento: {document.original_filename}")
        
        # Extraer texto del documento
        extraction_result = await document_processor.extract_text_from_file(
            document.file_path
        )
        
        if not extraction_result.get("success"):
            print(f"Error extrayendo texto: {extraction_result.get('error')}")
            document.processed_at = datetime.utcnow()
            db.commit()
            return
        
        text_content = extraction_result.get("text", "")
        if not text_content.strip():
            print("Documento sin contenido de texto")
            document.processed_at = datetime.utcnow()
            db.commit()
            return
        
        # Crear chunks del texto
        metadata = {
            "source": document.original_filename,
            "chatbot_id": chatbot_id,
            "document_id": document_id,
            "file_type": document.file_type
        }
        
        chunks = document_processor.create_text_chunks(text_content, metadata)
        
        if not chunks:
            print("No se pudieron crear chunks del documento")
            document.processed_at = datetime.utcnow()
            db.commit()
            return
        
        # Generar embeddings para cada chunk
        chunk_texts = [chunk["text"] for chunk in chunks]
        embeddings = await embedding_service.generate_embeddings(chunk_texts)
        
        if not embeddings or len(embeddings) != len(chunks):
            print("Error generando embeddings")
            document.processed_at = datetime.utcnow()
            db.commit()
            return
        
        # Preparar vectores para Pinecone
        vectors = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vector_id = f"doc_{document_id}_chunk_{i}"
            
            vector_metadata = {
                **chunk["metadata"],
                "text": chunk["text"],
                "chunk_number": chunk["chunk_number"],
                "char_count": chunk["char_count"],
                "word_count": chunk["word_count"]
            }
            
            vectors.append({
                "id": vector_id,
                "values": embedding,
                "metadata": vector_metadata
            })
        
        # Subir a Pinecone
        success = await pinecone_service.upsert_vectors(
            chatbot.pinecone_index_name,
            vectors,
            namespace=f"chatbot_{chatbot_id}"
        )
        
        if success:
            # Marcar como procesado
            document.is_processed = True
            document.chunks_count = len(chunks)
            document.processed_at = datetime.utcnow()
            
            print(f"Documento procesado exitosamente: {len(chunks)} chunks creados")
        else:
            print("Error subiendo vectores a Pinecone")
            document.processed_at = datetime.utcnow()
        
        db.commit()
        
    except Exception as e:
        print(f"Error procesando documento {document_id}: {str(e)}")
        # Marcar como intentado (para evitar reprocesamiento infinito)
        if document:
            document.processed_at = datetime.utcnow()
            db.commit()
        
    finally:
        db.close()