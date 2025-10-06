# Sistema RAG - Chatbot USS

## 🎯 Descripción del Sistema

Este proyecto implementa un sistema RAG (Retrieval-Augmented Generation) optimizado que combina:

- **Embeddings gratuitos** con Hugging Face (`all-MiniLM-L6-v2`)
- **Almacenamiento vectorial** en Pinecone
- **Generación de respuestas** con Gemini (solo para chat)
- **Caché inteligente** para evitar regenerar embeddings

## 🏗️ Arquitectura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Documentos    │────│  Hugging Face    │────│   Pinecone      │
│   PDF           │    │  Embeddings      │    │   Vector DB     │
│   (una vez)     │    │  (gratis)        │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Usuario       │────│     Gemini       │◄───│   Búsqueda      │
│   Consulta      │    │   (solo chat)    │    │   Contexto      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 Configuración Inicial

### 1. Instalar Dependencias

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno

Copia el archivo de ejemplo y configura las APIs:

```bash
cp .env.example .env
```

Edita `.env` con tus claves:

```env
# APIs necesarias
GEMINI_API_KEY=tu_api_key_de_gemini
PINECONE_API_KEY=tu_api_key_de_pinecone

# Base de datos
DATABASE_URL=postgresql://usuario:password@host:puerto/db

# Seguridad
SECRET_KEY=clave_secreta_jwt
```

### 3. Obtener API Keys

#### Gemini API (Google AI Studio)
1. Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Crea una nueva API key
3. Copia la clave a `GEMINI_API_KEY`

#### Pinecone API
1. Regístrate en [Pinecone](https://www.pinecone.io/)
2. Crea un nuevo proyecto
3. Ve a "API Keys" y copia tu clave
4. Agrega la clave a `PINECONE_API_KEY`

### 4. Agregar Documentos

Coloca tus archivos PDF en `backend/context_docs/`:

```
backend/
├── context_docs/
│   ├── calidad1.pdf
│   ├── calidad2.pdf
│   └── tu_documento.pdf
```

### 5. Inicializar el Sistema RAG

Ejecuta el script de configuración:

```bash
python setup_rag.py
```

Este script:
- ✅ Verifica las variables de entorno
- ✅ Procesa los documentos PDF
- ✅ Genera embeddings con Hugging Face
- ✅ Sube los vectores a Pinecone
- ✅ Configura el caché local

## 🔧 Uso del Sistema

### Iniciar el Servidor

```bash
uvicorn main:app --reload
```

### Endpoints Disponibles

| Endpoint | Método | Descripción |
|----------|---------|-------------|
| `/` | GET | Estado general del sistema |
| `/conversations/{id}/messages/` | POST | Enviar mensaje (usa RAG) |
| `/rag_status/` | GET | Estado del sistema RAG |
| `/rebuild_index/` | POST | Reconstruir índice completo |
| `/chatbot_info/` | GET | Información del chatbot |

### Ejemplo de Uso

```python
import requests

# Enviar mensaje al chatbot
response = requests.post(
    "http://localhost:8000/conversations/1/messages/",
    json={"text": "¿Cuáles son las políticas de calidad?"},
    headers={"Authorization": "Bearer tu_token"}
)

data = response.json()
print(f"Respuesta: {data['response']}")
print(f"Fuentes: {data['sources']}")
```

## 💡 Características Clave

### 🔄 Caché Inteligente

El sistema evita regenerar embeddings:

- **Primera ejecución**: Genera embeddings y los almacena
- **Siguientes ejecuciones**: Usa embeddings en caché
- **Detección de cambios**: Solo regenera si los PDFs cambian

### 🎯 Búsqueda Semántica

- Usa `all-MiniLM-L6-v2` (384 dimensiones)
- Búsqueda por similitud coseno
- Filtro por score mínimo (0.7 por defecto)
- Retorna top-k documentos relevantes

### 💬 Generación Contextual

- Combina contexto de documentos + historial de chat
- Usa Gemini solo para generar respuestas finales
- Mantiene coherencia conversacional
- Incluye fuentes en las respuestas

## 🛠️ Administración

### Reconstruir Índice

Si agregas nuevos documentos:

```bash
curl -X POST "http://localhost:8000/rebuild_index/"
```

O ejecuta nuevamente:

```bash
python setup_rag.py
```

### Verificar Estado

```bash
curl "http://localhost:8000/rag_status/"
```

Respuesta esperada:
```json
{
  "rag_initialized": true,
  "embedding_model": "all-MiniLM-L6-v2",
  "pinecone_vectors": 150,
  "pinecone_index": "uss-chatbot-rag",
  "gemini_model": "gemini-1.5-flash"
}
```

## 📁 Estructura de Archivos

```
backend/
├── main.py                 # API principal con RAG integrado
├── rag_manager.py          # Gestor principal del sistema RAG
├── embedding_service.py    # Servicio de embeddings (Hugging Face)
├── pinecone_service.py     # Servicio de Pinecone
├── setup_rag.py           # Script de inicialización
├── requirements.txt        # Dependencias actualizadas
├── context_docs/          # Documentos PDF
├── embeddings_cache/      # Caché de embeddings
│   ├── embeddings.pkl
│   ├── documents.pkl
│   └── metadata.pkl
└── .env                   # Variables de entorno
```

## 🔧 Configuración Avanzada

### Personalizar Modelo de Embeddings

En `embedding_service.py`:

```python
# Cambiar modelo (debe ser compatible con sentence-transformers)
embedding_service = EmbeddingService(model_name="paraphrase-multilingual-MiniLM-L12-v2")
```

### Ajustar Parámetros de Búsqueda

En `rag_manager.py`:

```python
# Modificar parámetros de búsqueda
similar_docs = self.search_context(
    query,
    top_k=8,        # Más documentos
    min_score=0.6   # Score más permisivo
)
```

### Configurar Pinecone

En `pinecone_service.py`:

```python
# Cambiar configuración del índice
self.index_name = "mi-chatbot-personalizado"
self.dimension = 384  # Debe coincidir con el modelo de embeddings
self.region = "us-west-2"  # Región más cercana
```

## 🐛 Solución de Problemas

### Error: "PINECONE_API_KEY no encontrada"
- Verifica que el archivo `.env` existe
- Confirma que `PINECONE_API_KEY` está configurada
- Reinicia el servidor después de cambiar `.env`

### Error: "No se pudieron generar embeddings"
- Verifica que los PDFs están en `context_docs/`
- Asegúrate de que los PDFs contienen texto (no solo imágenes)
- Revisa los logs para errores específicos

### Error: "Sistema RAG no inicializado"
- Ejecuta `python setup_rag.py`
- Verifica que Pinecone esté funcionando
- Revisa el endpoint `/rag_status/` para más detalles

### Rendimiento Lento
- Reduce `top_k` en búsquedas
- Aumenta `min_score` para filtrar mejor
- Usa chunks más pequeños en documentos largos

## 📊 Monitoreo

### Logs del Sistema

Los logs incluyen:
- Inicialización del sistema RAG
- Procesamiento de documentos
- Generación de embeddings
- Búsquedas en Pinecone
- Respuestas generadas

### Métricas Importantes

- **Vectores en Pinecone**: Número de chunks indexados
- **Score de similitud**: Relevancia de los resultados
- **Tiempo de respuesta**: Latencia de búsqueda + generación
- **Fuentes utilizadas**: Documentos que contribuyen a las respuestas

## 🔄 Mantenimiento

### Actualizaciones Regulares

1. **Documentos**: Agrega nuevos PDFs y ejecuta `rebuild_index/`
2. **Modelos**: Actualiza versiones de Hugging Face si es necesario
3. **Índices**: Limpia Pinecone si cambias la estructura de datos

### Respaldos

- **Embeddings**: Se almacenan en `embeddings_cache/`
- **Pinecone**: Los vectores están en la nube
- **Documentos**: Mantén respaldo de `context_docs/`

## 🚀 Producción

### Variables de Entorno

```env
ENVIRONMENT=production
DATABASE_URL=postgresql://prod_user:secure_pass@prod_host:5432/prod_db
```

### Optimizaciones

- Usa Pinecone en región más cercana a tu servidor
- Implementa rate limiting en endpoints
- Configura logging estructurado
- Monitorea uso de APIs (Gemini tiene cuotas)

---

¡Tu sistema RAG está listo! 🎉

El chatbot ahora responderá basándose únicamente en tus documentos, usando embeddings eficientes y optimizando el uso de tokens de Gemini.