"""
FastAPI Backend para Chatbot USS con RAG
Sistema de chatbots personalizados con procesamiento de documentos
"""

from fastapi import FastAPI, Depends, HTTPException, status, Path, Form
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Annotated, List, Optional
import hashlib
from fastapi import UploadFile, File
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Importaciones de base de datos y modelos
from database import Base, engine, get_db
from models import (
    User as UserModel, 
    Conversation as ConversationModel,
    Message as MessageModel,
    ConversationParticipant as ConversationParticipantModel,
    Attachment as AttachmentModel,
    Report as ReportModel
)

# Importar funciones de autenticación
from auth import (
    authenticate_user, 
    create_access_token, 
    get_password_hash, 
    get_current_user,
    get_user_by_email
)

# Crear aplicación FastAPI
app = FastAPI(
    title="Chatbot USS API",
    description="API para el Chatbot de la Universidad San Sebastián con RAG",
    version="2.0.0"
)

# Configuración CORS
origins = [
    "http://localhost:5173",  # frontend local (Vite/React)
    "http://localhost:3000",  # frontend local alternativo
    "https://*.vercel.app",   # Vercel deployments
    "https://chatbot-uss-frontend.vercel.app",  # Dominio específico de Vercel
]

# Para producción, permitir dominios de Vercel
if os.getenv("ENVIRONMENT") == "production":
    origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Incluir rutas del sistema RAG
from routes.chatbots import router as chatbots_router
from routes.documents import router as documents_router  
from routes.chat_rag import router as chat_rag_router

app.include_router(chatbots_router)
app.include_router(documents_router)
app.include_router(chat_rag_router)

# --------------- Schemas Pydantic ------------------

class UserCreate(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class AdminCreateUser(BaseModel):
    email: str
    password: str
    nombre: Optional[str] = None
    activo: Optional[bool] = True

class ReportCreate(BaseModel):
    report_type: str
    comment: Optional[str] = None

# --------------- Endpoints Health Check ------------------

@app.get("/")
async def root():
    """Endpoint raíz para verificar que la API está funcionando"""
    return {
        "message": "Chatbot USS API con RAG está funcionando",
        "status": "ok",
        "version": "2.0.0",
        "rag_enabled": True,
        "features": ["custom_chatbots", "document_upload", "pinecone_search", "gemini_2_flash"]
    }

@app.get("/health")
async def health_check():
    """Health check para servicios de monitoreo"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/ai_health/")
async def ai_health():
    """Health check del sistema de IA (Groq)"""
    try:
        from services.groq_service import groq_service
        
        # Obtener información del modelo
        model_info = groq_service.get_model_info()
        
        return {
            "status": "healthy",
            "ai_provider": "Groq",
            "model": model_info["model_name"],
            "provider_info": model_info["provider"],
            "temperature": model_info["temperature"],
            "max_tokens": model_info["max_tokens"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "ai_provider": "Groq",
            "model": "unknown",
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/chatbot_info/")
async def chatbot_info():
    """Información sobre el estado del chatbot"""
    return {
        "mode": "rag_enabled",
        "rag_enabled": True,
        "description": "Chatbot con RAG usando Pinecone, Groq/Llama3 y Sentence Transformers",
        "model": "llama-3.1-8b-instant",
        "ai_provider": "Groq",
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "vector_store": "pinecone",
        "features": {
            "custom_chatbots": True,
            "document_processing": True,
            "semantic_search": True,
            "multi_user": True,
            "ultra_fast_inference": True
        }
    }

# --------------- Endpoints Autenticación ------------------

@app.post("/register/", status_code=201)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Registrar nuevo usuario"""
    try:
        db_user = get_user_by_email(db, user.email)
        if db_user:
            raise HTTPException(status_code=400, detail="Email ya registrado")
        
        hashed_password = get_password_hash(user.password)
        new_user = UserModel(email=user.email, password_hash=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"message": "Usuario registrado exitosamente"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email ya registrado")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al registrar usuario: {str(e)}")

@app.post("/login/", response_model=Token)
def login_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    """Iniciar sesión de usuario"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )
    access_token = create_access_token({"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# --------------- Endpoints Administración de Usuarios ------------------

@app.get("/admin/users/")
def admin_list_users(
    current_user: Annotated[UserModel, Depends(get_current_user)], 
    db: Session = Depends(get_db)
):
    """Listar usuarios (endpoint administrativo)"""
    users = db.query(UserModel).order_by(UserModel.email.asc()).all()
    return [
        {
            "id": u.id, 
            "email": u.email, 
            "nombre": u.nombre, 
            "activo": bool(u.activo)
        } 
        for u in users
    ]

@app.post("/admin/users/", status_code=201)
def admin_create_user(
    payload: AdminCreateUser, 
    current_user: Annotated[UserModel, Depends(get_current_user)], 
    db: Session = Depends(get_db)
):
    """Crear usuario desde panel administrativo"""
    hashed = get_password_hash(payload.password)
    user = UserModel(
        email=payload.email, 
        password_hash=hashed, 
        nombre=payload.nombre, 
        activo=1 if payload.activo else 0
    )
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email ya registrado")
    return {"id": user.id, "email": user.email, "nombre": user.nombre}

@app.delete('/admin/users/{user_id}/', status_code=204)
def admin_delete_user(
    user_id: int, 
    current_user: Annotated[UserModel, Depends(get_current_user)], 
    db: Session = Depends(get_db)
):
    """Eliminar usuario por id (endpoint administrativo)"""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='Usuario no encontrado')
    db.delete(user)
    db.commit()

@app.patch('/admin/users/{user_id}/password', status_code=200)
def admin_update_user_password(
    user_id: int,
    payload: dict,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """Actualizar contraseña de un usuario (endpoint administrativo)"""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='Usuario no encontrado')
    
    new_password = payload.get('password')
    if not new_password:
        raise HTTPException(status_code=400, detail='Contraseña requerida')
    
    # Validación básica de longitud
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail='La contraseña debe tener al menos 6 caracteres')
    
    user.password_hash = get_password_hash(new_password)
    db.commit()
    
    return {"message": "Contraseña actualizada exitosamente"}

# --------------- Endpoints Administración de Conversaciones ------------------

@app.post("/admin/conversations/", status_code=201)
async def admin_create_conversation(
    title: str = Form(""),
    users: str = Form(""),
    files: List[UploadFile] = File(default=[]),
    current_user: Annotated[UserModel, Depends(get_current_user)] = None,
    db: Session = Depends(get_db),
):
    """Crear conversación desde panel administrativo"""
    conv = ConversationModel(
        user_id=current_user.id if current_user else None, 
        title=title.strip() or "Nueva conversación"
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)

    # Agregar participantes (emails separados por comas)
    emails = [e.strip() for e in users.split(",") if e.strip()]
    inserted_emails = []
    inserted_ids = []
    for email in emails:
        u = db.query(UserModel).filter(func.lower(UserModel.email) == email.lower()).first()
        if u:
            cp = ConversationParticipantModel(conversation_id=conv.id, user_id=u.id)
            db.add(cp)
            inserted_emails.append(u.email)
            inserted_ids.append(u.id)
    db.commit()

    # Guardar archivos adjuntos
    upload_dir = os.path.join(os.path.dirname(__file__), "uploads", str(conv.id))
    os.makedirs(upload_dir, exist_ok=True)
    files_info = []
    
    for f in files:
        dest = os.path.join(upload_dir, f.filename)
        with open(dest, "wb") as out:
            content = await f.read()
            out.write(content)
        att = AttachmentModel(conversation_id=conv.id, filename=f.filename, path=dest)
        db.add(att)
        db.commit()
        db.refresh(att)
        files_info.append({"filename": f.filename, "path": dest, "id": att.id})

    # Insertar mensaje de bienvenida
    try:
        welcome_text = "¡Hola! Soy tu asistente de IA USS. ¿Cómo puedo ayudarte hoy?"
        welcome_msg = MessageModel(conversation_id=conv.id, sender="ai", text=welcome_text)
        db.add(welcome_msg)
        conv.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(conv)
    except Exception:
        db.rollback()

    return {
        "id": conv.id, 
        "title": conv.title, 
        "created_at": conv.created_at, 
        "users": inserted_emails, 
        "participant_ids": inserted_ids, 
        "files": files_info
    }

@app.get("/admin/conversations/")
def admin_list_conversations(
    current_user: Annotated[UserModel, Depends(get_current_user)], 
    db: Session = Depends(get_db)
):
    """Listar conversaciones con participantes y archivos"""
    convs = db.query(ConversationModel).order_by(ConversationModel.updated_at.desc()).all()
    out = []
    for c in convs:
        # Obtener participantes
        parts = db.query(ConversationParticipantModel).filter(
            ConversationParticipantModel.conversation_id == c.id
        ).all()
        emails = []
        for p in parts:
            u = db.query(UserModel).filter(UserModel.id == p.user_id).first()
            if u:
                emails.append(u.email)
        
        # Obtener archivos adjuntos
        atts = db.query(AttachmentModel).filter(AttachmentModel.conversation_id == c.id).all()
        files = [{"filename": a.filename, "path": a.path} for a in atts]
        
        out.append({
            "id": c.id, 
            "title": c.title, 
            "created_at": c.created_at, 
            "users": emails, 
            "files": files
        })
    return out

@app.delete('/admin/conversations/{conversation_id}/', status_code=204)
def admin_delete_conversation(
    conversation_id: int = Path(..., ge=1), 
    current_user: Annotated[UserModel, Depends(get_current_user)] = None, 
    db: Session = Depends(get_db)
):
    """Eliminar conversación desde panel administrativo"""
    conv = db.query(ConversationModel).filter(ConversationModel.id == conversation_id).first()
    if not conv:
        return  # Idempotente: ya eliminada
    try:
        db.delete(conv)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail='Error eliminando conversación')

# --------------- Endpoints Archivos Adjuntos ------------------

@app.post('/conversations/{conversation_id}/attachments/', status_code=201)
async def add_conversation_attachments(
    conversation_id: int = Path(..., ge=1), 
    files: List[UploadFile] = File(default=[]), 
    current_user: Annotated[UserModel, Depends(get_current_user)] = None, 
    db: Session = Depends(get_db)
):
    """Agregar archivos adjuntos a conversación"""
    conv = db.query(ConversationModel).filter(ConversationModel.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail='Conversación no encontrada')

    upload_dir = os.path.join(os.path.dirname(__file__), 'uploads', str(conv.id))
    os.makedirs(upload_dir, exist_ok=True)
    files_info = []
    
    for f in files:
        dest = os.path.join(upload_dir, f.filename)
        with open(dest, 'wb') as out:
            content = await f.read()
            out.write(content)
        att = AttachmentModel(conversation_id=conv.id, filename=f.filename, path=dest)
        db.add(att)
        db.commit()
        db.refresh(att)
        files_info.append({'filename': f.filename, 'path': dest, 'id': att.id})
    
    try:
        db.commit()
    except Exception:
        db.rollback()
    return {'files': files_info}

# --------------- Endpoints Conversaciones (Compatibilidad) ------------------
# Estos endpoints mantienen compatibilidad con el frontend existente
# y redirigen a los nuevos endpoints RAG

from models import Conversation as ConversationModel, Message as MessageModel

class ConversationOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

class ConversationCreate(BaseModel):
    title: Optional[str] = None
    with_welcome: bool = True

class MessageOut(BaseModel):
    id: int
    sender: str
    text: str
    created_at: datetime

@app.get("/conversations/", response_model=List[ConversationOut])
async def get_conversations(
    current_user: Annotated[UserModel, Depends(get_current_user)], 
    db: Session = Depends(get_db)
):
    """Compatibilidad: listar conversaciones del usuario"""
    # Solo conversaciones creadas por el usuario (sin participantes por ahora)
    items = (
        db.query(ConversationModel)
        .filter(ConversationModel.user_id == current_user.id)
        .order_by(ConversationModel.updated_at.desc())
        .all()
    )
    return [
        ConversationOut(
            id=i.id, title=i.title, created_at=i.created_at, updated_at=i.updated_at
        )
        for i in items
    ]

@app.post("/conversations/", response_model=ConversationOut, status_code=201)
async def create_conversation(
    payload: ConversationCreate, 
    current_user: Annotated[UserModel, Depends(get_current_user)], 
    db: Session = Depends(get_db)
):
    """Compatibilidad: crear nueva conversación"""
    conv = ConversationModel(
        user_id=current_user.id, 
        title=payload.title or "Nueva conversación"
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)

    # Mensaje de bienvenida opcional
    if payload.with_welcome:
        welcome_text = "¡Hola! Soy tu asistente de IA USS. ¿Cómo puedo ayudarte hoy?"
        msg = MessageModel(conversation_id=conv.id, sender="ai", text=welcome_text)
        db.add(msg)
        conv.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(conv)

    return ConversationOut(
        id=conv.id, title=conv.title, created_at=conv.created_at, updated_at=conv.updated_at
    )

@app.get("/conversations/{conversation_id}/messages/", response_model=List[MessageOut])
async def get_conversation_messages(
    conversation_id: int = Path(..., ge=1), 
    current_user: Annotated[UserModel, Depends(get_current_user)] = None, 
    db: Session = Depends(get_db)
):
    """Compatibilidad: obtener mensajes de conversación"""
    conv = db.query(ConversationModel).filter(
        ConversationModel.id == conversation_id,
        ConversationModel.user_id == current_user.id
    ).first()
    
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    msgs = (
        db.query(MessageModel)
        .filter(MessageModel.conversation_id == conversation_id)
        .order_by(MessageModel.created_at.asc())
        .all()
    )
    return [
        MessageOut(id=m.id, sender=m.sender, text=m.text, created_at=m.created_at) 
        for m in msgs
    ]

@app.delete("/conversations/{conversation_id}/", status_code=204)
async def delete_conversation(
    conversation_id: int = Path(..., ge=1),
    current_user: Annotated[UserModel, Depends(get_current_user)] = None,
    db: Session = Depends(get_db),
):
    """Compatibilidad: eliminar conversación"""
    conv = db.query(ConversationModel).filter(
        ConversationModel.id == conversation_id, 
        ConversationModel.user_id == current_user.id
    ).first()
    
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    
    db.delete(conv)
    db.commit()

class MessageCreate(BaseModel):
    text: str

class ChatResponse(BaseModel):
    response: str
    sources: List[str] = []

@app.post("/conversations/{conversation_id}/messages/", response_model=ChatResponse)
async def send_message_to_conversation(
    payload: MessageCreate,
    conversation_id: int = Path(..., ge=1),
    current_user: Annotated[UserModel, Depends(get_current_user)] = None,
    db: Session = Depends(get_db),
):
    """Compatibilidad: enviar mensaje a conversación (modo simple sin RAG)"""
    conv = db.query(ConversationModel).filter(
        ConversationModel.id == conversation_id,
        ConversationModel.user_id == current_user.id
    ).first()
    
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    user_text = (payload.text or "").strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Texto vacío")

    # Guardar mensaje del usuario
    user_msg = MessageModel(conversation_id=conv.id, sender="user", text=user_text)
    db.add(user_msg)
    db.commit()

    # Generar respuesta simple (sin RAG)
    # TODO: En el futuro, integrar con el sistema RAG completo
    simple_responses = [
        f"Gracias por tu mensaje: '{user_text}'. ¿En qué más puedo ayudarte?",
        "Entiendo tu consulta. ¿Podrías proporcionar más detalles?",
        "Esa es una buena pregunta. ¿Te gustaría que profundicemos en el tema?",
        "He recibido tu mensaje. ¿Hay algo específico en lo que puedas ayudarte?",
    ]
    
    import hashlib
    # Usar hash del texto para una respuesta "consistente" pero variada
    hash_obj = hashlib.md5(user_text.encode())
    response_index = int(hash_obj.hexdigest(), 16) % len(simple_responses)
    ai_text = simple_responses[response_index]

    # Guardar mensaje de la IA
    ai_msg = MessageModel(conversation_id=conv.id, sender="ai", text=ai_text)
    db.add(ai_msg)
    conv.updated_at = datetime.utcnow()
    db.commit()

    return ChatResponse(response=ai_text, sources=[])

# --------------- Endpoints Reportes ------------------

@app.post('/reports/', status_code=201)
def create_report(
    payload: ReportCreate, 
    conversation_id: Optional[int] = None, 
    current_user: Annotated[UserModel, Depends(get_current_user)] = None, 
    db: Session = Depends(get_db)
):
    """Crear reporte"""
    r = ReportModel(
        conversation_id=conversation_id, 
        user_id=current_user.id if current_user else None, 
        report_type=payload.report_type, 
        comment=payload.comment
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return {
        'id': r.id, 
        'conversation_id': r.conversation_id, 
        'user_id': r.user_id, 
        'report_type': r.report_type, 
        'comment': r.comment, 
        'created_at': r.created_at, 
        'status': r.status
    }

@app.get('/admin/reports/')
def admin_list_reports(
    current_user: Annotated[UserModel, Depends(get_current_user)] = None, 
    db: Session = Depends(get_db)
):
    """Listar reportes (panel administrativo)"""
    rows = db.query(ReportModel).order_by(ReportModel.created_at.desc()).all()
    out = []
    for row in rows:
        u = None
        if row.user_id:
            u = db.query(UserModel).filter(UserModel.id == row.user_id).first()
        out.append({
            'id': row.id, 
            'docente': u.nombre if u else None, 
            'email': u.email if u else None, 
            'conversation_id': row.conversation_id, 
            'tipo': row.report_type, 
            'comentario': row.comment, 
            'fechaEnvio': row.created_at, 
            'estado': row.status
        })
    return out

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)