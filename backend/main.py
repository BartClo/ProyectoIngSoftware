from fastapi import FastAPI, Depends, HTTPException, status, Path
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import Annotated, List, Tuple, Dict, Optional
from pydantic import BaseModel
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

from database import Base, engine, get_db
from models import User as UserModel
from models import Conversation as ConversationModel
from models import Message as MessageModel

# JWT
from jose import JWTError, jwt

# RAG System
from rag_manager import RAGManager
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Inicializar sistema RAG
rag_manager = RAGManager()

# Inicializar RAG en startup (esto solo se ejecuta una vez al iniciar el servidor)
@app.on_event("startup")
async def startup_event():
    """Inicializa el sistema RAG al iniciar la aplicación"""
    logger.info("Inicializando sistema RAG...")
    success = rag_manager.initialize_rag_system()
    if success:
        logger.info("Sistema RAG inicializado exitosamente")
    else:
        logger.error("Error al inicializar sistema RAG")

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
# El sistema RAG ahora maneja la configuración de IA
# Gemini se configura dentro de RAGManager

# --------------- HEALTH CHECK ------------------
@app.get("/")
async def root():
    """Endpoint raíz para verificar que la API está funcionando"""
    status = rag_manager.get_system_status()
    return {
        "message": "Chatbot USS API está funcionando",
        "status": "ok",
        "version": "1.0.0",
        "rag_enabled": status.get("rag_initialized", False),
        "vector_count": status.get("pinecone_vectors", 0)
    }

@app.get("/health")
async def health_check():
    """Health check para servicios de monitoreo"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# --------------- ENDPOINTS AUTH ------------------
@app.post("/register/", status_code=201)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email ya registrado")
    hashed_password = get_password_hash(user.password)
    new_user = UserModel(email=user.email, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Usuario registrado exitosamente"}


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
    """Envía un mensaje y obtiene respuesta usando el sistema RAG"""
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

    # Obtener historial de conversación para contexto
    recent_messages = (
        db.query(MessageModel)
        .filter(MessageModel.conversation_id == conv.id)
        .order_by(MessageModel.created_at.desc())
        .limit(10)  # Últimos 10 mensajes para contexto
        .all()
    )
    
    # Preparar historial para RAG
    conversation_history = []
    if len(recent_messages) > 1:  # Si hay mensajes previos
        for msg in reversed(recent_messages[1:]):  # Excluir el mensaje actual
            conversation_history.append({
                "sender": msg.sender,
                "text": msg.text,
                "created_at": msg.created_at
            })

    try:
        # Generar respuesta usando RAG
        ai_text, sources = rag_manager.generate_response(
            query=user_text,
            conversation_history=conversation_history
        )
        
        if not ai_text:
            ai_text = "Lo siento, no pude generar una respuesta en este momento."
            
    except Exception as e:
        logger.error(f"Error generando respuesta RAG: {e}")
        ai_text = "Lo siento, hubo un error al procesar tu mensaje. Por favor, inténtalo de nuevo."
        sources = []

    # Guardar mensaje de la IA
    ai_msg = MessageModel(conversation_id=conv.id, sender="ai", text=ai_text)
    db.add(ai_msg)
    conv.updated_at = datetime.utcnow()
    db.commit()

    return ChatResponse(response=ai_text, sources=sources)


# --------------- Mantenimiento / Salud IA ------------------
@app.post("/rebuild_index/")
async def rebuild_index():
    """Reconstruye completamente el índice RAG"""
    try:
        success = rag_manager.rebuild_index()
        if success:
            status = rag_manager.get_system_status()
            return {
                "message": "Índice RAG reconstruido exitosamente",
                "vector_count": status.get("pinecone_vectors", 0)
            }
        else:
            return {"error": "No se pudo reconstruir el índice RAG"}
    except Exception as e:
        logger.error(f"Error al reconstruir índice: {e}")
        return {"error": f"Error al reconstruir índice: {str(e)}"}


@app.get("/rag_status/")
async def rag_status():
    """Obtiene el estado completo del sistema RAG"""
    return rag_manager.get_system_status()


@app.post("/initialize_rag/")
async def initialize_rag_endpoint():
    """Inicializa manualmente el sistema RAG"""
    try:
        success = rag_manager.initialize_rag_system(force_refresh=False)
        if success:
            return {"message": "Sistema RAG inicializado exitosamente"}
        else:
            return {"error": "No se pudo inicializar el sistema RAG"}
    except Exception as e:
        logger.error(f"Error al inicializar RAG: {e}")
        return {"error": f"Error al inicializar RAG: {str(e)}"}


@app.get("/ai_health/")
async def ai_health():
    """Health check del sistema RAG"""
    return rag_manager.get_system_status()


@app.get("/chatbot_info/")
async def chatbot_info():
    """Endpoint para obtener información sobre el estado del chatbot"""
    status = rag_manager.get_system_status()
    return {
        "mode": "rag_enabled",
        "rag_enabled": status.get("rag_initialized", False),
        "description": "Chatbot con sistema RAG usando Hugging Face + Pinecone + Gemini",
        "embedding_model": status.get("embedding_model", "all-MiniLM-L6-v2"),
        "llm_model": status.get("gemini_model", "gemini-1.5-flash"),
        "vector_store": "Pinecone",
        "vectors_count": status.get("pinecone_vectors", 0)
    }
