# 🤖 Sistema de Chatbot RAG - Universidad San Sebastián# Chatbot para Docentes - Universidad San Sebastián



Sistema inteligente de chatbots personalizados con Retrieval-Augmented Generation (RAG) desarrollado para **Taller de Ingeniería de Software**.  Este repositorio contiene el código del proyecto desarrollado en **Taller de Ingeniería de Software**.  

Permite crear chatbots especializados que responden preguntas basadas en documentos específicos.El objetivo es construir un chatbot especializado en responder preguntas de docentes basadas en documentos cargados.



## ⚡ Estado Actual: **95% Completo - Listo para Producción**## 🚀 Stack

- **Frontend:** React + Vite

### ✅ **Funcionando Correctamente**- **Backend:** FastAPI (Python)

- **RAG System**: Búsqueda semántica completa con Pinecone + Google Gemini- **Base de Datos:** PostgreSQL

- **Autenticación**: Sistema JWT con PostgreSQL funcionando- **IA:** HuggingFace + GPT4All + FAISS/ChromaDB

- **Frontend**: Interface completa React/TypeScript operativa  - **Orquestación:** Docker Compose

- **Upload**: Procesamiento de PDF, DOCX, TXT, MD implementado

- **Multi-usuario**: Gestión de permisos y acceso a chatbots## 📂 Estructura

- `frontend/` → Aplicación en React

### 🎯 **Requiere Solo**- `backend/` → API con FastAPI

- ✅ **CONFIGURADO**: Groq API Key ya configurada y funcionando- `ia/` → Módulos de IA (embeddings, RAG, GPT4All)

- `db/` → Scripts SQL y configuración inicial

## 🚀 Stack Tecnológico- `docker-compose.yml` → Orquestación de servicios



- **Frontend:** React + TypeScript + Vite## ▶️ Cómo ejecutar

- **Backend:** FastAPI (Python 3.11+)1. Clonar repositorio

- **Base de Datos:** PostgreSQL   ```bash

- **IA:** Groq (Llama3) + Pinecone Vector DB   git clone https://github.com/tu-org/proyecto-chatbot.git

- **Embeddings:** HuggingFace Transformers   cd proyecto-chatbot

- **Auth:** JWT + bcrypt

2. Levantar servicios con Docker

## 📂 Estructura del Proyecto   ```bash

   docker-compose up --build

```

ProyectoIngSoftware/3.  Frontend: http://localhost:3000

├── backend/                    # FastAPI Backend

│   ├── services/              # Servicios de IA    Backend (Swagger): http://localhost:8000/docs

│   │   ├── gemini_service.py  # Google Gemini ✅

│   │   ├── pinecone_service.py# Vector Database ✅##👥 Equipo

│   │   └── embedding_service.py# Embeddings ✅

│   ├── routes/               # API Endpoints- Luciano Alegria

│   │   ├── chat_rag.py       # Chat con RAG ✅

│   │   ├── chatbots.py       # Gestión chatbots ✅- Renata Antequiera

│   │   └── documents.py      # Upload docs ✅

│   ├── models.py             # SQLAlchemy Models ✅- Marcelo Muñoz

│   └── main.py               # FastAPI App ✅

├── frontend/                 # React Frontend ✅
│   └── src/components/       # Componentes completos
└── README_ESTADO_ACTUAL.md   # Estado detallado
```

## ⚙️ Configuración e Instalación

### 1. **Backend Setup**
```bash
cd backend
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
# ✅ Groq ya configurado

uvicorn main:app --reload
```

### 2. **Frontend Setup**
```bash
cd frontend  
npm install
npm run dev
```

### 3. **Variables Críticas (.env)**
```env
# ⚠️ REQUERIDO para funcionar
GROQ_API_KEY=gsk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
   GROQ_MODEL=llama-3.1-8b-instant

# Base de datos
DATABASE_URL=postgresql://user:pass@localhost:5432/db

# Pinecone Vector DB
PINECONE_API_KEY=tu_pinecone_key
PINECONE_INDEX_NAME=tu_index
```

## 🎯 Flujo de Uso

1. **Admin crea chatbot** → Sube documentos específicos
2. **Sistema procesa docs** → Genera embeddings y los guarda en Pinecone  
3. **Admin otorga permisos** → Usuarios específicos pueden acceder
4. **Usuario conversa** → IA responde basada en documentos + RAG

## 🏗️ Arquitectura RAG

```
Usuario pregunta → Frontend → FastAPI → Pinecone (busca docs) → Gemini (responde) → Usuario
```

## 📋 Accesos

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/docs
- **Admin Panel**: Gestión de chatbots y usuarios

## 👥 Equipo de Desarrollo

- **Luciano Alegria** - Desarrollo Frontend
- **Renata Antequiera** - Integración Backend  
- **Marcelo Muñoz** - Arquitectura RAG e IA

---

**🎉 Sistema Listo**: Solo configurar API Key de Gemini y ¡funciona completamente!