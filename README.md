# Chatbot para Docentes - Universidad San Sebastián

Este repositorio contiene el código del proyecto desarrollado en **Taller de Ingeniería de Software**.  
El objetivo es construir un chatbot especializado en responder preguntas de docentes basadas en documentos cargados.

## 🚀 Stack
- **Frontend:** React + Vite
- **Backend:** FastAPI (Python)
- **Base de Datos:** PostgreSQL
- **IA:** HuggingFace + GPT4All + FAISS/ChromaDB
- **Orquestación:** Docker Compose

## 📂 Estructura
- `frontend/` → Aplicación en React
- `backend/` → API con FastAPI
- `ia/` → Módulos de IA (embeddings, RAG, GPT4All)
- `db/` → Scripts SQL y configuración inicial
- `docker-compose.yml` → Orquestación de servicios

## ▶️ Cómo ejecutar
1. Clonar repositorio
   ```bash
   git clone https://github.com/tu-org/proyecto-chatbot.git
   cd proyecto-chatbot

2. Levantar servicios con Docker
   ```bash
   docker-compose up --build

3.  Frontend: http://localhost:3000

    Backend (Swagger): http://localhost:8000/docs

##👥 Equipo

- Luciano Alegria

- Renata Antequiera

- Marcelo Muñoz

