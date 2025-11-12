# 🤖 Chatbot RAG con IA - Sistema Completo# 🤖 Sistema de Chatbot RAG - Universidad San Sebastián# Chatbot para Docentes - Universidad San Sebastián



Sistema completo de chatbots con Retrieval-Augmented Generation (RAG) que permite crear asistentes de IA personalizados basados en documentos propios.



## 🌟 Características PrincipalesSistema inteligente de chatbots personalizados con Retrieval-Augmented Generation (RAG) desarrollado para **Taller de Ingeniería de Software**.  Este repositorio contiene el código del proyecto desarrollado en **Taller de Ingeniería de Software**.  



### 🎯 Sistema de Chatbots PersonalizadosPermite crear chatbots especializados que responden preguntas basadas en documentos específicos.El objetivo es construir un chatbot especializado en responder preguntas de docentes basadas en documentos cargados.

- ✅ Crea chatbots especializados con tus propios documentos

- ✅ Sube múltiples archivos (PDF, DOCX, Markdown)

- ✅ Procesamiento automático y vectorización

- ✅ Búsqueda semántica inteligente con Pinecone## ⚡ Estado Actual: **95% Completo - Listo para Producción**## 🚀 Stack



### 💬 Chat Inteligente- **Frontend:** React + Vite

- ✅ Conversaciones contextuales con historial

- ✅ Respuestas basadas únicamente en tus documentos### ✅ **Funcionando Correctamente**- **Backend:** FastAPI (Python)

- ✅ Citación automática de fuentes

- ✅ Detección de preguntas fuera de contexto- **RAG System**: Búsqueda semántica completa con Pinecone + Google Gemini- **Base de Datos:** PostgreSQL

- ✅ Interfaz moderna estilo WhatsApp

- **Autenticación**: Sistema JWT con PostgreSQL funcionando- **IA:** HuggingFace + GPT4All + FAISS/ChromaDB

### 👥 Gestión de Usuarios

- ✅ Sistema completo de autenticación (JWT)- **Frontend**: Interface completa React/TypeScript operativa  - **Orquestación:** Docker Compose

- ✅ Panel de administración

- ✅ Gestión de usuarios y permisos- **Upload**: Procesamiento de PDF, DOCX, TXT, MD implementado

- ✅ Reportes de conversaciones

- **Multi-usuario**: Gestión de permisos y acceso a chatbots## 📂 Estructura

### 🎨 UI/UX Moderna

- ✅ Diseño responsivo (móvil, tablet, desktop)- `frontend/` → Aplicación en React

- ✅ Tema oscuro/claro

- ✅ Burbujas de chat diferenciadas### 🎯 **Requiere Solo**- `backend/` → API con FastAPI

- ✅ Animaciones suaves

- ✅ Scroll automático inteligente- ✅ **CONFIGURADO**: Groq API Key ya configurada y funcionando- `ia/` → Módulos de IA (embeddings, RAG, GPT4All)



## 🛠️ Stack Tecnológico- `db/` → Scripts SQL y configuración inicial



### Backend## 🚀 Stack Tecnológico- `docker-compose.yml` → Orquestación de servicios

- **FastAPI**: Framework web moderno y rápido

- **PostgreSQL**: Base de datos relacional

- **SQLAlchemy**: ORM para Python

- **Groq AI**: LLM ultrarrápido (Llama 3.1 8B)- **Frontend:** React + TypeScript + Vite## ▶️ Cómo ejecutar

- **Pinecone**: Vector database para RAG

- **Sentence Transformers**: Embeddings semánticos- **Backend:** FastAPI (Python 3.11+)1. Clonar repositorio



### Frontend- **Base de Datos:** PostgreSQL   ```bash

- **React + TypeScript**: UI moderna y type-safe

- **Vite**: Build tool ultrarrápido- **IA:** Groq (Llama3) + Pinecone Vector DB   git clone https://github.com/tu-org/proyecto-chatbot.git

- **CSS Modules**: Estilos componetizados

- **React Hooks**: Estado y efectos- **Embeddings:** HuggingFace Transformers   cd proyecto-chatbot



### DevOps- **Auth:** JWT + bcrypt

- **Render**: Backend + PostgreSQL (Free Tier)

- **Vercel**: Frontend (Free Tier)2. Levantar servicios con Docker

- **GitHub Actions**: CI/CD automático (opcional)

## 📂 Estructura del Proyecto   ```bash

## 📋 Requisitos Previos

   docker-compose up --build

- Python 3.11+

- Node.js 18+```

- Cuenta en [Groq](https://console.groq.com) (API Key gratuita)

- Cuenta en [Pinecone](https://www.pinecone.io) (Free Tier)ProyectoIngSoftware/3.  Frontend: http://localhost:3000



## 🚀 Quick Start (Desarrollo Local)├── backend/                    # FastAPI Backend



### 1. Clonar el Repositorio│   ├── services/              # Servicios de IA    Backend (Swagger): http://localhost:8000/docs



```bash│   │   ├── gemini_service.py  # Google Gemini ✅

git clone https://github.com/BartClo/ProyectoIngSoftware.git

cd ProyectoIngSoftware│   │   ├── pinecone_service.py# Vector Database ✅##👥 Equipo

```

│   │   └── embedding_service.py# Embeddings ✅

### 2. Backend Setup

│   ├── routes/               # API Endpoints- Luciano Alegria

```bash

cd backend│   │   ├── chat_rag.py       # Chat con RAG ✅



# Crear entorno virtual│   │   ├── chatbots.py       # Gestión chatbots ✅- Renata Antequiera

python -m venv venv

source venv/bin/activate  # En Windows: venv\Scripts\activate│   │   └── documents.py      # Upload docs ✅



# Instalar dependencias│   ├── models.py             # SQLAlchemy Models ✅- Marcelo Muñoz

pip install -r requirements.txt

│   └── main.py               # FastAPI App ✅

# Configurar variables de entorno

cp .env.example .env├── frontend/                 # React Frontend ✅

# Edita .env con tus API keys│   └── src/components/       # Componentes completos

└── README_ESTADO_ACTUAL.md   # Estado detallado

# Iniciar servidor```

uvicorn main:app --reload

```## ⚙️ Configuración e Instalación



Backend corriendo en: `http://localhost:8000`### 1. **Backend Setup**

API Docs: `http://localhost:8000/docs````bash

cd backend

### 3. Frontend Setuppip install -r requirements.txt



```bash# Configurar .env

cd frontendcp .env.example .env

# ✅ Groq ya configurado

# Instalar dependencias

npm installuvicorn main:app --reload

```

# Configurar variables de entorno

echo "VITE_API_URL=http://localhost:8000" > .env### 2. **Frontend Setup**

```bash

# Iniciar servidor de desarrollocd frontend  

npm run devnpm install

```npm run dev

```

Frontend corriendo en: `http://localhost:5173`

### 3. **Variables Críticas (.env)**

### 4. Configurar Pinecone```env

# ⚠️ REQUERIDO para funcionar

1. Ve a [Pinecone Console](https://app.pinecone.io)GROQ_API_KEY=gsk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

2. Crea un nuevo índice:   GROQ_MODEL=llama-3.1-8b-instant

   - **Name**: `chatbot-rag-index`

   - **Dimensions**: `384`# Base de datos

   - **Metric**: `cosine`DATABASE_URL=postgresql://user:pass@localhost:5432/db

3. Copia tu API Key al `.env`

# Pinecone Vector DB

### 5. Primera EjecuciónPINECONE_API_KEY=tu_pinecone_key

PINECONE_INDEX_NAME=tu_index

1. Registra un usuario en `http://localhost:5173````

2. Crea tu primer chatbot

3. Sube un documento (PDF/DOCX)## 🎯 Flujo de Uso

4. ¡Inicia una conversación!

1. **Admin crea chatbot** → Sube documentos específicos

## 📦 Deployment a Producción2. **Sistema procesa docs** → Genera embeddings y los guarda en Pinecone  

3. **Admin otorga permisos** → Usuarios específicos pueden acceder

**Lee la [Guía de Deployment](./DEPLOYMENT.md)** para instrucciones completas.4. **Usuario conversa** → IA responde basada en documentos + RAG



### TL;DR## 🏗️ Arquitectura RAG



1. **Backend + DB**: Deploy en Render.com usando `render.yaml````

2. **Frontend**: Deploy en VercelUsuario pregunta → Frontend → FastAPI → Pinecone (busca docs) → Gemini (responde) → Usuario

3. **Configura variables de entorno** en ambos servicios```

4. **Actualiza CORS** en backend con tu URL de Vercel

## 📋 Accesos

## 📁 Estructura del Proyecto

- **Frontend**: http://localhost:5173

```- **Backend API**: http://localhost:8000/docs

ProyectoIngSoftware/- **Admin Panel**: Gestión de chatbots y usuarios

├── backend/                    # API FastAPI

│   ├── main.py                # Entry point## 👥 Equipo de Desarrollo

│   ├── database.py            # SQLAlchemy setup

│   ├── models.py              # Database models- **Luciano Alegria** - Desarrollo Frontend

│   ├── auth.py                # JWT authentication- **Renata Antequiera** - Integración Backend  

│   ├── routes/                # API endpoints- **Marcelo Muñoz** - Arquitectura RAG e IA

│   │   ├── chatbots.py       # Chatbot CRUD

│   │   ├── chat_rag.py       # RAG chat logic---

│   │   └── documents.py      # File upload/processing

│   ├── services/              # Business logic**🎉 Sistema Listo**: Solo configurar API Key de Gemini y ¡funciona completamente!
│   │   ├── groq_service.py   # LLM integration
│   │   ├── pinecone_service.py # Vector DB
│   │   ├── embedding_service.py # Text embeddings
│   │   └── document_processor.py # PDF/DOCX parsing
│   └── requirements.txt       # Python dependencies
│
├── frontend/                   # React + TypeScript
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── chat/         # Chat interface
│   │   │   ├── admin/        # Admin panel
│   │   │   ├── auth/         # Login/Register
│   │   │   └── dashboard/    # Main dashboard
│   │   ├── lib/
│   │   │   └── api.ts        # API client
│   │   └── main.tsx          # Entry point
│   ├── package.json           # npm dependencies
│   └── vite.config.ts         # Vite config
│
├── render.yaml                # Render deployment config
├── vercel.json                # Vercel deployment config
├── DEPLOYMENT.md              # Deployment guide
└── README.md                  # This file
```

## 🔧 Configuración de Entorno

### Backend (.env)

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/chatbot_rag

# AI Services
GROQ_API_KEY=gsk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
PINECONE_API_KEY=pcsk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=chatbot-rag-index

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
FRONTEND_URL=http://localhost:5173
```

### Frontend (.env)

```bash
VITE_API_URL=http://localhost:8000
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm run test
```

## 📊 API Documentation

Una vez que el backend esté corriendo, visita:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Endpoints Principales

- `POST /auth/register` - Registrar usuario
- `POST /auth/login` - Iniciar sesión
- `GET /chatbots` - Listar chatbots
- `POST /chatbots` - Crear chatbot
- `POST /chatbots/{id}/documents` - Subir documento
- `POST /conversations` - Crear conversación
- `POST /conversations/{id}/messages` - Enviar mensaje

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/amazing-feature`)
3. Commit tus cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 👥 Autores

- **Equipo USS** - Proyecto de Ingeniería de Software

## 🙏 Agradecimientos

- [Groq](https://groq.com) - LLM ultrarrápido
- [Pinecone](https://www.pinecone.io) - Vector database
- [FastAPI](https://fastapi.tiangolo.com) - Framework web
- [React](https://react.dev) - UI library
- [Render](https://render.com) - Hosting backend
- [Vercel](https://vercel.com) - Hosting frontend

## 📞 Soporte

¿Problemas? Abre un [Issue](https://github.com/BartClo/ProyectoIngSoftware/issues)

---

⭐ **Star** este proyecto si te fue útil!
