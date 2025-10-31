# Sistema RAG con Pinecone, Gemini 2.0 Flash y Hugging Face

## 🎯 Características Implementadas

### ✅ Backend Completo
- **Servicios RAG**: Pinecone, Gemini 2.0 Flash, Sentence Transformers
- **Modelos de Base de Datos**: CustomChatbot, ChatbotAccess, ChatbotDocument
- **API Endpoints**: CRUD completo para chatbots, documentos y chat con RAG
- **Procesamiento de Documentos**: PDF, DOCX, TXT, Markdown
- **Sistema de Permisos**: Lectura, escritura, administración por chatbot
- **Embeddings Locales**: Cache inteligente con Sentence Transformers

### 🔧 Servicios Implementados

#### 1. PineconeService (`services/pinecone_service.py`)
- Creación/eliminación de índices por chatbot
- Inserción y búsqueda de vectores con metadatos
- Gestión de namespaces por chatbot
- Estadísticas de índices

#### 2. GeminiService (`services/gemini_service.py`)
- Integración con Gemini 2.0 Flash Experimental
- Prompts optimizados para RAG
- Generación de respuestas contextualizadas
- Manejo de historial de conversación
- Configuración de seguridad y parámetros

#### 3. EmbeddingService (`services/embedding_service.py`)
- Sentence Transformers (all-MiniLM-L6-v2)
- Cache en memoria y disco
- Procesamiento por lotes
- Similitud coseno

#### 4. DocumentProcessor (`services/document_processor.py`)
- Extracción de texto multi-formato
- Chunking inteligente preservando párrafos
- Metadatos enriquecidos
- Validación de archivos

### 🚀 API Endpoints

#### Gestión de Chatbots (`/api/chatbots/`)
```
POST   /api/chatbots/                    # Crear chatbot personalizado
GET    /api/chatbots/                    # Listar chatbots del usuario
GET    /api/chatbots/{id}                # Obtener chatbot específico
PUT    /api/chatbots/{id}                # Actualizar chatbot
DELETE /api/chatbots/{id}                # Eliminar chatbot
GET    /api/chatbots/{id}/stats          # Estadísticas del chatbot

POST   /api/chatbots/{id}/users          # Asignar usuarios al chatbot
GET    /api/chatbots/{id}/users          # Listar usuarios con acceso
DELETE /api/chatbots/{id}/users/{user_id} # Remover acceso de usuario
```

#### Gestión de Documentos (`/api/chatbots/{id}/documents/`)
```
POST   /upload                           # Subir documentos
GET    /                                 # Listar documentos
DELETE /{document_id}                    # Eliminar documento
POST   /process                          # Procesar documentos pendientes
GET    /{document_id}/status             # Estado de procesamiento
```

#### Chat con RAG (`/api/chat/`)
```
POST   /message                          # Enviar mensaje con RAG
POST   /conversations                    # Crear conversación
GET    /conversations                    # Listar conversaciones
POST   /conversations/{id}/messages      # Enviar mensaje a conversación
GET    /conversations/{id}/messages      # Obtener mensajes
GET    /available-chatbots               # Chatbots disponibles
```

### 🗄️ Modelos de Base de Datos

#### CustomChatbot
- Información básica del chatbot
- Índice de Pinecone asociado
- Estado activo/inactivo
- Relaciones con documentos y accesos

#### ChatbotAccess
- Control de permisos por usuario
- Niveles: READ, WRITE, ADMIN
- Auditoría de quien otorgó acceso

#### ChatbotDocument
- Metadatos de archivos subidos
- Estado de procesamiento
- Conteo de chunks generados
- Información del usuario que subió

### 🔄 Flujo de Trabajo

#### Creación de Chatbot
1. Admin crea chatbot → Se crea índice en Pinecone
2. Sube documentos → Procesamiento automático en background
3. Genera embeddings → Almacena en Pinecone con metadatos
4. Asigna usuarios → Control de permisos granular

#### Uso del Chat
1. Usuario selecciona chatbot → Verifica permisos
2. Envía pregunta → Genera embedding de consulta
3. Busca en Pinecone → Obtiene contexto relevante
4. Genera respuesta con Gemini → Incluye fuentes
5. Guarda conversación → Mantiene historial

## 📦 Instalación y Configuración

### 1. Instalar Dependencias
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno
Copiar `.env.example` a `.env` y completar:
```env
# Base de datos
DATABASE_URL=postgresql://usuario:password@localhost:5432/chatbot_db

# Gemini 2.0 Flash
GEMINI_API_KEY=tu_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash-exp

# Pinecone
PINECONE_API_KEY=tu_pinecone_api_key
PINECONE_ENVIRONMENT=us-east1-gcp

# Configuración RAG
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RESULTS=5
MAX_FILE_SIZE_MB=50

# JWT
SECRET_KEY=tu_clave_secreta_jwt
ACCESS_TOKEN_EXPIRE_MINUTES=120
```

### 3. Crear Base de Datos
```bash
# Crear las tablas
python -c "from database import Base, engine; Base.metadata.create_all(bind=engine)"
```

### 4. Ejecutar Servidor
```bash
uvicorn main:app --reload
```

## 🎯 Próximos Pasos para Frontend

La implementación del backend está completa. Para el frontend necesitarás:

### 1. Panel de Administración
- **Gestión de Chatbots**: Crear, editar, eliminar chatbots
- **Gestión de Usuarios**: Asignar permisos por chatbot
- **Gestión de Documentos**: Subir, procesar, eliminar documentos
- **Dashboard**: Estadísticas y métricas de uso

### 2. Interface de Chat Mejorada
- **Selector de Chatbot**: Dropdown con chatbots disponibles
- **Indicadores de Fuente**: Mostrar de qué documentos proviene la respuesta
- **Estado de Procesamiento**: Indicar cuando se están procesando documentos
- **Historial por Chatbot**: Conversaciones organizadas por chatbot

### 3. Componentes Sugeridos
```
src/components/admin/
├── ChatbotManager.tsx          # CRUD de chatbots
├── DocumentUploader.tsx        # Subir y gestionar documentos
├── UserPermissions.tsx         # Asignar usuarios a chatbots
├── ChatbotStats.tsx           # Estadísticas y métricas
└── ProcessingStatus.tsx        # Estado de documentos

src/components/chat/
├── ChatbotSelector.tsx         # Selector de chatbot activo
├── MessageWithSources.tsx      # Mensaje con fuentes citadas
├── ConversationList.tsx        # Lista filtrada por chatbot
└── ContextIndicator.tsx        # Indicador de contexto RAG
```

## 🚦 Testing de la API

### 1. Health Check
```bash
curl http://localhost:8000/
curl http://localhost:8000/chatbot_info/
```

### 2. Crear Chatbot (después de login)
```bash
curl -X POST "http://localhost:8000/api/chatbots/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Asistente de Calidad",
    "description": "Chatbot especializado en gestión de calidad"
  }'
```

### 3. Subir Documento
```bash
curl -X POST "http://localhost:8000/api/chatbots/1/documents/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "files=@documento.pdf"
```

### 4. Chat con RAG
```bash
curl -X POST "http://localhost:8000/api/chat/message" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "¿Qué es el ciclo PDCA?",
    "chatbot_id": 1
  }'
```

## 🔧 Configuración Avanzada

### Optimización de Pinecone
- **Dimensiones**: 384 (optimizado para all-MiniLM-L6-v2)
- **Métrica**: Similitud coseno
- **Namespaces**: Separación por chatbot
- **Batch Size**: 100 vectores por inserción

### Configuración de Gemini
- **Modelo**: gemini-2.0-flash-exp (más rápido y eficiente)
- **Temperatura**: 0.7 (balance creatividad/precisión)
- **Max Tokens**: 2048 (respuestas detalladas)
- **Safety Settings**: Configurado para uso académico

### Chunking Inteligente
- **Tamaño**: 1000 caracteres con overlap de 200
- **Preservación**: Mantiene párrafos completos cuando es posible
- **Metadatos**: Fuente, página, tipo de archivo, timestamps

¡El sistema RAG está listo para uso! 🎉