from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import Annotated, List, Tuple, Dict
from pydantic import BaseModel
import os
import glob
import pickle

import numpy as np

from database import Base, engine, get_db
from models import User as UserModel

# Gemini
from google.generativeai import configure, GenerativeModel
import google.generativeai as genai

# FAISS
import faiss

app = FastAPI()

origins = [
    "http://localhost:5173",  # frontend (Vite/React)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

Base.metadata.create_all(bind=engine)

# --------------- USERS ------------------
class UserCreate(BaseModel):
    email: str
    password: str

@app.post("/register/")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = pwd_context.hash(user.password)
    new_user = UserModel(email=user.email, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Usuario registrado exitosamente"}

@app.post("/login/")
def login_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )
    return {"access_token": user.email, "token_type": "bearer"}


# --------------- IA CONFIG ------------------
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

CONTEXT_DIR = os.path.join(os.path.dirname(__file__), "context_docs")
INDEX_PATH = os.path.join(os.path.dirname(__file__), "vector_store.index")
DOCSTORE_PATH = os.path.join(os.path.dirname(__file__), "docstore.pkl")

def _chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    chunks: List[str] = []
    start = 0
    text_length = len(text)
    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunks.append(text[start:end])
        if end == text_length:
            break
        start = end - overlap
        if start < 0:
            start = 0
    return chunks

def _load_context_texts() -> List[str]:
    from pypdf import PdfReader
    # OCR fallback imports se cargarán dinámicamente cuando se necesiten

    texts: List[str] = []
    if not os.path.isdir(CONTEXT_DIR):
        return texts

    pdf_paths = sorted(glob.glob(os.path.join(CONTEXT_DIR, "*.pdf")))
    for pdf_path in pdf_paths:
        try:
            reader = PdfReader(pdf_path)
            pages_text: List[str] = [page.extract_text() or "" for page in reader.pages]
            full_text = "\n".join(pages_text)

            if not full_text.strip():
                # Fallback OCR: renderizar páginas e intentar extraer texto con Tesseract
                try:
                    import pypdfium2 as pdfium  # renderizador de PDF
                    from PIL import Image
                    import pytesseract

                    pdf = pdfium.PdfDocument(pdf_path)
                    ocr_text_parts: List[str] = []
                    # Escala para mejor OCR
                    render_scale = 2.0
                    for i in range(len(pdf)):
                        page = pdf[i]
                        bitmap = page.render(scale=render_scale).to_pil()
                        # Convertir a escala de grises mejora OCR en muchos casos
                        if bitmap.mode != "L":
                            bitmap = bitmap.convert("L")
                        page_text = pytesseract.image_to_string(bitmap, lang="spa+eng")
                        if page_text:
                            ocr_text_parts.append(page_text)
                    full_text = "\n".join(ocr_text_parts)
                except Exception:
                    # Si el OCR falla, seguir al siguiente PDF
                    full_text = ""

            # Evitar textos vacíos
            if full_text.strip():
                for chunk in _chunk_text(full_text):
                    texts.append(chunk)
        except Exception:
            # Si un PDF falla, lo omitimos para no bloquear el inicio
            continue
    return texts

def build_faiss_from_context() -> Tuple[faiss.IndexFlatIP, Dict[int, str]]:
    documents = _load_context_texts()
    if not documents:
        return None, {}

    embeddings: List[List[float]] = []
    docstore: Dict[int, str] = {}

    for idx, doc_text in enumerate(documents):
        try:
            emb = genai.embed_content(
                model="models/embedding-001",
                content=doc_text,
                task_type="retrieval_document",
            )["embedding"]
        except Exception:
            # Si una incrustación falla, omitir ese documento
            continue
        embeddings.append(emb)
        docstore[idx] = doc_text

    if not embeddings:
        return None, {}

    emb_dim = len(embeddings[0])
    # Normalizamos y usamos IP para similiaridad coseno
    emb_matrix = np.array(embeddings, dtype="float32")
    faiss.normalize_L2(emb_matrix)
    index = faiss.IndexFlatIP(emb_dim)
    index.add(emb_matrix)

    # Persistimos para futuras ejecuciones
    faiss.write_index(index, INDEX_PATH)
    with open(DOCSTORE_PATH, "wb") as f:
        pickle.dump(docstore, f)

    return index, docstore

SIMILARITY_THRESHOLD = 0.05  # IP con vectores normalizados ≈ similitud coseno

def _is_generic_query(text: str) -> bool:
    normalized = (text or "").strip().lower()
    if not normalized:
        return True
    generic_starts = [
        "hola", "buenas", "hey", "ayuda", "help", "¿qué puedes", "que puedes",
        "como estas", "menu", "inicio", "start",
    ]
    return any(normalized.startswith(gs) for gs in generic_starts)

def _topic_suggestions(docstore: Dict[int, str], limit: int = 5) -> List[str]:
    suggestions: List[str] = []
    seen: set = set()
    for _, chunk in docstore.items():
        if not chunk:
            continue
        snippet = chunk.strip().split("\n")[0][:140].strip()
        if len(snippet) < 20:
            continue
        key = snippet[:60].lower()
        if key in seen:
            continue
        seen.add(key)
        suggestions.append(snippet + ("…" if len(snippet) == 140 else ""))
        if len(suggestions) >= limit:
            break
    if not suggestions:
        suggestions = [
            "Políticas y procedimientos de gestión de calidad",
            "Indicadores y métricas de aseguramiento de la calidad",
            "Roles y responsabilidades en el sistema de calidad",
            "Ciclo de mejora continua (Planificar-Hacer-Verificar-Actuar)",
            "Auditorías y acciones correctivas/preventivas",
        ]
    return suggestions

# Cargamos o construimos el índice FAISS a partir de los documentos en context_docs
if os.path.exists(INDEX_PATH) and os.path.exists(DOCSTORE_PATH):
    index = faiss.read_index(INDEX_PATH)
    with open(DOCSTORE_PATH, "rb") as f:
        docstore = pickle.load(f)  # dict con {id: texto}
    # Validar consistencia: número de vectores vs tamaño del docstore
    try:
        if index.ntotal != len(docstore):
            index, docstore = build_faiss_from_context()
    except Exception:
        index, docstore = build_faiss_from_context()
else:
    index, docstore = build_faiss_from_context()

class ChatRequest(BaseModel):
    message: str

@app.post("/chat/")
async def chat(req: ChatRequest):
    if index is None or not docstore:
        return {"error": "No hay documentos precargados para contexto."}

    query = req.message

    # Si la consulta es genérica o vacía, proponemos tópicos del corpus
    if _is_generic_query(query):
        topics = _topic_suggestions(docstore)
        system_msg = (
            "Responde únicamente basándote en los documentos cargados. "
            "Si algo no está en el contexto, di explícitamente que no lo sabes."
        )
        return {"response": "Aquí tienes algunos temas disponibles:\n- " + "\n- ".join(topics), "sources": [], "system": system_msg}

    # Convertimos la consulta en embedding (y normalizamos para IP ≈ coseno)
    q_emb = genai.embed_content(
        model="models/embedding-001",
        content=query,
        task_type="retrieval_query",
    )["embedding"]
    q_vec = np.array([q_emb], dtype="float32")
    faiss.normalize_L2(q_vec)

    # Buscamos en FAISS
    k = 8
    D, I = index.search(q_vec, k)

    # Filtramos por umbral de similitud
    context_pairs_all = [(float(D[0][pos]), int(I[0][pos])) for pos in range(len(I[0])) if int(I[0][pos]) in docstore]
    context_pairs = [(score, idx) for score, idx in context_pairs_all if score >= SIMILARITY_THRESHOLD]
    # Si nada supera el umbral, tomar los 2 mejores resultados como fallback
    if not context_pairs and context_pairs_all:
        context_pairs = sorted(context_pairs_all, key=lambda x: x[0], reverse=True)[:2]
    context_pairs = context_pairs[:3]

    context_docs = [docstore[idx] for _, idx in context_pairs]

    if not context_docs:
        topics = _topic_suggestions(docstore)
        return {"response": "⚠️ No se encontró una respuesta en el contexto. Prueba con alguno de estos temas:\n- " + "\n- ".join(topics), "sources": []}

    context_text = "\n\n".join(context_docs)
    prompt = f"""
    ERES UN ASISTENTE ESTRICTO A CONTEXTO.
    - Responde SOLO en base al CONTEXTO proporcionado.
    - Si la respuesta no está en el CONTEXTO, responde: "No lo sé con la información disponible".
    - Cita solo fragmentos pertinentes del CONTEXTO si ayuda a la claridad.

    CONTEXTO:
    {context_text}

    PREGUNTA:
    {query}
    """

    response = model.generate_content(prompt)

    return {
        "response": response.text,
        "sources": context_docs,
    }

@app.post("/rebuild_index/")
async def rebuild_index():
    global index, docstore
    index, docstore = build_faiss_from_context()
    if index is None or not docstore:
        return {"error": "No se pudo reconstruir el índice. Verifica que existan PDFs válidos en context_docs."}
    return {"message": "Índice reconstruido", "num_chunks": len(docstore)}

@app.get("/ai_health/")
async def ai_health():
    details = {
        "has_index": index is not None,
        "doc_chunks": len(docstore) if docstore else 0,
        "can_embed": False,
        "can_generate": False,
    }

    # Probar embeddings
    try:
        emb = genai.embed_content(
            model="models/embedding-001",
            content="ping",
            task_type="retrieval_query",
        )["embedding"]
        details["can_embed"] = bool(emb and len(emb) > 0)
    except Exception as e:
        details["embed_error"] = str(e)

    # Probar generación con salida mínima
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

    status_label = "ok" if (details["has_index"] and details["doc_chunks"] > 0 and details["can_embed"] and details["can_generate"]) else ("degraded" if (details["can_embed"] or details["can_generate"]) else "error")
    return {"status": status_label, **details}

@app.post("/debug_retrieve/")
async def debug_retrieve(req: ChatRequest):
    if index is None or not docstore:
        return {"error": "No hay índice/docstore"}

    q_emb = genai.embed_content(
        model="models/embedding-001",
        content=req.message,
        task_type="retrieval_query",
    )["embedding"]
    q_vec = np.array([q_emb], dtype="float32")
    faiss.normalize_L2(q_vec)

    k = 8
    D, I = index.search(q_vec, k)
    pairs = [(float(D[0][pos]), int(I[0][pos])) for pos in range(len(I[0])) if int(I[0][pos]) in docstore]
    preview = [
        {
            "score": score,
            "idx": idx,
            "snippet": (docstore[idx][:220] + ("…" if len(docstore[idx]) > 220 else "")) if docstore[idx] else ""
        }
        for score, idx in pairs
    ]
    return {"pairs": preview}
