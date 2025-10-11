from fastapi import FastAPI, Depends, HTTPException, status, Path, Form
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from passlib.context import CryptContext
from typing import Annotated, List, Tuple, Dict, Optional
from fastapi import UploadFile, File
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
import os
# import glob  # RAG DESHABILITADO
# import pickle  # RAG DESHABILITADO
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# import numpy as np  # RAG DESHABILITADO

from database import Base, engine, get_db
from models import User as UserModel
from models import Conversation as ConversationModel
from models import Message as MessageModel
from models import ConversationParticipant as ConversationParticipantModel
from models import Attachment as AttachmentModel
from models import Report as ReportModel

# JWT
from jose import JWTError, jwt

# Gemini
import google.generativeai as genai

# FAISS - RAG DESHABILITADO
# import faiss

app = FastAPI(
    title="Chatbot USS API",
    description="API para el Chatbot de la Universidad San Sebastián",
    version="1.0.0"
)

origins = [
    "http://localhost:5173",  # frontend local (Vite/React)
    "http://localhost:3000",  # frontend local alternativo
    "https://*.vercel.app",   # Vercel deployments
    "https://chatbot-uss-frontend.vercel.app",  # Tu dominio específico de Vercel
]

# Para producción, también permitir todos los dominios de Vercel
import os
if os.getenv("ENVIRONMENT") == "production":
    origins.append("*")  # Solo en producción para simplificar CORS

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Seguridad / JWT
SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_ME_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/")

Base.metadata.create_all(bind=engine)

# --------------- Pydantic Schemas ------------------
class UserCreate(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None

class ConversationOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

class ConversationCreate(BaseModel):
    title: Optional[str] = None
    with_welcome: bool = True

class ConversationRename(BaseModel):
    title: str

class MessageOut(BaseModel):
    id: int
    sender: str
    text: str
    created_at: datetime

class MessageCreate(BaseModel):
    text: str

class ChatResponse(BaseModel):
    response: str
    sources: List[str] = []  # Siempre vacío cuando RAG está deshabilitado

# --------------- Helpers de Seguridad ------------------

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user_by_email(db: Session, email: str) -> Optional[UserModel]:
    return db.query(UserModel).filter(UserModel.email == email).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[UserModel]:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user

# --------------- IA CONFIG ------------------
# Configuración de Gemini con API key desde variables de entorno (RAG deshabilitado)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY no está configurada en las variables de entorno")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# RAG DESHABILITADO - Comentado para uso futuro
# CONTEXT_DIR = os.path.join(os.path.dirname(__file__), "context_docs")
# INDEX_PATH = os.path.join(os.path.dirname(__file__), "vector_store.index")
# DOCSTORE_PATH = os.path.join(os.path.dirname(__file__), "docstore.pkl")


# RAG DESHABILITADO - Función de chunking comentada
# def _chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
#     chunks: List[str] = []
#     start = 0
#     text_length = len(text)
#     while start < text_length:
#         end = min(start + chunk_size, text_length)
#         chunks.append(text[start:end])
#         if end == text_length:
#             break
#         start = end - overlap
#         if start < 0:
#             start = 0
#     return chunks


# RAG DESHABILITADO - Función de carga de documentos comentada
# def _load_context_texts() -> List[str]:
#     from pypdf import PdfReader
# 
#     texts: List[str] = []
#     if not os.path.isdir(CONTEXT_DIR):
#         return texts
# 
#     pdf_paths = sorted(glob.glob(os.path.join(CONTEXT_DIR, "*.pdf")))
#     for pdf_path in pdf_paths:
#         try:
#             reader = PdfReader(pdf_path)
#             pages_text: List[str] = [page.extract_text() or "" for page in reader.pages]
#             full_text = "\n".join(pages_text)
# 
#             if not full_text.strip():
#                 try:
#                     import pypdfium2 as pdfium
#                     from PIL import Image  # noqa: F401  # Pillow usado indirectamente
#                     import pytesseract
# 
#                     pdf = pdfium.PdfDocument(pdf_path)
#                     ocr_text_parts: List[str] = []
#                     render_scale = 2.0
#                     for i in range(len(pdf)):
#                         page = pdf[i]
#                         bitmap = page.render(scale=render_scale).to_pil()
#                         if bitmap.mode != "L":
#                             bitmap = bitmap.convert("L")
#                         page_text = pytesseract.image_to_string(bitmap, lang="spa+eng")
#                         if page_text:
#                             ocr_text_parts.append(page_text)
#                     full_text = "\n".join(ocr_text_parts)
#                 except Exception:
#                     full_text = ""
# 
#             if full_text.strip():
#                 for chunk in _chunk_text(full_text):
#                     texts.append(chunk)
#         except Exception:
#             continue
#     return texts


# RAG DESHABILITADO - Función de construcción de índice FAISS comentada
# def build_faiss_from_context() -> Tuple[Optional[faiss.IndexFlatIP], Dict[int, str]]:
#     documents = _load_context_texts()
#     if not documents:
#         return None, {}
# 
#     embeddings: List[List[float]] = []
#     docstore: Dict[int, str] = {}
# 
#     for idx, doc_text in enumerate(documents):
#         try:
#             emb = genai.embed_content(
#                 model="models/embedding-001",
#                 content=doc_text,
#                 task_type="retrieval_document",
#             )["embedding"]
#         except Exception:
#             continue
#         embeddings.append(emb)
#         docstore[idx] = doc_text
# 
#     if not embeddings:
#         return None, {}
# 
#     emb_dim = len(embeddings[0])
#     emb_matrix = np.array(embeddings, dtype="float32")
#     faiss.normalize_L2(emb_matrix)
#     index = faiss.IndexFlatIP(emb_dim)
#     index.add(emb_matrix)
# 
#     faiss.write_index(index, INDEX_PATH)
#     with open(DOCSTORE_PATH, "wb") as f:
#         pickle.dump(docstore, f)
# 
#     return index, docstore

# RAG DESHABILITADO - Variables y funciones RAG comentadas
# SIMILARITY_THRESHOLD = 0.05
# AI_PLACEHOLDER_RESPONSE = "Esperando respuesta del asistente..."
# 
# def _is_generic_query(text: str) -> bool:
#     normalized = (text or "").strip().lower()
#     if not normalized:
#         return True
#     generic_starts = [
#         "hola", "buenas", "hey", "ayuda", "help", "¿qué puedes", "que puedes",
#         "como estas", "menu", "inicio", "start",
#     ]
#     return any(normalized.startswith(gs) for gs in generic_starts)
# 
# def _topic_suggestions(docstore: Dict[int, str], limit: int = 5) -> List[str]:
#     suggestions: List[str] = []
#     seen: set = set()
#     for _, chunk in docstore.items():
#         if not chunk:
#             continue
#         snippet = chunk.strip().split("\n")[0][:140].strip()
#         if len(snippet) < 20:
#             continue
#         key = snippet[:60].lower()
#         if key in seen:
#             continue
#         seen.add(key)
#         suggestions.append(snippet + ("…" if len(snippet) == 140 else ""))
#         if len(suggestions) >= limit:
#             break
#     if not suggestions:
#         suggestions = [
#             "Políticas y procedimientos de gestión de calidad",
#             "Indicadores y métricas de aseguramiento de la calidad",
#             "Roles y responsabilidades en el sistema de calidad",
#             "Ciclo de mejora continua (Planificar-Hacer-Verificar-Actuar)",
#             "Auditorías y acciones correctivas/preventivas",
#         ]
#     return suggestions

# RAG DESHABILITADO - Inicialización de índice FAISS comentada
# if os.path.exists(INDEX_PATH) and os.path.exists(DOCSTORE_PATH):
#     index = faiss.read_index(INDEX_PATH)
#     with open(DOCSTORE_PATH, "rb") as f:
#         docstore = pickle.load(f)
#     try:
#         if index.ntotal != len(docstore):
#             index, docstore = build_faiss_from_context()
#     except Exception:
#         index, docstore = build_faiss_from_context()
# else:
#     index, docstore = build_faiss_from_context()

# Variables deshabilitadas para RAG
index = None
docstore = {}

# --------------- HEALTH CHECK ------------------
@app.get("/")
async def root():
    """Endpoint raíz para verificar que la API está funcionando"""
    return {
        "message": "Chatbot USS API está funcionando",
        "status": "ok",
        "version": "1.0.0",
        "rag_enabled": False
    }

@app.get("/health")
async def health_check():
    """Health check para servicios de monitoreo"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# --------------- ENDPOINTS AUTH ------------------
@app.post("/register/", status_code=201)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
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
        # Devolver error más descriptivo para depuración local
        raise HTTPException(status_code=500, detail=f"Error al registrar usuario: {str(e)}")


@app.get("/admin/users/")
def admin_list_users(current_user: Annotated[UserModel, Depends(get_current_user)], db: Session = Depends(get_db)):
    # Para simplificar, cualquier usuario autenticado puede listar usuarios; en producción validar rol
    users = db.query(UserModel).order_by(UserModel.email.asc()).all()
    return [{"id": u.id, "email": u.email, "nombre": u.nombre, "activo": bool(u.activo)} for u in users]


class AdminCreateUser(BaseModel):
    email: str
    password: str
    nombre: Optional[str] = None
    activo: Optional[bool] = True


@app.post("/admin/users/", status_code=201)
def admin_create_user(payload: AdminCreateUser, current_user: Annotated[UserModel, Depends(get_current_user)], db: Session = Depends(get_db)):
    # En producción, comprobar que current_user es admin
    hashed = get_password_hash(payload.password)
    user = UserModel(email=payload.email, password_hash=hashed, nombre=payload.nombre, activo=1 if payload.activo else 0)
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email ya registrado")
    return {"id": user.id, "email": user.email, "nombre": user.nombre}


@app.delete('/admin/users/{user_id}/', status_code=204)
def admin_delete_user(user_id: int, current_user: Annotated[UserModel, Depends(get_current_user)], db: Session = Depends(get_db)):
    """Eliminar un usuario por id (endpoint administrativo).
    En producción debería validar roles; aquí permitimos a cualquier autenticado para simplificar pruebas.
    """
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='Usuario no encontrado')
    # Opcional: evitar auto-eliminación del propio admin si lo deseas
    db.delete(user)
    db.commit()
    return


@app.post("/admin/conversations/", status_code=201)
async def admin_create_conversation(
    title: str = Form(""),
    users: str = Form(""),
    files: List[UploadFile] = File(default=[]),
    current_user: Annotated[UserModel, Depends(get_current_user)] = None,
    db: Session = Depends(get_db),
):
    # users: comma-separated emails
    conv = ConversationModel(user_id=current_user.id if current_user else None, title=title.strip() or "Nueva conversación")
    db.add(conv)
    db.commit()
    db.refresh(conv)

    # agregar participantes (buscar emails case-insensitive)
    emails = [e.strip() for e in users.split(",") if e.strip()]
    inserted_emails = []
    inserted_ids = []
    for email in emails:
        # Buscar sin distinguir mayúsculas/minúsculas
        u = db.query(UserModel).filter(func.lower(UserModel.email) == email.lower()).first()
        if u:
            cp = ConversationParticipantModel(conversation_id=conv.id, user_id=u.id)
            db.add(cp)
            inserted_emails.append(u.email)
            inserted_ids.append(u.id)
    db.commit()

    # guardar archivos en backend/uploads/<conv.id>/
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
        try:
            print(f"admin_create_conversation: saved attachment id={att.id} filename={att.filename} path={att.path}")
        except Exception:
            pass
    db.commit()

    # Insertar mensaje de bienvenida para que el docente lo vea al abrir la conversación
    try:
        welcome_text = "¡Hola! Soy tu asistente de IA USS. ¿Cómo puedo ayudarte hoy?"
        welcome_msg = MessageModel(conversation_id=conv.id, sender="ai", text=welcome_text)
        db.add(welcome_msg)
        conv.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(conv)
    except Exception:
        db.rollback()

    # Log para depuración local
    try:
        print(f"admin_create_conversation: created conv_id={conv.id}, owner={conv.user_id}, users_inserted={inserted_ids}")
    except Exception:
        pass

    return {"id": conv.id, "title": conv.title, "created_at": conv.created_at, "users": inserted_emails, "participant_ids": inserted_ids, "files": files_info}


@app.post('/conversations/{conversation_id}/attachments/', status_code=201)
async def add_conversation_attachments(conversation_id: int = Path(..., ge=1), files: List[UploadFile] = File(default=[]), current_user: Annotated[UserModel, Depends(get_current_user)] = None, db: Session = Depends(get_db)):
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
            print(f"add_conversation_attachments: saved attachment id={att.id} filename={att.filename} path={att.path}")
        except Exception:
            pass
    # ensure final commit
    try:
        db.commit()
    except Exception:
        db.rollback()
    return {'files': files_info}


class ReportCreate(BaseModel):
    report_type: str
    comment: Optional[str] = None


@app.post('/reports/', status_code=201)
def create_report(payload: ReportCreate, conversation_id: Optional[int] = None, current_user: Annotated[UserModel, Depends(get_current_user)] = None, db: Session = Depends(get_db)):
    # conversation_id optional; if provided, link the report
    r = ReportModel(conversation_id=conversation_id, user_id=current_user.id if current_user else None, report_type=payload.report_type, comment=payload.comment)
    db.add(r)
    db.commit()
    db.refresh(r)
    return { 'id': r.id, 'conversation_id': r.conversation_id, 'user_id': r.user_id, 'report_type': r.report_type, 'comment': r.comment, 'created_at': r.created_at, 'status': r.status }


@app.get('/admin/reports/')
def admin_list_reports(current_user: Annotated[UserModel, Depends(get_current_user)] = None, db: Session = Depends(get_db)):
    rows = db.query(ReportModel).order_by(ReportModel.created_at.desc()).all()
    out = []
    for row in rows:
        u = None
        if row.user_id:
            u = db.query(UserModel).filter(UserModel.id == row.user_id).first()
        out.append({'id': row.id, 'docente': u.nombre if u else None, 'email': u.email if u else None, 'conversation_id': row.conversation_id, 'tipo': row.report_type, 'comentario': row.comment, 'fechaEnvio': row.created_at, 'estado': row.status})
    return out


@app.get("/admin/conversations/")
def admin_list_conversations(current_user: Annotated[UserModel, Depends(get_current_user)], db: Session = Depends(get_db)):
    # Devuelve conversaciones con participantes y attachments
    convs = db.query(ConversationModel).order_by(ConversationModel.updated_at.desc()).all()
    out = []
    for c in convs:
        parts = db.query(ConversationParticipantModel).filter(ConversationParticipantModel.conversation_id == c.id).all()
        emails = []
        for p in parts:
            u = db.query(UserModel).filter(UserModel.id == p.user_id).first()
            if u:
                emails.append(u.email)
        atts = db.query(AttachmentModel).filter(AttachmentModel.conversation_id == c.id).all()
        files = [{"filename": a.filename, "path": a.path} for a in atts]
        out.append({"id": c.id, "title": c.title, "created_at": c.created_at, "users": emails, "files": files})
    return out


@app.delete('/admin/conversations/{conversation_id}/', status_code=204)
def admin_delete_conversation(conversation_id: int = Path(..., ge=1), current_user: Annotated[UserModel, Depends(get_current_user)] = None, db: Session = Depends(get_db)):
    """Eliminar conversación por id desde el panel administrativo.
    Nota: en este proyecto no hay roles diferenciados, por simplicidad cualquier usuario autenticado
    que acceda al endpoint puede eliminar; en producción deberías validar roles.
    """
    conv = db.query(ConversationModel).filter(ConversationModel.id == conversation_id).first()
    try:
        if not conv:
            # Ya no existe; considerar idempotente -> devolver 204
            print(f"admin_delete_conversation: conversation_id={conversation_id} not found (already deleted?)")
            return
        db.delete(conv)
        db.commit()
        print(f"admin_delete_conversation: deleted conversation_id={conversation_id} by admin={current_user.id if current_user else 'unknown'}")
    except Exception as e:
        db.rollback()
        print(f"admin_delete_conversation: error deleting {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail='Error eliminando conversación')
    return


@app.post("/login/", response_model=Token)
def login_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )
    access_token = create_access_token({"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


# --------------- ENDPOINTS CONVERSATIONS ------------------
@app.get("/conversations/", response_model=List[ConversationOut])
async def list_conversations(current_user: Annotated[UserModel, Depends(get_current_user)], db: Session = Depends(get_db)):
    """List conversations where the current user is owner or a participant."""
    # IDs where user is participant
    part_rows = db.query(ConversationParticipantModel.conversation_id).filter(ConversationParticipantModel.user_id == current_user.id).all()
    part_ids = [r[0] for r in part_rows]

    items = (
        db.query(ConversationModel)
        .filter((ConversationModel.user_id == current_user.id) | (ConversationModel.id.in_(part_ids)))
        .order_by(ConversationModel.updated_at.desc())
        .all()
    )
    return [
        ConversationOut(
            id=i.id, title=i.title, created_at=i.created_at, updated_at=i.updated_at
        )
        for i in items
    ]


@app.get("/conversations/{conversation_id}/messages/", response_model=List[MessageOut])
async def get_conversation_messages(conversation_id: int = Path(..., ge=1), current_user: Annotated[UserModel, Depends(get_current_user)] = None, db: Session = Depends(get_db)):
    # Check that the user is owner or participant
    conv = db.query(ConversationModel).filter(ConversationModel.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    is_owner = conv.user_id == current_user.id
    is_part = db.query(ConversationParticipantModel).filter(ConversationParticipantModel.conversation_id == conversation_id, ConversationParticipantModel.user_id == current_user.id).first() is not None
    if not (is_owner or is_part):
        raise HTTPException(status_code=403, detail="No tiene permiso para ver esta conversación")
    msgs = db.query(MessageModel).filter(MessageModel.conversation_id == conversation_id).order_by(MessageModel.created_at.asc()).all()
    return [MessageOut(id=m.id, sender=m.sender, text=m.text, created_at=m.created_at) for m in msgs]


@app.post("/conversations/", response_model=ConversationOut, status_code=201)
async def create_conversation(payload: ConversationCreate, current_user: Annotated[UserModel, Depends(get_current_user)], db: Session = Depends(get_db)):
    conv = ConversationModel(user_id=current_user.id, title=payload.title or "Nueva conversación")
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

    return ConversationOut(id=conv.id, title=conv.title, created_at=conv.created_at, updated_at=conv.updated_at)


@app.patch("/conversations/{conversation_id}/", response_model=ConversationOut)
async def rename_conversation(
    conversation_id: int = Path(..., ge=1),
    payload: ConversationRename = None,
    current_user: Annotated[UserModel, Depends(get_current_user)] = None,
    db: Session = Depends(get_db),
):
    conv = db.query(ConversationModel).filter(ConversationModel.id == conversation_id, ConversationModel.user_id == current_user.id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    conv.title = payload.title.strip() or conv.title
    conv.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(conv)
    return ConversationOut(id=conv.id, title=conv.title, created_at=conv.created_at, updated_at=conv.updated_at)


@app.delete("/conversations/{conversation_id}/", status_code=204)
async def delete_conversation(
    conversation_id: int = Path(..., ge=1),
    current_user: Annotated[UserModel, Depends(get_current_user)] = None,
    db: Session = Depends(get_db),
):
    conv = db.query(ConversationModel).filter(ConversationModel.id == conversation_id, ConversationModel.user_id == current_user.id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    db.delete(conv)
    db.commit()
    return


# --------------- ENDPOINTS MESSAGES ------------------
@app.get("/conversations/{conversation_id}/messages/", response_model=List[MessageOut])
async def list_messages(
    conversation_id: int = Path(..., ge=1),
    current_user: Annotated[UserModel, Depends(get_current_user)] = None,
    db: Session = Depends(get_db),
):
    conv = db.query(ConversationModel).filter(ConversationModel.id == conversation_id, ConversationModel.user_id == current_user.id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    msgs = (
        db.query(MessageModel)
        .filter(MessageModel.conversation_id == conv.id)
        .order_by(MessageModel.created_at.asc())
        .all()
    )
    return [MessageOut(id=m.id, sender=m.sender, text=m.text, created_at=m.created_at) for m in msgs]


@app.post("/conversations/{conversation_id}/messages/", response_model=ChatResponse)
async def send_message(
    payload: MessageCreate,
    conversation_id: int = Path(..., ge=1),
    current_user: Annotated[UserModel, Depends(get_current_user)] = None,
    db: Session = Depends(get_db),
):
    # RAG DESHABILITADO - Ahora funciona como chatbot normal
    conv = db.query(ConversationModel).filter(ConversationModel.id == conversation_id, ConversationModel.user_id == current_user.id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    user_text = (payload.text or "").strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Texto vacío")

    # Guardar mensaje del usuario
    user_msg = MessageModel(conversation_id=conv.id, sender="user", text=user_text)
    db.add(user_msg)
    db.commit()

    # Obtener historial de conversación para contexto
    recent_messages = (
        db.query(MessageModel)
        .filter(MessageModel.conversation_id == conv.id)
        .order_by(MessageModel.created_at.desc())
        .limit(10)  # Últimos 10 mensajes para contexto
        .all()
    )
    
    # Construir contexto de conversación
    conversation_context = ""
    if len(recent_messages) > 1:  # Si hay mensajes previos
        context_messages = []
        for msg in reversed(recent_messages[1:]):  # Excluir el mensaje actual
            role = "Usuario" if msg.sender == "user" else "Asistente"
            context_messages.append(f"{role}: {msg.text}")
        if context_messages:
            conversation_context = "\n".join(context_messages[-6:])  # Últimos 6 mensajes

    # Prompt para chatbot normal (sin RAG)
    if conversation_context:
        prompt = f"""
Eres un asistente de IA útil y amigable. Responde de manera natural y conversacional.

Contexto de la conversación:
{conversation_context}

Usuario: {user_text}

Asistente:"""
    else:
        prompt = f"""
Eres un asistente de IA útil y amigable. Responde de manera natural y conversacional.

Usuario: {user_text}

Asistente:"""

    try:
        # Generar respuesta con Gemini
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 1000,
            }
        )
        ai_text = getattr(response, "text", "") or "Lo siento, no pude generar una respuesta en este momento."
    except Exception as e:
        print(f"Error generando respuesta: {e}")
        ai_text = "Lo siento, hubo un error al procesar tu mensaje. Por favor, inténtalo de nuevo."

    # Guardar mensaje de la IA
    ai_msg = MessageModel(conversation_id=conv.id, sender="ai", text=ai_text)
    db.add(ai_msg)
    conv.updated_at = datetime.utcnow()
    db.commit()

    # Sin RAG, no hay fuentes
    return ChatResponse(response=ai_text, sources=[])


# --------------- Mantenimiento / Salud IA ------------------
# RAG DESHABILITADO - Endpoint de reconstrucción de índice comentado
# @app.post("/rebuild_index/")
# async def rebuild_index():
#     global index, docstore
#     index, docstore = build_faiss_from_context()
#     if index is None or not docstore:
#         return {"error": "No se pudo reconstruir el índice. Verifica que existan PDFs válidos en context_docs."}
#     return {"message": "Índice reconstruido", "num_chunks": len(docstore)}


@app.get("/ai_health/")
async def ai_health():
    # RAG DESHABILITADO - Health check simplificado para chatbot normal
    details = {
        "rag_enabled": False,
        "chatbot_mode": "normal",
        "can_generate": False,
    }

    try:
        resp = model.generate_content(
            "Di 'pong'. Solo la palabra.",
            generation_config={"max_output_tokens": 3, "temperature": 0},
        )
        out_text = getattr(resp, "text", "") or ""
        details["can_generate"] = bool(out_text)
        if out_text:
            details["sample"] = out_text
    except Exception as e:
        details["generate_error"] = str(e)

    status_label = "ok" if details["can_generate"] else "error"
    return {"status": status_label, **details}


# RAG DESHABILITADO - Endpoint de debug de recuperación comentado
# @app.post("/debug_retrieve/")
# async def debug_retrieve(req: MessageCreate):
#     if index is None or not docstore:
#         return {"error": "No hay índice/docstore"}
# 
#     q_emb = genai.embed_content(
#         model="models/embedding-001",
#         content=req.text,
#         task_type="retrieval_query",
#     )["embedding"]
#     q_vec = np.array([q_emb], dtype="float32")
#     faiss.normalize_L2(q_vec)
# 
#     k = 8
#     D, I = index.search(q_vec, k)
#     pairs = [(float(D[0][pos]), int(I[0][pos])) for pos in range(len(I[0])) if int(I[0][pos]) in docstore]
#     preview = [
#         {
#             "score": score,
#             "idx": idx,
#             "snippet": (docstore[idx][:220] + ("…" if len(docstore[idx]) > 220 else "")) if docstore[idx] else ""
#         }
#         for score, idx in pairs
#     ]
#     return {"pairs": preview}

@app.get("/chatbot_info/")
async def chatbot_info():
    """Endpoint para obtener información sobre el estado del chatbot"""
    return {
        "mode": "normal_ai",
        "rag_enabled": False,
        "description": "Chatbot funcionando como IA conversacional normal sin RAG",
        "model": "gemini-1.5-flash"
    }
