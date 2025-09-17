# RAG DESHABILITADO - Configuración del Chatbot

## Estado Actual
El sistema RAG (Retrieval-Augmented Generation) ha sido **DESHABILITADO** temporalmente. El chatbot ahora funciona como una IA conversacional normal usando únicamente Gemini.

## Cambios Realizados

### 1. Configuración de API Key
- **API Key de Gemini configurada**: `AIzaSyDO1JayjGYlDCMi08zvFKa-VGRAQIzMEXA`
- Configuración hardcodeada en `main.py` línea 142

### 2. Funcionalidad RAG Comentada
Las siguientes funciones y variables han sido comentadas pero **NO eliminadas**:
- `_chunk_text()` - Función de chunking de documentos
- `_load_context_texts()` - Carga de documentos PDF
- `build_faiss_from_context()` - Construcción del índice FAISS
- `_is_generic_query()` - Detección de consultas genéricas
- `_topic_suggestions()` - Sugerencias de temas
- Variables: `CONTEXT_DIR`, `INDEX_PATH`, `DOCSTORE_PATH`, `SIMILARITY_THRESHOLD`

### 3. Endpoints Modificados
- **`/conversations/{id}/messages/`**: Ahora funciona como chatbot normal sin RAG
- **`/ai_health/`**: Health check simplificado
- **`/rebuild_index/`**: Comentado (no disponible)
- **`/debug_retrieve/`**: Comentado (no disponible)
- **`/chatbot_info/`**: Nuevo endpoint para información del chatbot

### 4. Dependencias
Las siguientes dependencias han sido comentadas en `requirements.txt`:
- faiss-cpu
- numpy
- langchain
- langchain-community
- langchain-openai
- pypdf
- pypdfium2
- pytesseract
- Pillow

## Funcionamiento Actual

### Chatbot Normal
- Usa **Gemini 1.5 Flash** directamente
- Mantiene contexto de conversación (últimos 6 mensajes)
- Respuestas naturales y conversacionales
- **No usa documentos** como fuente de conocimiento
- **No retorna fuentes** (sources siempre vacío)

### Configuración de Generación
```python
generation_config={
    "temperature": 0.7,
    "max_output_tokens": 1000,
}
```

## Cómo Reactivar RAG

Para reactivar el RAG en el futuro:

1. **Descomentar las importaciones** en `main.py`:
   ```python
   import glob
   import pickle
   import numpy as np
   import faiss
   ```

2. **Descomentar las dependencias** en `requirements.txt` e instalar:
   ```bash
   pip install faiss-cpu numpy langchain langchain-community langchain-openai pypdf pypdfium2 pytesseract Pillow
   ```

3. **Descomentar todas las funciones RAG** en `main.py`

4. **Restaurar el endpoint original** de `/conversations/{id}/messages/`

5. **Descomentar los endpoints** `/rebuild_index/` y `/debug_retrieve/`

## Endpoints Disponibles

### Funcionando
- `POST /register/` - Registro de usuarios
- `POST /login/` - Login de usuarios
- `GET /conversations/` - Listar conversaciones
- `POST /conversations/` - Crear conversación
- `PATCH /conversations/{id}/` - Renombrar conversación
- `DELETE /conversations/{id}/` - Eliminar conversación
- `GET /conversations/{id}/messages/` - Obtener mensajes
- `POST /conversations/{id}/messages/` - **Enviar mensaje (SIN RAG)**
- `GET /ai_health/` - Estado del sistema (simplificado)
- `GET /chatbot_info/` - Información del chatbot

### Deshabilitados
- `POST /rebuild_index/` - Reconstruir índice RAG
- `POST /debug_retrieve/` - Debug de recuperación RAG

## Notas Importantes
- El sistema mantiene toda la funcionalidad de usuarios y conversaciones
- La base de datos PostgreSQL sigue funcionando normalmente
- El frontend no requiere cambios
- Todos los archivos RAG están preservados para reactivación futura
