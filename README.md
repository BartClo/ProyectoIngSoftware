# Chatbot RAG para Docentes - Universidad San Sebastián

Este repositorio contiene el código del proyecto desarrollado en **Taller de Ingeniería de Software**.  
El objetivo es construir un chatbot especializado con sistema RAG (Retrieval-Augmented Generation) que responde preguntas de docentes basándose exclusivamente en documentos institucionales cargados.

## 🎯 Características del Sistema RAG

- **🧠 IA Local**: Usa Ollama con LLaMA 3.2 (100% gratuito, sin API keys, privacidad total)
- **📝 Embeddings eficientes**: Usa Hugging Face (gratuito) para generar embeddings una sola vez
- **💾 Caché inteligente**: Evita regenerar embeddings, solo procesa cuando hay cambios
- **☁️ Vector Database**: Almacena embeddings en Pinecone para búsquedas rápidas
- **🔒 Privacidad**: El LLM se ejecuta completamente en tu máquina local
- **📚 Fuentes transparentes**: Muestra las fuentes de información en cada respuesta
- **⚡ Sin límites**: No hay restricciones de cuota ni costos por uso

## 🚀 Stack Tecnológico

- **Frontend:** React + TypeScript + Vite
- **Backend:** FastAPI (Python)
- **Base de Datos:** PostgreSQL
- **Sistema RAG:** 
  - **LLM Local:** Ollama con LLaMA 3.2 1B (gratuito, privado)
  - **Embeddings:** Hugging Face Sentence Transformers (all-MiniLM-L6-v2)
  - **Vector DB:** Pinecone
- **Deployment:** Docker Compose

## 📂 Estructura del Proyecto

```
├── frontend/                 # Aplicación React con TypeScript
├── backend/                  # API FastAPI con sistema RAG
│   ├── context_docs/        # Documentos PDF para el RAG
│   ├── embeddings_cache/    # Caché local de embeddings
│   ├── rag_manager.py       # Gestor principal del RAG
│   ├── embedding_service.py # Servicio de embeddings con HF
│   ├── pinecone_service.py  # Servicio de Pinecone
│   ├── setup_rag.py         # Script de configuración inicial
│   └── test_rag.py          # Pruebas del sistema RAG
├── db/                      # Scripts SQL y configuración
└── docker-compose.yml       # Orquestación de servicios
```

## ⚡ Inicio Rápido

### 1. Clonar el Repositorio
```bash
git clone https://github.com/BartClo/ProyectoIngSoftware.git
cd ProyectoIngSoftware
```

### 2. Instalar Ollama (LLM Local)

#### Windows:
```bash
winget install ollama
```

#### macOS/Linux:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

#### Descargar modelo LLaMA 3.2:
```bash
ollama pull llama3.2:1b
```

### 3. Configurar Backend RAG

#### Instalar dependencias:
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

#### Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tu configuración
```

Variables necesarias en `.env`:
```env
# IA Local con Ollama (NO requiere API keys pagadas)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b

# Vector Database (requiere cuenta gratuita)
PINECONE_API_KEY=tu_api_key_de_pinecone

# Base de datos local
DATABASE_URL=postgresql://postgres:tu_password@localhost:5432/tu_database

# JWT
SECRET_KEY=tu_clave_secreta_jwt
```

#### Obtener API Key de Pinecone (GRATIS):

**Pinecone:**
1. Regístrate en [Pinecone](https://www.pinecone.io/) (plan gratuito disponible)
2. Crea un proyecto y obtén tu API key
3. Agrega a `PINECONE_API_KEY`

> **💡 Nota:** Pinecone ofrece un plan gratuito generoso. Solo Ollama es completamente local.

#### Agregar documentos:
```bash
# Coloca tus PDFs en backend/context_docs/
cp tu_documento.pdf backend/context_docs/
```

#### Inicializar sistema RAG:
```bash
cd backend
python setup_rag.py
```

### 4. Ejecutar el Sistema

#### Opción A: Con Docker (Recomendado)
```bash
# Iniciar Ollama primero
ollama serve  # En una terminal separada

# Luego el resto del sistema
docker-compose up --build
```

#### Opción B: Desarrollo Local
```bash
# Terminal 1 - Ollama
ollama serve

# Terminal 2 - Backend
cd backend
venv\Scripts\activate  # Windows
uvicorn main:app --reload

# Terminal 3 - Frontend
cd frontend
npm install
npm run dev
```

### 5. Acceder a la Aplicación

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **Documentación API:** http://localhost:8000/docs
- **Ollama:** http://localhost:11434 (servidor local)

## 🔧 Uso del Sistema

### Primera Configuración

1. **Instalar Ollama y modelo**: `ollama pull llama3.2:1b`
2. **Agregar documentos PDF** en `backend/context_docs/`
3. **Ejecutar setup**: `python backend/setup_rag.py`
4. **Verificar funcionamiento**: `python backend/test_rag.py`

### Funcionamiento del RAG

1. **Usuario hace pregunta** → El frontend envía al backend
2. **Sistema busca contexto** → Genera embedding de la pregunta y busca en Pinecone
3. **Encuentra documentos relevantes** → Filtra por score de similitud
4. **Ollama genera respuesta localmente** → Usa solo el contexto encontrado + historial de chat
5. **Respuesta incluye fuentes** → Muestra qué documentos se usaron
6. **100% privado** → Todo el procesamiento del LLM es local

### Administración

- **Ver estado del sistema**: `GET /rag_status/`
- **Reconstruir índice**: `POST /rebuild_index/`
- **Información del chatbot**: `GET /chatbot_info/`
- **Estado de Ollama**: `ollama list` para ver modelos instalados

## 🎯 Características Técnicas

### IA Local con Ollama
- **LLaMA 3.2 1B**: Modelo optimizado para respuestas rápidas y precisas
- **Ejecución local**: Sin envío de datos a servidores externos
- **Sin límites**: Usa cuanto necesites sin restricciones de API
- **Privacidad garantizada**: Todos los datos permanecen en tu máquina

### Sistema de Caché Inteligente
- Detecta cambios en documentos PDF
- Solo regenera embeddings cuando es necesario
- Almacena metadatos para verificación de integridad

### Búsqueda Semántica Optimizada
- Modelo: `all-MiniLM-L6-v2` (384 dimensiones, gratuito)
- Similitud coseno con filtro por score mínimo
- Top-k documentos más relevantes

### Generación Contextual Local
- Combina contexto de documentos + historial conversacional
- Respuestas basadas exclusivamente en la base de conocimientos
- Transparencia total con fuentes citadas
- **100% offline para generación de texto**

## 🧪 Pruebas y Validación

```bash
# Ejecutar pruebas completas
cd backend
python test_rag.py

# Verificar estado del sistema
curl "http://localhost:8000/rag_status/"

# Ejemplo de consulta
curl -X POST "http://localhost:8000/conversations/1/messages/" \
  -H "Authorization: Bearer tu_token" \
  -H "Content-Type: application/json" \
  -d '{"text": "¿Cuáles son las políticas de calidad?"}'
```

## 📖 Documentación Adicional

- **[Guía Completa de Configuración RAG](backend/RAG_SETUP_GUIDE.md)** - Documentación detallada del sistema
- **[API Documentation](http://localhost:8000/docs)** - Swagger/OpenAPI docs
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Guía de despliegue en producción

## � Desarrollo

### Estructura del Código RAG

- **`rag_manager.py`**: Orquestador principal del sistema RAG
- **`embedding_service.py`**: Gestión de embeddings con Hugging Face
- **`pinecone_service.py`**: Interfaz con Pinecone Vector Database
- **`main.py`**: API FastAPI con endpoints RAG integrados

### Personalización

```python
# Cambiar modelo de embeddings
embedding_service = EmbeddingService(model_name="tu-modelo-preferido")

# Ajustar parámetros de búsqueda
similar_docs = search_context(query, top_k=10, min_score=0.6)

# Configurar Pinecone
pinecone_service = PineconeService(index_name="mi-indice-personalizado")
```

## 🚨 Solución de Problemas

### Error: "Sistema RAG no inicializado"
```bash
cd backend
python setup_rag.py
```

### Error: "No se pudo conectar a Ollama"
```bash
# Verificar que Ollama esté ejecutándose
ollama serve

# En otra terminal, verificar modelos
ollama list

# Si no tienes el modelo, descargarlo
ollama pull llama3.2:1b
```

### Error: "API keys no encontradas"
- Verifica que el archivo `.env` existe y tiene las variables correctas
- Solo necesitas `PINECONE_API_KEY` (Ollama es local)
- Reinicia el servidor después de cambiar `.env`

### Documentos no procesan correctamente
- Asegúrate de que los PDFs contienen texto (no solo imágenes)
- Verifica que están en `backend/context_docs/`

### Ollama funciona lento
- La primera respuesta puede ser lenta (carga del modelo)
- Considera usar `llama3.2:3b` si tienes más RAM
- El modelo se mantiene en memoria después del primer uso

## 👥 Equipo

- **Luciano Alegria** - Desarrollo Frontend
- **Renata Antequiera** - Desarrollo Backend  
- **Marcelo Muñoz** - Integración RAG y DevOps

## 📄 Licencia

Este proyecto fue desarrollado como parte del Taller de Ingeniería de Software en la Universidad San Sebastián.

---

🎉 **¡Tu chatbot RAG está listo para responder preguntas basándose en tus documentos institucionales!**

